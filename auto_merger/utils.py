# MIT License
#
# Copyright (c) 2024 Red Hat, Inc.
import json

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

import subprocess
import logging
import tempfile
import os

from pathlib import Path
from contextlib import contextmanager

from auto_merger.config import Config


logger = logging.getLogger(__name__)


def run_command(
    cmd,
    return_output: bool = True,
    ignore_error: bool = False,
    shell: bool = True,
    **kwargs,
):
    """
    Run provided command on host system using the same user as invoked this code.
    Raises subprocess.CalledProcessError if it fails.
    :param cmd: list or str
    :param return_output: bool, return output of the command
    :param ignore_error: bool, do not fail in case nonzero return code
    :param shell: bool, run command in shell
    :param debug: bool, print command in shell, default is suppressed
    :return: None or str
    """
    logger.debug(f"command: {cmd}")
    try:
        if return_output:
            return subprocess.check_output(
                cmd,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                shell=shell,
                **kwargs,
            )
        else:
            return subprocess.check_call(cmd, shell=shell, **kwargs)
    except subprocess.CalledProcessError as cpe:
        if ignore_error:
            if return_output:
                return cpe.output
            else:
                return cpe.returncode
        else:
            logger.error(f"failed with code {cpe.returncode} and output:\n{cpe.output}")
            raise cpe


def temporary_dir(prefix: str = "automerger") -> str:
    temp_file = tempfile.TemporaryDirectory(prefix=prefix)
    logger.debug(f"Temporary dir name: {temp_file.name}")
    return temp_file.name


def check_mandatory_config_fields(config: Config) -> bool:
    config_correct: bool = True
    if config.github:
        if "blocker_labels" not in config.github:
            logger.error("In github section is missing 'blocker_labels'")
            config_correct = False
        if "approval_labels" not in config.github:
            logger.error("In github section is missing 'approval_labels'")
            config_correct = False
        if "repos" not in config.github:
            logger.error("In github section is missing 'repos'. No repositories are specified.")
            config_correct = False
    if config.gitlab:
        if "blocker_labels" not in config.gitlab:
            logger.error("In gitlab section is missing 'blocker_labels'")
            config_correct = False
        if "approval_labels" not in config.gitlab:
            logger.error("In gitlab section is missing 'approval_labels'")
            config_correct = False
        if "repos" not in config.gitlab:
            logger.error("In gitlab section is missing 'repos'. No repositories are specified.")
            config_correct = False
    return config_correct


@contextmanager
def cwd(path):
    """
    Switch to Path directory and once action is done
    returns back
    :param path:
    :return:
    """
    prev_cwd = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev_cwd)


def get_realtime():
    from datetime import datetime

    return datetime.now()


def return_full_path(json_file_path: str = "") -> Path:
    return Path(os.path.abspath(json_file_path))


def check_json_path(json_file_path: str = "") -> bool:
    json_file_path = return_full_path(json_file_path=json_file_path)
    if not json_file_path.parent.is_dir():
        logger.error(f"The specified parent dir does not exist: {json_file_path.parent}.")
        logger.error("Specify proper file path in --json-output argument.")
        return False
    return True


def save_json_file(json_file_path: str = "", json_dict=None) -> bool:
    if json_dict is None:
        json_dict = {}
    full_path = return_full_path(json_file_path=json_file_path)
    logger.debug(f"Checking json file {full_path}")
    new_dict = {}
    for data in json_dict:
        if not json_dict[data]:
            continue
        new_dict[data] = json_dict[data]
    with open(full_path, "w") as f:
        json.dump(new_dict, f, indent=2)
        logger.warning(f"The auto-merge results were stored to {full_path}")
    return True
