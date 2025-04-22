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
import logging
import subprocess
import os
import shutil

from subprocess import CalledProcessError
from pathlib import Path

from auto_merger import utils
from auto_merger.config import Config
from auto_merger.utils import cwd
from auto_merger.email import EmailSender
from auto_merger.pull_request_handler import PullRequestHandler


logger = logging.getLogger(__name__)


class AutoMerger:
    container_name: str = ""
    container_dir: Path
    current_dir = os.getcwd()

    def __init__(self, config: Config):
        self.config = config
        self.approval_labels = self.config.github["approval_labels"]
        self.blocking_labels = self.config.github["blocker_labels"]
        self.approvals = self.config.github["approvals"]
        self.namespace = self.config.github["namespace"]
        self.pr_lifetime = self.config.github["pr_lifetime"]
        self.pr_to_merge: dict = {}
        self.approval_body: list = []
        self.repo_data: list = []
        self.temp_dir = utils.temporary_dir()

    def is_correct_repo(self) -> bool:
        cmd = ["gh repo view --json name"]
        repo_name = AutoMerger.get_gh_json_output(cmd=cmd)
        logger.debug(repo_name)
        if repo_name["name"] == self.container_name:
            return True
        return False

    @staticmethod
    def get_gh_json_output(cmd):
        gh_repo_list = utils.run_command(cmd=cmd, return_output=True)
        return json.loads(gh_repo_list)

    def get_gh_pr_list(self):
        cmd = ["gh pr list -s open --json number,title,labels,reviews,isDraft,createdAt"]
        repo_data_output = AutoMerger.get_gh_json_output(cmd=cmd)
        for pr in repo_data_output:
            if PullRequestHandler.is_draft(pull_request=pr):
                continue
            if PullRequestHandler.is_changes_requested(pull_request=pr):
                continue
            self.repo_data.append(pr)

    def is_authenticated(self) -> bool:
        token = os.getenv("GH_TOKEN")
        if token == "":
            logger.error("Environment variable GH_TOKEN is not specified.")
            return False
        cmd = ["gh status"]
        logger.debug(f"Authentication command: {cmd}")
        try:
            utils.run_command(cmd=cmd, return_output=True)
        except subprocess.CalledProcessError as cpe:
            logger.error(f"Authentication to GitHub failed. {cpe}")
            return False
        return True

    def check_labels_to_merge(self, pr) -> bool:
        if "labels" not in pr:
            return False
        logger.debug(f"check_labels_to_merge for {self.container_name}: {pr['labels']} and {self.approval_labels}")
        for label in pr["labels"]:
            if label["name"] in self.approval_labels:
                logger.debug(f"Add '{pr['number']}' to approved PRs.")
                return True
        return False

    def check_pr_to_merge(self) -> bool:
        if len(self.repo_data) == 0:
            return False
        for pr in self.repo_data:
            if not self.check_labels_to_merge(pr):
                logger.debug(
                    f"check_pr_to_merge for {self.container_name}: " f"pull request {pr['number']} did not met labels."
                )
                continue
            if "reviews" not in pr:
                logger.debug(
                    f"check_pr_to_merge for {self.container_name}:"
                    f" pull request {pr['number']} does not have reviews yet."
                )
                continue
            approval_count = PullRequestHandler.check_pr_approvals(reviews_to_check=pr["reviews"])
            if approval_count < self.approvals:
                logger.debug(f"Not enough approvals: {approval_count}. Should be at least {self.approvals}")
                continue
            logger.debug(f"Approval count is {approval_count}")
            if not PullRequestHandler.check_pr_lifetime(pull_request=pr):
                logger.debug(f"Pr is not valid for more  then {self.config.github['pr_lifetime']}")
                continue
            self.pr_to_merge[self.container_name].append(
                {
                    "number": pr["number"],
                    "approvals": approval_count,
                    "title": pr["title"],
                }
            )
        logger.debug(self.pr_to_merge)
        return True

    def clone_repo(self):
        self.container_dir = Path(self.temp_dir) / f"{self.container_name}"
        try:
            utils.run_command(
                f"gh repo clone https://github.com/{self.namespace}/{self.container_name} {self.container_dir}"
            )
        except CalledProcessError as cpe:
            logger.error(cpe.stderr)
            return False
        return True

    def merge_pull_requests(self):
        for container in self.config.github["repos"]:
            self.container_name = container
            self.container_dir = Path(self.temp_dir) / f"{self.container_name}"
            with cwd(self.container_dir) as _:
                self.merge_pr()
        os.chdir(self.current_dir)

    def clean_temporary_dir(self):
        os.chdir(self.current_dir)
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def clean_container_dir(self):
        os.chdir(self.current_dir)
        if Path(self.container_dir).exists():
            shutil.rmtree(self.container_dir)

    def merge_pr(self):
        for pr in self.pr_to_merge[self.container_name]:
            if int(pr["approvals"]) < self.approvals:
                logger.debug(
                    f"Automerger does not have enough approvals '{pr['approvals']}' against '{self.approvals}' "
                )
                continue

            logger.info(f"Let's try to merge {pr['number']}....")
            try:
                output = utils.run_command(f"gh pr merge --rebase --auto {pr['number']}", return_output=True)
                logger.debug(f"The output from merging command '{output}'")
                logger.info(f"Pull request {pr['number']} was merged.")
            except subprocess.CalledProcessError as cpe:
                logger.error(f"Merging pr {pr} failed with reason {cpe.output}")
                continue

    def check_all_containers(self) -> bool:
        if not self.is_authenticated():
            return False
        for container in self.config.github["repos"]:
            self.container_name = container
            self.repo_data = []
            if not self.clone_repo():
                continue
            with cwd(self.container_dir) as _:
                if not self.is_correct_repo():
                    logger.error(f"This is not correct repo {self.container_name}.")
                    self.clean_container_dir()
                    continue
                if self.container_name not in self.pr_to_merge:
                    self.pr_to_merge[self.container_name] = []
                try:
                    self.get_gh_pr_list()
                    self.check_pr_to_merge()
                except subprocess.CalledProcessError:
                    logger.error(f"Something went wrong {self.container_name}.")
                    continue
        os.chdir(self.current_dir)
        logger.debug(f"List of all PRs to merge: '{self.pr_to_merge}'")
        return True

    def print_pull_request_to_merge(self) -> bool:
        logger.info("SUMMARY")
        if not self.pr_to_merge:
            return False
        is_there_something = [cont for cont in self.pr_to_merge.keys() if self.pr_to_merge[cont]]
        if not is_there_something:
            logger.info("There is nothing to send or merge.")
            return False
        self.approval_body.append("Pull requests are merged.")
        self.approval_body.append("<table><tr><th>Pull request URL</th><th>Title</th><th>Approval status</th></tr>")
        for cont, pr_list in self.pr_to_merge.items():
            logger.debug(f"Print info about {cont} and {pr_list}.")
            for pr in pr_list:
                if not pr:
                    continue
                logger.info(f"https://github.com/{self.namespace}/{cont}/pull/{pr['number']} -> CAN BE MERGED")
                self.approval_body.append(
                    f"<tr><td> https://github.com/{self.namespace}/{cont}/pull/{pr['number']} </td>"
                    f"<td> {pr['title']} </td><td><p style='color:red;'> CAN BE MERGED </p></td></tr>"
                )
        self.approval_body.append("</table><br>")
        return True

    def send_results(self, recipients):
        logger.debug(f"Recipients are: {recipients}")
        if not recipients:
            return False
        sender_class = EmailSender(recipient_email=list(recipients))
        subject_msg = "Merge request update"
        if self.approval_body:
            sender_class.send_email(subject_msg, self.approval_body)
        else:
            logger.info("Nothing to send.")
