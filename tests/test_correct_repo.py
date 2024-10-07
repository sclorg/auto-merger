#!/usr/bin/env python3

from flexmock import flexmock

from auto_merger.merger import AutoMerger


def test_get_gh_pr_correct_repo(get_repo_name):
    flexmock(AutoMerger).should_receive("get_gh_json_output").and_return(get_repo_name)
    auto_merger = AutoMerger()
    auto_merger.container_name = "s2i-nodejs-container"
    assert auto_merger.is_correct_repo()


def test_get_gh_pr_wrong_repo(get_repo_wrong_name):
    flexmock(AutoMerger).should_receive("get_gh_json_output").and_return(
        get_repo_wrong_name
    )
    auto_merger = AutoMerger()
    auto_merger.container_name = "s2i-nodejs-container"
    assert not auto_merger.is_correct_repo()
