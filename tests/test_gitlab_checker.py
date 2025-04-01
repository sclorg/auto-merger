#!/usr/bin/env python3

from flexmock import flexmock

from auto_merger.config import Config
from auto_merger.gitlab_checker import GitLabStatusChecker
from auto_merger.gitlab_handler import GitLabHandler
from auto_merger.named_tuples import ProjectMR


def test_gl_check_auth_failed(default_config_merger):
    flexmock(GitLabHandler).should_receive("check_authentication").and_return(False)
    test_config = Config()
    auto_merger = GitLabStatusChecker(config=test_config.get_from_dict(default_config_merger))
    assert not auto_merger.check_all_containers()


def test_gl_not_repos(get_pr_missing_ci, no_gitlab_repos_config):
    flexmock(GitLabHandler).should_receive("check_authentication").and_return(True)
    test_config = Config()
    auto_merger = GitLabStatusChecker(config=test_config.get_from_dict(no_gitlab_repos_config))
    assert not auto_merger.check_all_containers()


def test_gl_check_all_containers(get_pr_missing_ci, default_config_merger, merge_requests_psql_13):
    flexmock(GitLabHandler).should_receive("check_authentication").and_return(True)
    flexmock(GitLabHandler).should_receive("get_project_id_from_url").and_return()
    flexmock(GitLabHandler).should_receive("get_project_merge_requests").and_return(merge_requests_psql_13)
    test_config = Config()
    auto_merger = GitLabStatusChecker(config=test_config.get_from_dict(default_config_merger))
    auto_merger.container_name = "postgresql-15"
    assert auto_merger.check_all_containers()
    assert len(auto_merger.merge_requests) == 1
    print(auto_merger.blocked_mr)
    p_mr: ProjectMR = merge_requests_psql_13[0]
    assert auto_merger.blocked_mr[auto_merger.config.gitlab["namespace"] + "/postgresql-13"]
    blocker_mr: dict = auto_merger.blocked_mr[auto_merger.config.gitlab["namespace"] + "/postgresql-13"][0]
    assert blocker_mr["number"] == p_mr.iid
    assert blocker_mr["title"] == p_mr.title
