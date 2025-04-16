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
from auto_merger.gitlab_checker import GitLabStatusChecker
from auto_merger.gitlab_handler import GitLabHandler
from auto_merger.named_tuples import ProjectMR

from tests.conftest import default_config_merger, no_gitlab_repos_config


def test_gl_check_auth_failed():
    flexmock(GitLabHandler).should_receive("check_authentication").and_return(False)
    test_config = Config()
    auto_merger = GitLabStatusChecker(config=test_config.get_from_dict(default_config_merger()))
    assert not auto_merger.check_gitlab_status()


def test_gl_not_repos(get_pr_missing_ci):
    flexmock(GitLabHandler).should_receive("check_authentication").and_return(True)
    test_config = Config()
    auto_merger = GitLabStatusChecker(config=test_config.get_from_dict(no_gitlab_repos_config()))
    assert not auto_merger.check_all_containers()


def test_gl_check_all_containers(get_pr_missing_ci, merge_requests_psql_13):
    flexmock(GitLabHandler).should_receive("check_authentication").and_return(True)
    flexmock(GitLabHandler).should_receive("get_project_id_from_url").and_return()
    flexmock(GitLabHandler).should_receive("get_project_merge_requests").and_return(merge_requests_psql_13)
    test_config = Config()
    auto_merger = GitLabStatusChecker(config=test_config.get_from_dict(default_config_merger()))
    auto_merger.container_name = "postgresql-15"
    assert auto_merger.check_all_containers()
    assert len(auto_merger.merge_requests) == 1
    print(auto_merger.blocked_mr)
    p_mr: ProjectMR = merge_requests_psql_13[0]
    assert auto_merger.blocked_mr[auto_merger.config.gitlab["namespace"] + "/postgresql-13"]
    blocker_mr: dict = auto_merger.blocked_mr[auto_merger.config.gitlab["namespace"] + "/postgresql-13"][0]
    assert blocker_mr["number"] == p_mr.iid
    assert blocker_mr["title"] == p_mr.title
