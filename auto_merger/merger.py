#!/usr/bin/env python3

# MIT License
#
# Copyright (c) 2024 Red Hat, Inc.

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


import json
import subprocess
import os
import shutil

from typing import List
from pathlib import Path

from auto_merger import utils
from auto_merger.constants import UPSTREAM_REPOS
from auto_merger.utils import setup_logger
from auto_merger.email import EmailSender


class AutoMerger:
    repo_data: List = []
    container_name: str = ""
    container_dir: Path
    current_dir = os.getcwd()

    def __init__(self, github_labels, blocking_labels, approvals=2):
        self.logger = setup_logger("AutoMerger")
        self.github_labels = list(github_labels)
        self.blocking_labels = list(blocking_labels)
        self.approvals = approvals
        self.logger.debug(f"GitHub Labels: {self.github_labels}")
        self.logger.debug(f"GitHub Blocking Labels: {self.blocking_labels}")
        self.logger.debug(f"Approvals Labels: {self.approvals}")
        self.blocked_pr = {}
        self.pr_to_merge = {}
        self.blocked_body = []
        self.approval_body = []

    def is_correct_repo(self) -> bool:
        cmd = ["gh repo view --json name"]
        repo_name = AutoMerger.get_gh_json_output(cmd=cmd)
        self.logger.debug(repo_name)
        if repo_name["name"] == self.container_name:
            return True
        return False

    @staticmethod
    def get_gh_json_output(cmd):
        gh_repo_list = utils.run_command(cmd=cmd, return_output=True)
        return json.loads(gh_repo_list)

    def get_gh_pr_list(self):
        cmd = ["gh pr list -s open --json number,title,labels,reviews,isDraft"]
        repo_data = AutoMerger.get_gh_json_output(cmd=cmd)
        for pr in repo_data:
            if self.is_draft(pr):
                continue
            if self.is_changes_requested(pr):
                continue
            self.repo_data.append(pr)

    def is_authenticated(self):
        token = os.getenv("GH_TOKEN")
        if token == "":
            self.logger.error(f"Environment variable GH_TOKEN is not specified.")
            return False
        cmd = [f"gh status"]
        self.logger.debug(f"Authentication command: {cmd}")
        try:
            return_output = utils.run_command(cmd=cmd, return_output=True)
        except subprocess.CalledProcessError as cpe:
            self.logger.error(f"Authentication to GitHub failed. {cpe}")
            return False
        return True

    def add_blocked_pr(self, pr: {}):
        present = False
        for stored_pr in self.blocked_pr[self.container_name]:
            if int(stored_pr["number"]) == int(pr["number"]):
                present = True
        if present:
            return
        self.blocked_pr[self.container_name].append({
            "number": pr["number"],
            "pr_dict": {
                "title": pr["title"],
                "labels": pr["labels"]
            }
        })
        self.logger.debug(f"PR {pr['number']} added to blocked")

    def add_approved_pr(self, pr: {}):
        self.pr_to_merge[self.container_name].append({
            "number": pr["number"],
            "pr_dict": {
                "title": pr["title"],
                "labels": pr["labels"]
            }
        })
        self.logger.debug(f"PR {pr['number']} added to approved")

    def check_blocked_labels(self):
        for pr in self.repo_data:
            self.logger.debug(f"Check blocked: {pr}")
            if "labels" not in pr:
                continue
            for label in pr["labels"]:
                if label["name"] not in self.blocking_labels:
                    continue
                self.logger.debug(f"Add '{pr['number']}' to blocked PRs.")
                self.add_blocked_pr(pr)

    def check_labels_to_merge(self, pr):
        if "labels" not in pr:
            return True
        for label in pr["labels"]:
            if label["name"] in self.blocking_labels:
                return False
        self.logger.debug(f"Add '{pr['number']}' to approved PRs.")
        return True

    def check_pr_approvals(self, reviews_to_check) -> int:
        self.logger.debug(f"Approvals to check: {reviews_to_check}")
        if not reviews_to_check:
            return False
        approval_cnt = 0
        for review in reviews_to_check:
            if review["state"] == "APPROVED":
                approval_cnt += 1
        if approval_cnt < 2:
            self.logger.debug(f"Approval count: {approval_cnt}")
        return approval_cnt

    def is_changes_requested(self, pr):
        if "labels" not in pr:
            return False
        for labels in pr["labels"]:
            if "pr/changes-requested" == labels["name"]:
                return True
        return False

    def is_draft(self, pr):
        if pr['isDraft']:
            return True
        return False

    def check_pr_to_merge(self) -> bool:
        if len(self.repo_data) == 0:
            return False
        for pr in self.repo_data:
            if self.is_draft(pr):
                continue
            self.logger.debug(f"PR status: {pr}")
            if not self.check_labels_to_merge(pr):
                continue
            approval_count = self.check_pr_approvals(pr["reviews"])
            self.pr_to_merge[self.container_name] = {
                "number": pr["number"],
                "approvals": approval_count,
                "pr_dict": {
                    "title": pr["title"]
                }
            }

    def clone_repo(self):
        temp_dir = utils.temporary_dir()
        utils.run_command(
            f"gh repo clone https://github.com/sclorg/{self.container_name} {temp_dir}/{self.container_name}"
        )
        self.container_dir = Path(temp_dir) / f"{self.container_name}"
        if self.container_dir.exists():
            os.chdir(self.container_dir)

    def merge_pull_requests(self):
        for pr in self.pr_to_merge:
            self.logger.debug(f"PR to merge {pr} in repo {self.container_name}.")

    def clean_dirs(self):
        os.chdir(self.current_dir)
        if self.container_dir.exists():
            shutil.rmtree(self.container_dir)

    def check_all_containers(self) -> int:
        if not self.is_authenticated():
            return 1
        for container in UPSTREAM_REPOS:
            self.container_name = container
            self.repo_data = []
            self.clone_repo()
            if not self.is_correct_repo():
                self.logger.error(f"This is not correct repo {self.container_name}.")
                self.clean_dirs()
                continue
            if self.container_name not in self.blocked_pr:
                self.blocked_pr[self.container_name] = []
            if self.container_name not in self.pr_to_merge:
                self.pr_to_merge[self.container_name] = []
            try:
                self.get_gh_pr_list()
                self.check_blocked_labels()
                if len(self.blocked_pr[self.container_name]) != 0:
                    self.logger.info(
                        f"This pull request can not be merged {self.pr_to_merge}"
                    )
                self.check_pr_to_merge()
            except subprocess.CalledProcessError:
                self.clean_dirs()
                self.logger.error(f"Something went wrong {self.container_name}.")
                continue
            self.clean_dirs()
        return 0

    def get_blocked_labels(self, pr_dict) -> List [str]:
        labels = []
        for lbl in pr_dict["labels"]:
            labels.append(lbl["name"])
        return labels

    def print_blocked_pull_request(self):
        # Do not print anything in case we do not have PR.
        if not [x for x in self.blocked_pr if self.blocked_pr[x]]:
            return 0
        self.blocked_body.append(
            f"Pull requests that are blocked by labels <b>[{', '.join(self.blocking_labels)}]</b><br><br>"
        )

        for container, pull_requests in self.blocked_pr.items():
            if not pull_requests:
                continue
            self.blocked_body.append(f"<b>{container}<b>:")
            self.blocked_body.append("<table><tr><th>Pull request URL</th><th>Title</th><th>Missing labels</th></tr>")
            for pr in pull_requests:
                blocked_labels = self.get_blocked_labels(pr["pr_dict"])
                self.blocked_body.append(
                    f"<tr><td>https://github.com/sclorg/{container}/pull/{pr['number']}</td>"
                    f"<td>{pr['pr_dict']['title']}</td><td><p style='color:red;'>{' '.join(blocked_labels)}</p></td></tr>"
                )
            self.blocked_body.append("</table><br><br>")
        print('\n'.join(self.blocked_body))

    def print_approval_pull_request(self):
        # Do not print anything in case we do not have PR.
        if not [x for x in self.pr_to_merge if self.pr_to_merge[x]]:
            return 0
        self.approval_body.append(f"Pull requests that can be merged or missing {self.approvals} approvals")
        self.approval_body.append("<table><tr><th>Pull request URL</th><th>Title</th><th>Approval status</th></tr>")
        for container, pr in self.pr_to_merge.items():
            if not pr:
                continue
            if int(pr["approvals"]) >= self.approvals:
                result_pr = f"CAN BE MERGED"
            else:
                result_pr = f"Missing {self.approvals-int(pr['approvals'])} APPROVAL"
            self.approval_body.append(
                f"<tr><td>https://github.com/sclorg/{container}/pull/{pr['number']}</td>"
                f"<td>{pr['pr_dict']['title']}</td><td><p style='color:red;'>{result_pr}</p></td></tr>"
            )
        self.approval_body.append("</table><br>")
        print('\n'.join(self.approval_body))

    def send_results(self, recipients):
        self.logger.debug(f"Recepients are: {recipients}")
        if not recipients:
            return 1
        sender_class = EmailSender(recipient_email=list(recipients))
        subject_msg = "Pull request statuses for organization https://gibhub.com/sclorg"
        sender_class.send_email(subject_msg, self.blocked_body + self.approval_body)


def run():
    auto_merger = AutoMerger()
    auto_merger.check_all_containers()
