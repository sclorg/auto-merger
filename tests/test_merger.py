#!/usr/bin/env python3

import pytest

from datetime import datetime
from flexmock import flexmock

from auto_merger.merger import AutoMerger


@pytest.mark.parametrize(
    "pr_created_date,pr_lifetime,return_code",
    (
            ("2024-12-20T09:30:11Z", 1, False),
            ("2024-12-19T07:30:11Z", 1, True),
            ("2024-12-21T09:30:11Z", 1, False),
            ("2024-12-21T09:30:11Z", 0, True),
    )
)
def test_get_gh_pr_list(pr_created_date, pr_lifetime, return_code):
    set_time = datetime.strptime("2024-12-20T10:35:20Z", '%Y-%m-%dT%H:%M:%SZ')
    flexmock(AutoMerger).should_receive("get_realtime").and_return(set_time)
    auto_merger = AutoMerger(github_labels=["READY-to-MERGE"], approvals=1, pr_lifetime=pr_lifetime)
    pr = {
        "createdAt": pr_created_date,
    }
    assert auto_merger.check_pr_lifetime(pr) == return_code
