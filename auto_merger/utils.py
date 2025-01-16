# MIT License
#
# Copyright (c) 2024 Red Hat, Inc.

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


logger = logging.getLogger("auto-merger")


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
    logger.debug(f"AutoMerger: Temporary dir name: {temp_file.name}")
    return temp_file.name

class AutoMergerFormatter(logging.Formatter):
    def __init__(
        self,
        fmt=None,
        datefmt=None,
        *args,
    ):
        fmt = (
            fmt
            or "%(name)s - %(levelname)s: %(message)s"
        )
        datefmt = datefmt or "%Y-%m-%d %H:%M:%S"
        super().__init__(fmt, datefmt, *args)


def setup_logger(level=logging.INFO, handler_class=logging.StreamHandler, handler_kwargs=None, datefmt: str = ""):
    logger = logging.getLogger("auto-merger")
    logger.setLevel(level)
    logger.debug(f"Logging set to {logging.getLevelName(level)}")

    # do not re-add handlers if they are already present
    if not [x for x in logger.handlers if isinstance(x, handler_class)]:
        # Debug handler
        handler_kwargs = handler_kwargs or {}
        handler = handler_class(**handler_kwargs)
        handler.setLevel(level)

        formatter = AutoMergerFormatter(None, datefmt=datefmt)
        handler.setFormatter(formatter)
        logger.addHandler(handler)


def check_mandatory_config_fields(config: Config) -> bool:
    config_correct: bool = True
    if "blocker_labels" not in config.github:
        logger.error("In github section is missing 'blocker_labels'")
        config_correct = False
    if "approval_labels" not in config.github:
        logger.error("In github section is missing 'approval_labels'")
        config_correct = False
    if "repos" not in config.github:
        logger.error("In github section is missing 'repos'. No repositories are specified.")
        config_correct = False
    if "namespace" not in config.github:
        logger.error("In github section is missing 'namespace'. are specified.")
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
