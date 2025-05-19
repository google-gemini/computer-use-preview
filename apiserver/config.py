# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import os
import urllib.request
import logging
from typing import Any, Callable


class Config:

    on_cloud_run: bool
    job_name: str | None
    job_image: str
    cmd_timeout: int
    project_id: str
    use_pubsub: bool
    api_key: str | None

    def __init__(self):
        # If we are running as Cloud Run service, the K_SERVICE env var will be set:
        # https://cloud.google.com/run/docs/container-contract#services-env-vars
        self.on_cloud_run = os.environ.get("K_SERVICE") != None
        self.use_pubsub = (
            os.environ.get("USE_PUBSUB", str(self.on_cloud_run)).lower() == "true"
        )
        self.job_image = os.environ.get(
            "JOB_IMAGE",
            "us-docker.pkg.dev/cloudrun/solutions/computer-use/puppeteer:latest",
        )
        self.cmd_timeout = int(os.environ.get("CMD_TIMEOUT", "10"))
        self.project_id = Config._get_project_id(self.on_cloud_run)
        self.job_name = Config._get_job_name(
            on_cloud_run=self.on_cloud_run, project_id=self.project_id
        )
        self.api_key = os.environ.get("API_KEY")

    def job_parent(self) -> str:
        return self.job_name.split("/jobs/")[0]

    def job_id(self) -> str:
        return self.job_name.split("/jobs/")[1]

    @staticmethod
    def _get_project_id(on_cloud_run: bool) -> str:
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "")
        if project_id == "" and on_cloud_run:
            metadata_server_url = (
                "http://metadata.google.internal/computeMetadata/v1/project/project-id"
            )
            headers = {"Metadata-Flavor": "Google"}

            req = urllib.request.Request(metadata_server_url, headers=headers)
            try:
                with urllib.request.urlopen(req) as response:
                    project_id = response.read().decode("utf-8")
                    logging.info(f"Fetched the project ID: {project_id}")
            except urllib.error.URLError as e:
                logging.error(f"Error fetching project ID from metadata server: {e}")
        return project_id

    @staticmethod
    def _get_job_name(on_cloud_run: bool, project_id: str) -> str:
        job_name = os.environ.get("JOB_NAME")
        if job_name is not None or not on_cloud_run:
            return job_name
        metadata_server_url = (
            "http://metadata.google.internal/computeMetadata/v1/instance/region"
        )
        headers = {"Metadata-Flavor": "Google"}
        req = urllib.request.Request(metadata_server_url, headers=headers)
        try:
            with urllib.request.urlopen(req) as response:
                region = response.read().decode("utf-8").split("/regions/")[1]
                logging.info(f"Fetched the region: {region}")
                return f"projects/{project_id}/locations/{region}/jobs/computer-use-job"
        except urllib.error.URLError as e:
            logging.error(f"Error fetching region from metadata server: {e}")
            return ""
