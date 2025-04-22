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

from auto_merger.github_checker import GitHubStatusChecker
from auto_merger.gitlab_checker import GitLabStatusChecker
from auto_merger.config import Config
from auto_merger.merger import AutoMerger


logger = logging.getLogger(__name__)


def merge_request_checker(config: Config, send_email: list[str] | None, json_output: str = "") -> int:
    """
    Checks NVR from brew build against pulp
    """
    logger.debug(f"Configuration: {config.__str__()}")
    logger.debug(f"Json path: {json_output}")
    gl_checker = GitLabStatusChecker(config=config, json_output_file=json_output)
    if not gl_checker.check_gitlab_status():
        return 1
    ret_value = gl_checker.check_all_containers()
    if not ret_value:
        return ret_value
    gl_checker.print_blocked_merge_requests()
    gl_checker.print_approval_pull_request()
    if json_output:
        gl_checker.save_results()
    if send_email:
        if not gl_checker.send_results(send_email):
            return 1
    return ret_value


def pull_request_checker(config: Config, send_email: list[str] | None, json_output: str = "") -> int:
    """
    Checks NVR from brew build against pulp
    """
    logger.debug(f"Configuration: {config.__str__()}")
    logger.debug(f"Json path: {json_output}")
    gh_checker = GitHubStatusChecker(config=config, json_output_file=json_output)
    try:
        if not gh_checker.check_github_status():
            return 1

        ret_value = gh_checker.check_all_containers()
        if not ret_value:
            return ret_value
        gh_checker.print_blocked_pull_request()
        gh_checker.print_approval_pull_request()
        if json_output:
            gh_checker.save_results()
        if send_email:
            if not gh_checker.send_results(send_email):
                return 1
    finally:
        gh_checker.clean_temporary_dir()


def merger(config: Config, send_email: list[str] | None) -> int:
    logger.debug(f"Configuration: {config.__str__()}")
    auto_merger = AutoMerger(config=config)
    ret_value = auto_merger.check_all_containers()
    try:
        if not ret_value:
            return ret_value
        is_there_pr_to_merge = auto_merger.print_pull_request_to_merge()
        if not is_there_pr_to_merge:
            return 0
        auto_merger.merge_pull_requests()
        if send_email:
            if not auto_merger.send_results(send_email):
                return 1
    finally:
        auto_merger.clean_temporary_dir()
