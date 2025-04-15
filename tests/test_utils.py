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

import pytest

from auto_merger.utils import check_mandatory_config_fields
from auto_merger.config import Config
from tests.conftest import (
    get_config_dict_simple,
    get_config_dict_miss_approval_lifetime,
    default_config_merger,
    no_gitlab_repos_config,
)


@pytest.mark.parametrize(
    "config_dict,expected_bool",
    (
        (get_config_dict_simple, True),
        (get_config_dict_miss_approval_lifetime, True),
        (default_config_merger, True),
        (no_gitlab_repos_config, False),
    ),
)
def test_check_mandatory_fields_simple_config(config_dict, expected_bool):
    test_config = Config()
    ret_val = check_mandatory_config_fields(config=test_config.get_from_dict(config_dict()))
    assert ret_val == expected_bool
