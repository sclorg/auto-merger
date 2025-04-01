#!/usr/bin/env python3

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
import requests
import gitlab
import os

from requests.exceptions import HTTPError

from auto_merger.config import Config
from auto_merger.named_tuples import CurrentUser, ProjectMR

logger = logging.getLogger(__name__)

requests.packages.urllib3.disable_warnings()


class GitLabHandler:
    def __init__(self, config: Config):
        self.config = config
        if "namespace" in self.config.gitlab:
            self.namespace = self.config.gitlab["namespace"]
        else:
            self.namespace = None
        self._gitlab_api = None
        self.project_id: int = 0
        self.current_user: CurrentUser
        self.token = ""

    @property
    def gitlab_api(self):
        if not self._gitlab_api:
            self._gitlab_api = gitlab.Gitlab(
                self.config.gitlab["url"],
                private_token=self.token.strip(),
                ssl_verify=False,
            )
        return self._gitlab_api

    def check_authentication(self):
        self.token = os.getenv("GITLAB_TOKEN", None)
        if not self.token:
            logger.error("Environment variable GITLAB_TOKEN is not specified.")
            return False
        try:
            assert self.gitlab_api
            self.gitlab_api.auth()
            current_user = self.gitlab_api.user
            self.current_user = CurrentUser(current_user.id, current_user.username)
            return self.current_user
        except gitlab.exceptions.GitlabAuthenticationError as gae:
            logger.error(f"Authentication failed with reason {gae}.")
            return None

    def get_project_merge_requests(self, project_id) -> list[ProjectMR]:
        self.project = self.gitlab_api.projects.get(project_id)
        project_mr = self.project.mergerequests.list(state="opened")
        return [
            ProjectMR(
                x.iid,
                x.title,
                x.description,
                x.target_branch,
                x.author["username"],
                x.web_url,
                x.draft,
                x.state,
                x.reviewers,
                x.approvals_before_merge,
                x.labels,
                x.merge_status,
                x.detailed_merge_status,
            )
            for x in project_mr
            if x.state == "opened"
        ]

    def get_project_id_from_url(self, url: str, reponame: str) -> str:
        url = f"{url}/api/v4/projects"
        headers = {"Content-Type": "application/json", "PRIVATE-TOKEN": self.token}
        url = f"{url}/{reponame.replace('/', '%2F')}"
        logger.debug(f"Get project_id from {url}")
        ret = requests.get(url=f"{url}", headers=headers, verify=False)
        ret.raise_for_status()
        if ret.status_code != 200:
            logger.error(f"Getting project_id failed for reason {ret.reason} {ret.json()} ")
            raise HTTPError
        project_id = ret.json()["id"]
        logger.debug(f"Project id returned from {url} is {project_id}")
        return project_id
