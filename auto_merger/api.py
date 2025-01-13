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

import logging

from typing import List

from auto_merger.pr_checker import PRStatusChecker
from auto_merger.config import Config
from auto_merger.merger import AutoMerger

logger = logging.getLogger(__name__)


def pull_request_checker(config: Config, print_results: bool, send_email: List[str]) -> int:
    """
    Checks NVR from brew build against pulp
    """
    pr_status_checker = PRStatusChecker(config=config)
    ret_value = pr_status_checker.check_all_containers()
    if ret_value != 0:
        return ret_value
    if print_results:
        pr_status_checker.print_blocked_pull_request()
        pr_status_checker.print_approval_pull_request()
    if not pr_status_checker.send_results(send_email):
        return 1
    return ret_value


def merger(config: Config, print_results: bool, send_email: List[str]) -> int:
    auto_merger = AutoMerger(config=config)
    ret_value = auto_merger.check_all_containers()
    if ret_value != 0:
        return ret_value
    if print_results:
        auto_merger.print_pull_request_to_merge()
    auto_merger.merge_pull_requests()
    if not auto_merger.send_results(send_email):
        return 1
    return ret_value