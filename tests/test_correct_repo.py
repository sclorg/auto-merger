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


def test_get_gh_pr_correct_repo(get_repo_name):
    flexmock(GitHubStatusChecker).should_receive("get_gh_json_output").and_return(get_repo_name)
    test_config = Config()
    auto_merger = GitHubStatusChecker(config=test_config.get_from_dict(default_config_merger()))
    auto_merger.container_name = "s2i-nodejs-container"
    assert auto_merger.is_correct_repo()


def test_get_gh_pr_wrong_repo(get_repo_wrong_name):
    flexmock(GitHubStatusChecker).should_receive("get_gh_json_output").and_return(get_repo_wrong_name)
    test_config = Config()
    auto_merger = GitHubStatusChecker(config=test_config.get_from_dict(default_config_merger()))
    auto_merger.container_name = "s2i-nodejs-container"
    assert not auto_merger.is_correct_repo()
