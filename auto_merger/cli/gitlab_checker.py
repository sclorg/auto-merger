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

from auto_merger.config import pass_config
from auto_merger import api

logger = logging.getLogger("auto-merger")


@click.command("gitlab-checker")
@click.option(
    "--send-email",
    multiple=True,
    help="Specify email addresses to which the mail will be sent.",
)
@click.option(
    "--json-output",
    multiple=False,
    help="Save auto-merge outputs in json format. Default is current working directory.",
)
@pass_config
def gitlab_checker(config, send_email, json_output):
    ret_value = api.merge_request_checker(config=config, send_email=send_email, json_output=json_output)
    sys.exit(ret_value)
