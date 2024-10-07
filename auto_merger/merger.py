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


class AutoMerger:
    repo_data: List = []
    pr_to_merge: List[int] = []
    container_name: str = ""
    container_dir: Path
    current_dir = os.getcwd()

    def __init__(self):
        self.logger = setup_logger("AutoMerger")

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
        cmd = ["gh pr list -s open --json number,title,labels,reviews"]
        self.repo_data = AutoMerger.get_gh_json_output(cmd=cmd)

    def check_pr_labels(self, labels_to_check) -> bool:
        self.logger.debug(f"Labels to check: {labels_to_check}")
        if not labels_to_check:
            return False
        pr_failed_tags = ["pr/missing_review", "pr/failing-ci"]
        pr_present = ["READY-to-MERGE"]
        failed_pr = True
        for label in labels_to_check:
            if label["name"] in pr_failed_tags:
                failed_pr = False
            if label["name"] not in pr_present:
                failed_pr = False
        return failed_pr

    def check_pr_approvals(self, reviews_to_check) -> bool:
        self.logger.debug(f"Approvals to check: {reviews_to_check}")
        if not reviews_to_check:
            return False
        approval = "APPROVED"
        approval_cnt = 0
        for review in reviews_to_check:
            if review["state"] == approval:
                approval_cnt += 1
        if approval_cnt < 2:
            self.logger.debug(f"Approval count: {approval_cnt}")
            return False
        return True

    def check_pr_to_merge(self) -> bool:
        if len(self.repo_data) == 0:
            return False
        pr_to_merge = []
        for pr in self.repo_data:
            self.logger.debug(f"PR status: {pr}")
            if "labels" not in pr:
                continue
            if not self.check_pr_labels(pr["labels"]):
                self.logger.info(
                    f"PR {pr['number']} does not have valid flag to merging in repo {self.container_name}."
                )
                continue
            if not self.check_pr_approvals(pr["reviews"]):
                self.logger.info(
                    f"PR {pr['number']} does not have enought APPROVALS to merging in repo {self.container_name}."
                )
                continue
            pr_to_merge.append(pr["number"])
        self.logger.debug(f"PR to merge {pr_to_merge}")
        if not pr_to_merge:
            return False
        self.pr_to_merge = pr_to_merge
        return True

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

    def check_all_containers(self):
        for container in UPSTREAM_REPOS:
            self.pr_to_merge = []
            self.container_name = container
            self.clone_repo()
            if not self.is_correct_repo():
                self.logger.error(f"This is not correct repo {self.container_name}.")
                self.clean_dirs()
                continue
            try:
                self.get_gh_pr_list()
                if self.check_pr_to_merge():
                    self.logger.info(
                        f"This pull request can be merged {self.pr_to_merge}"
                    )
                    # auto_merger.merge_pull_requests()
            except subprocess.CalledProcessError:
                self.clean_dirs()
                self.logger.error(f"Something went wrong {self.container_name}.")
                continue
            self.clean_dirs()


def run():
    auto_merger = AutoMerger()
    auto_merger.check_all_containers()
