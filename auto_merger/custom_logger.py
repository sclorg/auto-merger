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

import logging

from logging import Formatter

PREFIX = "\033["
SUFFIX = "\033[0m"


class ColoredFormatter(Formatter):
    grey = "\033[38m"
    yellow = "\033[33m"
    red = "\033[31m"
    bold_red = "\033[31;1m"
    reset = "\033[0m"
    green = "\033[91m"
    blue = "\033[34m"
    format_info = "%(message)s"
    format_debug = "%(levelname)s - %(name)s - %(message)s"

    FORMATS = {
        logging.DEBUG: blue + format_debug + reset,
        logging.INFO: green + format_info + reset,
        logging.WARNING: yellow + format_info + reset,
        logging.ERROR: red + format_debug + reset,
        logging.CRITICAL: bold_red + format_debug + reset,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def setup_logger(logger_name: str = "automerger", level=logging.INFO):
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    # Check if handlers already exist (to avoid duplicate logs)
    if not logger.handlers:
        # Create a console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(ColoredFormatter())

        # Create a file handler
        file_handler = logging.FileHandler("automerger.log")
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")
        file_handler.setFormatter(file_formatter)

        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

        logger.setLevel(logging.DEBUG)

    return logger
