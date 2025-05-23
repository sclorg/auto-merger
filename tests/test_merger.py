#!/usr/bin/env python3
# MIT License
#
# Copyright (c) 2018-2019 Red Hat, Inc.

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

import pytest

from datetime import datetime
from flexmock import flexmock

from auto_merger.config import Config
from auto_merger.merger import AutoMerger
from auto_merger import utils
from auto_merger.pull_request_handler import PullRequestHandler


yaml_merger = {
    "github": {
        "namespace": "sclorg",
        "repos": ["s2i-nodejs-container"],
        "blocker_labels": ["pr/missing-review", "pr/failing-ci"],
        "approval_labels": ["READY-to-MERGE"],
        "pr_lifetime": 1,
    }
}


@pytest.mark.parametrize(
    "pr_created_date,pr_lifetime,return_code",
    (
        ("2024-12-20T09:30:11Z", 1, False),
        ("2024-12-19T07:30:11Z", 1, True),
        ("2024-12-21T09:30:11Z", 1, False),
        ("2024-12-21T09:30:11Z", 0, True),
    ),
)
def test_get_gh_pr_list(pr_created_date, pr_lifetime, return_code):
    set_time = datetime.strptime("2024-12-20T10:35:20Z", "%Y-%m-%dT%H:%M:%SZ")
    flexmock(utils).should_receive("get_realtime").and_return(set_time)
    test_config = Config()
    auto_merger = AutoMerger(config=test_config.get_from_dict(yaml_merger))
    auto_merger.pr_lifetime = pr_lifetime
    pr = {
        "createdAt": pr_created_date,
    }
    assert PullRequestHandler.check_pr_lifetime(pull_request=pr, pr_lifetime=pr_lifetime) == return_code


@pytest.mark.parametrize(
    "review_data,return_code",
    (
        ([{"state": "APPROVED"}], 1),
        ([{"state": "COMMENTED"}], 0),
        ([{"state": "APPROVED"}, {"state": "APPROVED"}], 2),
        ({}, 0),
    ),
)
def test_get_approvals(review_data, return_code):
    assert PullRequestHandler.check_pr_approvals(reviews_to_check=review_data) == return_code


@pytest.mark.parametrize(
    "pr_to_merge,return_code,approval_body",
    (
        ({}, False, []),
        ({"valkey-container": []}, False, []),
    ),
)
def test_print_pull_request_to_merge_failed(pr_to_merge, return_code, approval_body):
    test_config = Config()
    auto_merger = AutoMerger(config=test_config.get_from_dict(yaml_merger))
    auto_merger.pr_to_merge = pr_to_merge
    assert auto_merger.print_pull_request_to_merge() == return_code
    assert auto_merger.approval_body == approval_body


def test_print_pull_request_to_merge_success():
    test_config = Config()
    auto_merger = AutoMerger(config=test_config.get_from_dict(yaml_merger))
    auto_merger.pr_to_merge = {
        "valkey-container": [{"number": 2, "title": "valkey_title"}],
        "httpd-container": [],
    }
    assert auto_merger.print_pull_request_to_merge() is True
    assert auto_merger.approval_body != []
