#!/usr/bin/env python3

from flexmock import flexmock

from auto_merger.config import Config
from auto_merger.github_checker import GitHubStatusChecker


def test_get_gh_pr_correct_repo(get_repo_name, default_config_merger):
    flexmock(GitHubStatusChecker).should_receive("get_gh_json_output").and_return(get_repo_name)
    test_config = Config()
    auto_merger = GitHubStatusChecker(config=test_config.get_from_dict(default_config_merger))
    auto_merger.container_name = "s2i-nodejs-container"
    assert auto_merger.is_correct_repo()


def test_get_gh_pr_wrong_repo(get_repo_wrong_name, default_config_merger):
    flexmock(GitHubStatusChecker).should_receive("get_gh_json_output").and_return(get_repo_wrong_name)
    test_config = Config()
    auto_merger = GitHubStatusChecker(config=test_config.get_from_dict(default_config_merger))
    auto_merger.container_name = "s2i-nodejs-container"
    assert not auto_merger.is_correct_repo()
