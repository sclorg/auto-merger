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

from auto_merger.config import pass_global_config
from auto_merger import api

logger = logging.getLogger(__name__)


@click.command("pr-checker")
@click.option("--print-results", is_flag=True, help="Prints readable summary")
@click.option("--github-labels", required=True, multiple=True,
              help="Specify Git Hub labels to meet criteria")
@click.option("--blocking-labels", multiple=True,
              help="Specify Git Hub labels that blocks PR to merge")
@click.option("--send-email", multiple=True, help="Specify email addresses to which the mail will be sent.")
@click.option("--approvals",
              default=2, type=int,
              help="Specify number of approvals to automatically merge PR. Default 2")
@pass_global_config
def pr_checker(ctx, print_results, github_labels, blocking_labels, approvals, send_email):
    logger.debug(ctx.debug)
    ret_value = api.pr_checker(print_results, github_labels, blocking_labels, approvals, send_email)
    sys.exit(ret_value)

