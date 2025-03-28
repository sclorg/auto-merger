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

from typing import Any
from pathlib import Path

from auto_merger import utils
from auto_merger.custom_logger import setup_logger
from auto_merger.email import EmailSender
from auto_merger.config import Config
from auto_merger.pull_request_handler import PullRequestHandler


class PRStatusChecker:
    container_name: str = ""
    container_dir: Path
    current_dir = os.getcwd()

    def __init__(self, config: Config):
        self.config = config
        self.approval_labels = self.config.github["approval_labels"]
        self.blocking_labels = self.config.github["blocker_labels"]
        self.approvals = self.config.github["approvals"]
        self.namespace = self.config.github["namespace"]
        self.blocked_pr: dict = {}
        self.pr_to_merge: dict = {}
        self.blocked_body: list = []
        self.approval_body: list = []
        self.repo_data: list = []
        self.temp_dir: Path
        self.logger = setup_logger("auto_merger.pr_checker", level=self.config.debug)

    def is_correct_repo(self) -> bool:
        cmd = ["gh repo view --json name"]
        repo_name = PRStatusChecker.get_gh_json_output(cmd=cmd)
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
        repo_data_output = PRStatusChecker.get_gh_json_output(cmd=cmd)
        for pr in repo_data_output:
            if PullRequestHandler.is_draft(pull_request=pr):
                continue
            if PullRequestHandler.is_changes_requested(pull_request=pr):
                continue
            self.repo_data.append(pr)

    def is_authenticated(self) -> bool:
        """
        Function check if user is authenticated
        :return: True if user is authenticated
                 False user is not authenticated
        """
        token = os.getenv("GH_TOKEN")
        if token is None:
            self.logger.critical("Environment variable GH_TOKEN is not specified.")
            return False
        cmd = ["gh status"]
        self.logger.debug(f"Authentication command: {cmd}")
        try:
            utils.run_command(cmd=cmd, return_output=True)
        except subprocess.CalledProcessError as cpe:
            self.logger.error(f"Authentication to GitHub failed. {cpe}")
            return False
        return True

    def add_blocked_pull_request(self, pull_request=None) -> Any:
        """
        Function adds pull request to self.blocked_pr dictionary with
        specific fields like 'number' and 'pr_dict': {'title': , 'labels': }
        :param pull_request: Dictionary with pull request structure
        :return:
        """
        if pull_request is None:
            pull_request = {}
        present = False
        for stored_pr in self.blocked_pr[self.container_name]:
            if int(stored_pr["number"]) == int(pull_request["number"]):
                present = True
        if present:
            return
        self.blocked_pr[self.container_name].append(
            {
                "number": pull_request["number"],
                "title": pull_request["title"],
                "labels": pull_request["labels"],
            }
        )
        self.logger.debug(f"PR {pull_request['number']} added to blocked")
        return

    def check_blocked_labels(self):
        for pr in self.repo_data:
            self.logger.debug(f"Checking PR {pr['number']}")
            if "labels" not in pr:
                continue
            for label in pr["labels"]:
                if label["name"] not in self.blocking_labels:
                    continue
                self.logger.info(f"Add PR'{pr['number']}' of '{self.container_name}' to blocked PRs.")
                self.add_blocked_pull_request(pull_request=pr)

    def check_pr_to_merge(self) -> bool:
        if len(self.repo_data) == 0:
            return False
        pr_to_merge: bool = False
        for pr in self.repo_data:
            self.logger.debug(f"PR status: {pr}")
            if not PullRequestHandler.check_labels_to_merge(pull_request=pr, blocking_labels=self.blocking_labels):
                continue
            if "reviews" not in pr:
                continue
            approval_count = PullRequestHandler.check_pr_approvals(reviews_to_check=pr["reviews"])
            if approval_count < self.approvals:
                self.logger.debug(f"Not enough approvals: {approval_count}. Should be at least {self.approvals}")
                continue
            self.pr_to_merge[self.container_name] = {
                "number": pr["number"],
                "approvals": approval_count,
                "title": pr["title"],
            }
            pr_to_merge = True
        return pr_to_merge

    def clone_repo(self):
        self.temp_dir = utils.temporary_dir()
        self.container_dir = Path(self.temp_dir) / f"{self.container_name}"
        utils.run_command(
            f"gh repo clone https://github.com/{self.namespace}/{self.container_name} {self.container_dir}"
        )
        if self.container_dir.exists():
            os.chdir(self.container_dir)

    def merge_pull_requests(self):
        for pr in self.pr_to_merge:
            self.logger.debug(f"PR to merge {pr} in repo {self.container_name}.")

    def clean_dirs(self):
        os.chdir(self.current_dir)
        if self.container_dir.exists():
            shutil.rmtree(self.container_dir)
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def check_all_containers(self) -> bool:
        if not self.is_authenticated():
            return False
        for container in self.config.github["repos"]:
            self.logger.info(f"Let's check repository in {self.namespace}/{container}")
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
                self.check_pr_to_merge()
            except subprocess.CalledProcessError:
                self.clean_dirs()
                self.logger.error(f"Something went wrong {self.container_name}.")
                continue
            self.clean_dirs()
        return True

    def get_blocked_labels(self, pr_dict) -> list[str]:
        return [lbl["name"] for lbl in pr_dict if lbl["name"] in self.blocking_labels]

    def print_blocked_pull_request(self) -> bool:
        self.logger.warning("SUMMARY OF BLOCKED PULL REQUESTS")
        if not self.pr_to_merge:
            return False
        self.logger.debug(self.blocked_pr)
        is_there_something = [cont for cont in self.blocked_pr.keys() if self.blocked_pr[cont]]
        if not is_there_something:
            self.logger.warning("There is nothing what is blocked.")
            return False
        string_to_print = f"Pull requests that are blocked by labels [{', '.join(self.blocking_labels)}]"

        self.logger.info(f"SUMMARY\n{string_to_print}\n")
        self.blocked_body.append(f"{string_to_print}</b><br><br>")

        for container, pull_requests in self.blocked_pr.items():
            if not pull_requests:
                continue
            self.logger.warning(f"\n{container}\n")
            self.blocked_body.append(f"<b>{container}<b>:")
            self.blocked_body.append("<table><tr><th>Pull request URL</th><th>Title</th><th>Missing labels</th></tr>")
            for pr in pull_requests:
                self.logger.debug(f"Print PR {pr}.")
                blocked_labels = self.get_blocked_labels(pr["labels"])
                self.logger.warning(
                    f"https://github.com/{self.namespace}/{container}/pull/{pr['number']} {' '.join(blocked_labels)}"
                )
                self.blocked_body.append(
                    f"<tr><td>https://github.com/{self.namespace}/{container}/pull/{pr['number']}</td>"
                    f"<td>{pr['title']}</td><td><p style='color:red;'>"
                    f"{' '.join(blocked_labels)}</p></td></tr>"
                )
        self.blocked_body.append("</table><br><br>")
        return True

    def print_approval_pull_request(self):
        # Do not print anything in case we do not have PR.
        if not [x for x in self.pr_to_merge if self.pr_to_merge[x]]:
            return
        self.logger.warning("SUMMARY\n\nPull requests that can be merged approvals")
        self.approval_body.append(f"Pull requests that can be merged or missing {self.approvals} approvals")
        self.approval_body.append("<table><tr><th>Pull request URL</th><th>Title</th><th>Approval status</th></tr>")
        for container, pr in self.pr_to_merge.items():
            if not pr:
                continue
            if int(pr["approvals"]) >= self.approvals:
                result_pr = "CAN BE MERGED"
            else:
                result_pr = f"Missing {self.approvals-int(pr['approvals'])} APPROVAL"
            self.logger.warning(f"https://github.com/{self.namespace}/{container}/pull/{pr['number']} - {result_pr}")
            self.approval_body.append(
                f"<tr><td>https://github.com/{self.namespace}/{container}/pull/{pr['number']}</td>"
                f"<td>{pr['pr_dict']['title']}</td><td><p style='color:red;'>{result_pr}</p></td></tr>"
            )
        self.approval_body.append("</table><br>")

    def send_results(self, recipients):
        self.logger.debug(f"Recipients are: {recipients}")
        if not recipients:
            return
        sender_class = EmailSender(recipient_email=list(recipients))
        subject_msg = f"Pull request statuses for organization https://github.com/{self.namespace}"
        sender_class.send_email(subject_msg, self.blocked_body + self.approval_body)
