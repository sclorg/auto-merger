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
import yaml
import os
import click
import requests

from yaml import safe_load

from pathlib import Path
from typing import Dict

from urllib3.exceptions import InsecureRequestWarning

from auto_merger.exceptions import AutoMergerConfigException, AutoMergerNetworkException
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)


logger = logging.getLogger(__name__)


class GlobalConfig(object):
    def __init__(self, debug: bool = False, work_dir: Path = Path("/tmp/auto-merger")):
        self.debug = debug
        self.work_dir = work_dir


pass_global_config = click.make_pass_decorator(GlobalConfig)


class Config:

    def __init__(self):
        self.debug: bool = True
        self.github: Dict = {}
        self.gitlab: Dict = {}

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
        logger.debug(str(config))
        return config

    @classmethod
    def get_user_config(cls, url: str):
        config = cls.download_config(url=url)
        return cls.get_from_dict(config)

    @classmethod
    def download_config(cls, url: str) -> Dict:
        """
        Loads Config from URL in raw format
        :param url: URL to config file in raw format
        :return:
        """
        # Requests have no file:// support
        file_protocol = 'file://'
        if url.startswith(file_protocol):
            try:
                with open(url[len(file_protocol):]) as f:
                    return yaml.safe_load(f.read())
            except IOError as error:
                logger.error(error)
                raise AutoMergerNetworkException
        try:
            result = requests.get(url, verify=False)
            result.raise_for_status()
            if result.status_code == 200:
                return yaml.safe_load(result.text)
        except requests.exceptions.MissingSchema as rms:
            logger.error(rms)
            raise AutoMergerNetworkException
        return {}

    def __repr__(self):
        return f"Config(debug={self.debug}, github={self.github}, " \
               f"gitlab={self.gitlab})"
