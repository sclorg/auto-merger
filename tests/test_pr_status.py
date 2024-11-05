#!/usr/bin/env python3

from flexmock import flexmock

from auto_merger.merger import AutoMerger


def test_get_gh_pr_list(get_pr_missing_ci):
    flexmock(AutoMerger).should_receive("get_gh_json_output").and_return(
        get_pr_missing_ci
    )
    auto_merger = AutoMerger(github_labels=["READY-to-MERGE"], blocking_labels=["pr/missing-review", 'pr/failing-ci'])
    auto_merger.container_name = "s2i-nodejs-container"
    auto_merger.get_gh_pr_list()
    assert auto_merger.repo_data


def test_get_gh_two_pr_labels_missing(get_two_pr_missing_labels):
    flexmock(AutoMerger).should_receive("get_gh_json_output").and_return(
        get_two_pr_missing_labels
    )
    auto_merger = AutoMerger(github_labels=["READY-to-MERGE"], blocking_labels=["pr/missing-review", 'pr/failing-ci'])
    auto_merger.container_name = "s2i-nodejs-container"
    auto_merger.get_gh_pr_list()
    assert auto_merger.repo_data
    assert not auto_merger.check_pr_to_merge()


def test_get_gh_pr_missing_ci(get_pr_missing_ci):
    flexmock(AutoMerger).should_receive("get_gh_json_output").and_return(
        get_pr_missing_ci
    )
    auto_merger = AutoMerger(github_labels=["READY-to-MERGE"], blocking_labels=["pr/missing-review", 'pr/failing-ci'])
    auto_merger.container_name = "s2i-nodejs-container"
    auto_merger.get_gh_pr_list()
    assert auto_merger.repo_data
    assert not auto_merger.check_pr_to_merge()


def test_get_no_pr_for_merge():
    flexmock(AutoMerger).should_receive("get_gh_json_output").and_return([])
    auto_merger = AutoMerger(github_labels=["READY-to-MERGE"], blocking_labels=["pr/missing-review", 'pr/failing-ci'])
    auto_merger.container_name = "s2i-nodejs-container"
    auto_merger.get_gh_pr_list()
    assert not auto_merger.repo_data
    assert not auto_merger.check_pr_to_merge()
