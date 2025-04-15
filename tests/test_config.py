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

from auto_merger.config import Config

from tests.conftest import get_config_dict_miss_approval_lifetime, get_config_dict_simple


@pytest.fixture()
def get_config_simple():
    config = Config()
    config.debug = True
    github_dict = {
        "namespace": "foobar",
        "repos": ["repo1"],
        "approvals": 23,
        "pr_lifetime": 2,
        "blocker_labels": [
            "pr/foobar1",
        ],
        "approval_labels": ["ok-to-merge"],
    }
    config.github = github_dict
    config.gitlab = None
    return config


@pytest.fixture()
def get_config_miss_approval_and_lifetime():
    config = Config()
    config.debug = True
    github_dict = {
        "namespace": "foobar",
        "repos": ["repo1"],
        "approvals": 2,
        "pr_lifetime": 1,
        "blocker_labels": [
            "pr/foobar1",
        ],
        "approval_labels": ["ok-to-merge"],
    }
    config.github = github_dict
    config.gitlab = None
    return config


def test_config_equal(get_config_simple):
    config = Config.get_from_dict(raw_dict=get_config_dict_simple())
    assert config.debug == get_config_simple.debug
    assert config.github == get_config_simple.github
    assert config.gitlab == get_config_simple.gitlab


def test_config_equal_missing_approval(get_config_miss_approval_and_lifetime):
    config = Config.get_from_dict(raw_dict=get_config_dict_miss_approval_lifetime())
    assert config.debug == get_config_miss_approval_and_lifetime.debug
    assert config.github == get_config_miss_approval_and_lifetime.github
    assert config.gitlab == get_config_miss_approval_and_lifetime.gitlab
