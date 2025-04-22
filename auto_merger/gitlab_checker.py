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


import os
import logging

from typing import Any
from pathlib import Path

import requests

from auto_merger.gitlab_handler import GitLabHandler
from auto_merger.email import EmailSender
from auto_merger.config import Config
from auto_merger.named_tuples import ProjectMR
from auto_merger.pull_request_handler import PullRequestHandler
from auto_merger import utils


logger = logging.getLogger(__name__)


class GitLabStatusChecker:
    container_name: str = ""
    container_dir: Path
    current_dir = os.getcwd()

    def __init__(self, config: Config, json_output_file: str = ""):
        self.config = config
        self.approval_labels = self.config.gitlab["approval_labels"]
        self.blocking_labels = self.config.gitlab["blocker_labels"]
        self.approvals = self.config.gitlab["approvals"]
        if "namespace" in self.config.gitlab:
            self.namespace = self.config.gitlab["namespace"]
        else:
            self.namespace = None
        self.blocked_mr: dict = {}
        self.pr_to_merge: dict = {}
        self.blocked_body: list = []
        self.approval_body: list = []
        self.merge_requests: list = []
        self.temp_dir: Path
        self._gitlab_handler = None
        self.project_id: str = ""
        self.json_output_file = json_output_file

    @property
    def gitlab_handler(self):
        if not self._gitlab_handler:
            self._gitlab_handler = GitLabHandler(config=self.config)
        return self._gitlab_handler

    def check_gitlab_status(self) -> bool:
        if not self.gitlab_handler.check_authentication():
            logger.error("GitLab authentication failed.")
            return False
        if "repos" not in self.config.gitlab:
            return False
        if self.json_output_file is not None:
            if not utils.check_json_path(json_file_path=self.json_output_file):
                return False
        return True

    def add_blocked_pull_request(self, merge_request=None) -> Any:
        """
        Function adds pull request to self.blocked_pr dictionary with
        specific fields like 'number' and 'pr_dict': {'title': , 'labels': }
        :param pull_request: Dictionary with pull request structure
        :return:
        """
        if merge_request is None:
            merge_request = {}
        present = False
        for stored_pr in self.blocked_mr[self.container_name]:
            if int(stored_pr["number"]) == int(merge_request.iid):
                present = True
        if present:
            return
        self.blocked_mr[self.container_name].append(
            {
                "number": merge_request.iid,
                "title": merge_request.title,
                "labels": merge_request.labels,
                "target_url": merge_request.target_project_id,
            }
        )
        logger.debug(f"PR {merge_request.iid} added to blocked")
        return

    def check_blocked_labels(self):
        for mr in self.merge_requests:
            logger.info(f"- Checking PR {mr.iid} for {self.container_name}")
            logger.debug(f"Labels: {mr.labels}")
            if not mr.labels:
                self.add_blocked_pull_request(merge_request=mr)
                continue
            logger.debug(self.blocking_labels)
            for label in mr.labels:
                if label not in self.blocking_labels:
                    continue
                logger.info(f"Add PR {mr.iid} to blocked PRs.")
                self.add_blocked_pull_request(merge_request=mr)

    def check_pr_to_merge(self) -> bool:
        if len(self.repo_data) == 0:
            return False
        pr_to_merge: bool = False
        for pr in self.repo_data:
            logger.debug(f"PR status: {pr}")
            if not PullRequestHandler.check_labels_to_merge(pull_request=pr, blocking_labels=self.blocking_labels):
                continue
            if "reviews" not in pr:
                continue
            approval_count = PullRequestHandler.check_pr_approvals(reviews_to_check=pr["reviews"])
            if approval_count < self.approvals:
                logger.debug(f"Not enough approvals: {approval_count}. Should be at least {self.approvals}")
                continue
            self.pr_to_merge[self.container_name] = {
                "number": pr["number"],
                "approvals": approval_count,
                "title": pr["title"],
            }
            pr_to_merge = True
        return pr_to_merge

    def merge_pull_requests(self):
        for pr in self.pr_to_merge:
            logger.debug(f"PR to merge {pr} in repo {self.container_name}.")

    def check_all_containers(self) -> bool:
        if "repos" not in self.config.gitlab:
            return False
        for container in self.config.gitlab["repos"]:
            self.container_name = container if not self.namespace else f"{self.namespace}/{container}"
            logger.info(f"Let's check repository in {self.container_name}")
            if self.container_name not in self.blocked_mr:
                self.blocked_mr[self.container_name] = []
            if self.container_name not in self.pr_to_merge:
                self.pr_to_merge[self.container_name] = []
            try:
                self.project_id = self.gitlab_handler.get_project_id_from_url(
                    url=self.config.gitlab["url"], reponame=self.container_name
                )
                self.merge_requests: list[ProjectMR] = self.gitlab_handler.get_project_merge_requests(self.project_id)
                logger.debug(f"List of MR for {self.container_name}")
                if not self.merge_requests:
                    logger.info(f"No merge requests opened for project {self.container_name}")
                    continue
                logger.debug(self.merge_requests)
                self.check_blocked_labels()
                # self.check_pr_to_merge()
            except requests.HTTPError:
                logger.error(f"Something went wrong {self.container_name}.")
                continue
        return True

    def get_blocked_labels(self, pr_dict) -> str:
        return " ".join(pr_dict)

    def print_blocked_merge_requests(self) -> bool:
        logger.debug(f"Blocked PR to print {self.blocked_mr}")
        if not self.blocked_mr:
            return False
        logger.warning(
            f"SUMMARY\n\nGitLab merge requests that are blocked by labels [{', '.join(self.blocking_labels)}]"
        )
        self.blocked_body.append(
            f"GitLab merge requests that are blocked by labels <b>[{', '.join(self.blocking_labels)}]</b><br><br>"
        )

        for container, merge_requests in self.blocked_mr.items():
            if not merge_requests:
                continue
            logger.info(f"\n{container}\n------\n")
            self.blocked_body.append(f"<b>{container}<b>:")
            self.blocked_body.append("<table><tr><th>Merge request URL</th><th>Title</th><th>Missing labels</th></tr>")
            for mr in merge_requests:
                blocked_labels = self.get_blocked_labels(mr["labels"])
                if blocked_labels == "":
                    blocked_labels = "No labels to unblock this merge request."
                logger.info(f"{self.config.gitlab['url']}/{container}/-/merge_requests/{mr['number']} '{mr['title']}'")
                self.blocked_body.append(
                    f"<tr><td>{self.config.gitlab['url']}/{container}/-/merge_requests/{mr['number']}</td>"
                    f"<td>{mr['title']}</td><td><p style='color:red;'>"
                    f"'{blocked_labels}'</p></td></tr>"
                )
        self.blocked_body.append("</table><br><br>")
        return True

    def print_approval_pull_request(self):
        # Do not print anything in case we do not have PR.
        if not [x for x in self.pr_to_merge if self.pr_to_merge[x]]:
            return
        logger.info("SUMMARY\n\nGitLab merge requests that can be merged approvals")
        self.approval_body.append(f"GitLab merge requests that can be merged or missing {self.approvals} approvals")
        self.approval_body.append("<table><tr><th>Merge request URL</th><th>Title</th><th>Approval status</th></tr>")
        for container, pr in self.pr_to_merge.items():
            if not pr:
                continue
            if int(pr["approvals"]) >= self.approvals:
                result_pr = "CAN BE MERGED"
            else:
                result_pr = f"Missing {self.approvals-int(pr['approvals'])} APPROVAL"
            logger.info(f"https://github.com/{self.namespace}/{container}/pull/{pr['number']} - {result_pr}")
            self.approval_body.append(
                f"<tr><td>https://github.com/{self.namespace}/{container}/pull/{pr['number']}</td>"
                f"<td>{pr['pr_dict']['title']}</td><td><p style='color:red;'>{result_pr}</p></td></tr>"
            )
        self.approval_body.append("</table><br>")

    def save_results(self):
        return utils.save_json_file(json_file_path=self.json_output_file, json_dict=self.blocked_mr)

    def send_results(self, recipients):
        logger.debug(f"Recipients are: {recipients}")
        if not recipients:
            return
        sender_class = EmailSender(recipient_email=list(recipients))
        subject_msg = f"Pull request statuses for organization https://github.com/{self.namespace}"
        sender_class.send_email(subject_msg, self.blocked_body + self.approval_body)
