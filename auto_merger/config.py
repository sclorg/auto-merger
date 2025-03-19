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

from yaml import safe_load

from pathlib import Path

from auto_merger.exceptions import AutoMergerConfigException


logger = logging.getLogger("auto_merger.config")


class Config:
    def __init__(self):
        self.debug: bool = True
        self.github: dict = {}
        self.gitlab: dict = {}

    @classmethod
    def get_default_config(cls) -> "Config":
        config_file_name = Path.home() / ".auto-merger.yaml"
        logger.debug(f"Loading user config from directory: {config_file_name}")
        loaded_config: dict = {}
        if config_file_name.is_file():
            try:
                loaded_config = safe_load(open(config_file_name))
            except Exception as ex:
                logger.error(f"Cannot load user config '{config_file_name}'.")
                raise AutoMergerConfigException(f"Cannot load user config: {ex}.")
        return Config.get_from_dict(raw_dict=loaded_config)

    @classmethod
    def get_from_dict(cls, raw_dict: dict) -> "Config":
        config = Config()
        config.debug = raw_dict.get("debug", True)
        config.github = raw_dict.get("github", None)
        config.gitlab = raw_dict.get("gitlab", None)
        if config.github:
            if "approvals" not in config.github:
                config.github["approvals"] = 2
            if "pr_lifetime" not in config.github:
                config.github["pr_lifetime"] = 1
        return config

    def __repr__(self):
        return f"Config(debug={self.debug}, github={self.github}, " f"gitlab={self.gitlab})"


pass_config = click.make_pass_decorator(Config)
