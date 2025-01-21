#!/usr/bin/env python3

from flexmock import flexmock

from auto_merger.config import Config
from auto_merger.pr_checker import PRStatusChecker


def test_get_gh_pr_list(get_pr_missing_ci, default_config_merger):
    flexmock(PRStatusChecker).should_receive("get_gh_json_output").and_return(get_pr_missing_ci)
    test_config = Config()
    auto_merger = PRStatusChecker(config=test_config.get_from_dict(default_config_merger))
    auto_merger.container_name = "s2i-nodejs-container"
    auto_merger.get_gh_pr_list()
    assert auto_merger.repo_data


def test_get_gh_two_pr_labels_missing(get_two_pr_missing_labels, default_config_merger):
    flexmock(PRStatusChecker).should_receive("get_gh_json_output").and_return(get_two_pr_missing_labels)
    test_config = Config()
    auto_merger = PRStatusChecker(config=test_config.get_from_dict(default_config_merger))
    auto_merger.container_name = "s2i-nodejs-container"
    auto_merger.get_gh_pr_list()
    assert auto_merger.repo_data
    assert not auto_merger.check_pr_to_merge()


def test_get_gh_pr_missing_ci(get_pr_missing_ci, default_config_merger):
    flexmock(PRStatusChecker).should_receive("get_gh_json_output").and_return(get_pr_missing_ci)
    test_config = Config()
    auto_merger = PRStatusChecker(config=test_config.get_from_dict(default_config_merger))
    auto_merger.container_name = "s2i-nodejs-container"
    auto_merger.get_gh_pr_list()
    assert auto_merger.repo_data
    assert not auto_merger.check_pr_to_merge()


def test_get_no_pr_for_merge(default_config_merger):
    flexmock(PRStatusChecker).should_receive("get_gh_json_output").and_return([])
    test_config = Config()
    auto_merger = PRStatusChecker(config=test_config.get_from_dict(default_config_merger))
    auto_merger.container_name = "s2i-nodejs-container"
    auto_merger.get_gh_pr_list()
    assert not auto_merger.repo_data
    assert not auto_merger.check_pr_to_merge()
