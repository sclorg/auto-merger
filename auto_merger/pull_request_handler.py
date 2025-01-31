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
import logging

from datetime import datetime, timedelta

from auto_merger import utils

logger = logging.getLogger(__name__)


class PullRequestHandler:
    @staticmethod
    def check_pr_lifetime(pull_request: dict = None, pr_lifetime: int = 0) -> bool:
        if pull_request is None:
            return False
        if pr_lifetime == 0:
            return True
        if "createdAt" not in pull_request:
            return False
        pr_life = pull_request["createdAt"]
        date_created = datetime.strptime(pr_life, "%Y-%m-%dT%H:%M:%SZ") + timedelta(days=1)
        if date_created < utils.get_realtime():
            return True
        return False

    @staticmethod
    def is_draft(pull_request: dict):
        if "isDraft" in pull_request:
            if pull_request["isDraft"] in ["True", "true"]:
                return True
        return False

    @staticmethod
    def check_pr_approvals(reviews_to_check: list) -> int:
        if not reviews_to_check:
            return 0
        approval_cnt = 0
        for review in reviews_to_check:
            if review["state"] == "APPROVED":
                approval_cnt += 1
        return approval_cnt

    @staticmethod
    def is_changes_requested(pull_request: dict):
        if "labels" not in pull_request:
            return False
        for labels in pull_request["labels"]:
            if "pr/changes-requested" == labels["name"]:
                return True
        return False

    @staticmethod
    def check_labels_to_merge(pull_request: dict, blocking_labels: list) -> bool:
        """
        Function checks labels for each pull request
        'label' is compared against configuration file 'github': 'blocking_labels'
        :param pr: pull request dictionary with labels
        :return: False is labels are not present or 'label' is int 'blocking_labels'
                 True pull request is approved. No blocking issue
        """
        if "labels" not in pull_request:
            return False
        for label in pull_request["labels"]:
            if label["name"] in blocking_labels:
                return False
        logger.debug(f"Add '{pull_request['number']}' to approved PRs.")
        return True
