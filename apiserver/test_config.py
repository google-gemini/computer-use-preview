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
import unittest
from unittest.mock import patch
from config import Config


class TestConfig(unittest.TestCase):

    def test_defaults(self):
        config = Config()
        self.assertFalse(config.use_pubsub)
        self.assertEqual(
            config.job_image,
            "us-east1-docker.pkg.dev/mattrobertsonfb/computer-use/puppeteer:latest",
        )
        self.assertEqual(config.cmd_timeout, 10)
        self.assertEqual(config.project_id, "")
        self.assertEqual(config.job_name, None)

    @patch.dict(
        os.environ,
        {
            "USE_PUBSUB": "true",
            "GOOGLE_CLOUD_PROJECT": "someproj",
            "JOB_NAME": "projects/differentproj/locations/us-east1/jobs/computer-use-job",
            "CMD_TIMEOUT": "123",
            "JOB_IMAGE": "gcr.io/banana/fofanana:latest",
        },
    )
    def test_env_var_overrides(self):
        config = Config()
        self.assertTrue(config.use_pubsub)
        self.assertEqual(config.job_image, "gcr.io/banana/fofanana:latest")
        self.assertEqual(config.cmd_timeout, 123)
        self.assertEqual(config.project_id, "someproj")
        self.assertEqual(
            config.job_name,
            "projects/differentproj/locations/us-east1/jobs/computer-use-job",
        )

    @patch.dict(
        os.environ,
        {
            "GOOGLE_CLOUD_PROJECT": "myproj",
            "JOB_NAME": "projects/myproj/locations/us-east1/jobs/computer-use-job",
        },
    )
    def test_job_parent(self):
        config = Config()
        self.assertEqual(config.job_parent(), "projects/myproj/locations/us-east1")

    @patch.dict(
        os.environ,
        {
            "GOOGLE_CLOUD_PROJECT": "myproj",
            "JOB_NAME": "projects/myproj/locations/us-east1/jobs/computer-use-job",
        },
    )
    def test_job_id(self):
        config = Config()
        self.assertEqual(config.job_id(), "computer-use-job")


if __name__ == "__main__":
    unittest.main()
