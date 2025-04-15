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

from flexmock import flexmock

from auto_merger.config import Config
from auto_merger.github_checker import GitHubStatusChecker

from tests.conftest import default_config_merger


def test_get_gh_pr_list(get_pr_missing_ci):
    flexmock(GitHubStatusChecker).should_receive("get_gh_json_output").and_return(get_pr_missing_ci)
    test_config = Config()
    auto_merger = GitHubStatusChecker(config=test_config.get_from_dict(default_config_merger()))
    auto_merger.container_name = "s2i-nodejs-container"
    auto_merger.get_gh_pr_list()
    assert auto_merger.repo_data


def test_get_gh_two_pr_labels_missing(get_two_pr_missing_labels):
    flexmock(GitHubStatusChecker).should_receive("get_gh_json_output").and_return(get_two_pr_missing_labels)
    test_config = Config()
    auto_merger = GitHubStatusChecker(config=test_config.get_from_dict(default_config_merger()))
    auto_merger.container_name = "s2i-nodejs-container"
    auto_merger.get_gh_pr_list()
    assert auto_merger.repo_data
    assert not auto_merger.check_pr_to_merge()


def test_get_gh_pr_missing_ci(get_pr_missing_ci):
    flexmock(GitHubStatusChecker).should_receive("get_gh_json_output").and_return(get_pr_missing_ci)
    test_config = Config()
    auto_merger = GitHubStatusChecker(config=test_config.get_from_dict(default_config_merger()))
    auto_merger.container_name = "s2i-nodejs-container"
    auto_merger.get_gh_pr_list()
    assert auto_merger.repo_data
    assert not auto_merger.check_pr_to_merge()


def test_get_no_pr_for_merge():
    flexmock(GitHubStatusChecker).should_receive("get_gh_json_output").and_return([])
    test_config = Config()
    auto_merger = GitHubStatusChecker(config=test_config.get_from_dict(default_config_merger()))
    auto_merger.container_name = "s2i-nodejs-container"
    auto_merger.get_gh_pr_list()
    assert not auto_merger.repo_data
    assert not auto_merger.check_pr_to_merge()
