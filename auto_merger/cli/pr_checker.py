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
import click
import sys

from auto_merger.config import Config, pass_global_config
from auto_merger.exceptions import AutoMergerConfigException
from auto_merger.utils import check_mandatory_config_fields
from auto_merger import api

logger = logging.getLogger(__name__)


@click.command("pr-checker")
@click.option("--print-results", is_flag=True, help="Prints readable summary")
@click.option("--send-email", multiple=True, help="Specify email addresses to which the mail will be sent.")
@pass_global_config
def pr_checker(ctx, print_results, send_email):
    logger.debug(ctx.debug)
    try:
        c = Config.get_default_config()
        if not c:
            logger.error("Default config does not exist")
            sys.exit(10)
        if not check_mandatory_config_fields(c):
            logger.error("Yaml does not contain some mandatory fields. See output")
            sys.exit(2)
    except AutoMergerConfigException:
        sys.exit(10)
    ret_value = api.pull_request_checker(config=c, print_results=print_results, send_email=send_email)
    sys.exit(ret_value)

