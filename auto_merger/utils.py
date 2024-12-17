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
import sys
import os

from pathlib import Path
from contextlib import contextmanager

logger = logging.getLogger(__name__)


def run_command(
    cmd,
    return_output: bool = True,
    ignore_error: bool = False,
    shell: bool = True,
    debug: bool = False,
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


def setup_logger(logger_id, level=logging.DEBUG):
    logger = logging.getLogger(logger_id)
    logger.setLevel(level)
    format_str = "%(name)s - %(levelname)s: %(message)s"
    # Debug handler
    debug = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(format_str)
    debug.setLevel(logging.DEBUG)
    debug.addFilter(lambda r: True if r.levelno == logging.DEBUG else False)
    debug.setFormatter(formatter)
    logger.addHandler(debug)
    # Info handler
    info = logging.StreamHandler(sys.stdout)
    info.setLevel(logging.DEBUG)
    info.addFilter(lambda r: True if r.levelno == logging.INFO else False)
    logger.addHandler(info)
    # Warning, error, critical handler
    stderr = logging.StreamHandler(sys.stderr)
    formatter = logging.Formatter(format_str)
    stderr.setLevel(logging.WARN)
    stderr.addFilter(lambda r: True if r.levelno >= logging.WARN else False)
    stderr.setFormatter(formatter)
    logger.addHandler(stderr)
    return logger


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
