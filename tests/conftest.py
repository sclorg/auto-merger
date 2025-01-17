# MIT License
#
# Copyright (c) 2020 SCL team at Red Hat
#
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
import json

from tests.spellbook import DATA_DIR


@pytest.fixture()
def get_repo_name():
    return json.loads((DATA_DIR / "gh_repo_name.json").read_text())


@pytest.fixture()
def get_repo_wrong_name():
    return json.loads((DATA_DIR / "gh_different_repo_name.json").read_text())


@pytest.fixture()
def get_pr_missing_ci():
    return json.loads((DATA_DIR / "pr_missing_ci.json").read_text())


@pytest.fixture()
def get_pr_missing_review():
    return json.loads((DATA_DIR / "pr_missing_review.json").read_text())


@pytest.fixture()
def get_pr_missing_ci_failed():
    return json.loads((DATA_DIR / "pr_missing_review_ci_failed.json").read_text())


@pytest.fixture()
def get_two_pr_missing_labels():
    return json.loads((DATA_DIR / "pr_two_pr_missing_labels.json").read_text())


@pytest.fixture()
def get_no_mr_to_check():
    return json.loads((DATA_DIR / "no_pr_for_merging.json").read_text())


@pytest.fixture()
def get_pr_missing_labels_approved():
    return json.loads((DATA_DIR / "pr_missing_labels_approved.json").read_text())


@pytest.fixture()
def get_pr_missing_labels_one_approval():
    return json.loads((DATA_DIR / "pr_missing_labels_one_approval.json").read_text())


@pytest.fixture()
def get_config_dict_simple():
    return {
        "github": {
            "namespace": "foobar",
            "repos": [
                "repo1"
            ],
            # How many approvals should have PR
            "approvals": 23,
            # How many days, PR should be opened
            "pr_lifetime": 2,
            # Labels that blockes merges
            "blocker_labels": [
                "pr/foobar1"
            ],
            # Labels that should be present in pull request before merging
            "approval_labels": [
                "ok-to-merge"
            ]
        }
    }


@pytest.fixture()
def get_config_dict_miss_approval_lifetime():
    return {
        "github": {
            "namespace": "foobar",
            "repos": [
                "repo1"
            ],
            # Labels that blockes merges
            "blocker_labels": [
                "pr/foobar1"
            ],
            # Labels that should be present in pull request before merging
            "approval_labels": [
                "ok-to-merge"
            ]
        }
    }


@pytest.fixture()
def default_config_merger():
    return {
        "github": {
            "namespace": "foobar",
            "repos": [
                "s2i-nodejs-container"
            ],
            "blocker_labels": ["pr/missing-review", 'pr/failing-ci'],
            "approval_labels": ["READY-to-MERGE"]
        }
    }
