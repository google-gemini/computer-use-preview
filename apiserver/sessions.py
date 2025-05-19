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
import asyncio
import logging
from google.cloud import run_v2
from google.api_core.exceptions import NotFound
import subprocess
from typing import List, Tuple
from models import SessionType, SignalingStrategy
from config import Config


class SessionManager:

    config: Config

    def __init__(self, config: Config) -> None:
        """
        Initializes the SessionManager.

        Args:
            config (Config): The Config object.
        """
        self.config = config

    async def start_worker(
        self,
        session_id: str,
        session_type: SessionType,
        signaling_strategy: SignalingStrategy,
        screen_resolution: str,
        job_timeout_seconds: int,
        idle_timeout_seconds: int,
    ) -> None:
        if self.config.job_name is not None:
            await self._execute_cloud_run_job(
                session_id=session_id,
                session_type=session_type,
                signaling_strategy=signaling_strategy,
                screen_resolution=screen_resolution,
                job_timeout_seconds=job_timeout_seconds,
                idle_timeout_seconds=idle_timeout_seconds,
            )
        else:
            self._create_local_worker(
                session_id=session_id,
                session_type=session_type,
                signaling_strategy=signaling_strategy,
                screen_resolution=screen_resolution,
                idle_timeout_seconds=idle_timeout_seconds,
            )

    def _create_local_worker(
        self,
        session_id: str,
        session_type: SessionType,
        signaling_strategy: SignalingStrategy,
        screen_resolution: str,
        idle_timeout_seconds: int,
    ) -> None:
        logging.info("Creating local process worker")
        extra_flags = self._docker_env_flags(
            self._env_vars(
                session_id,
                session_type,
                signaling_strategy,
                screen_resolution,
                idle_timeout_seconds,
            )
        )

        if signaling_strategy == SignalingStrategy.PUBSUB:
            extra_flags = extra_flags + [
                "-e",
                "PUBSUB_EMULATOR_HOST=host.docker.internal:8085",
            ]
            extra_flags.append("--add-host=host.docker.internal:host-gateway")

        subprocess.Popen(
            ["docker", "run", "--rm", "-it", f"--name={session_id}"]
            + extra_flags
            + ["puppeteer-worker"]
        )

    async def _execute_cloud_run_job(
        self,
        session_id: str,
        session_type: SessionType,
        signaling_strategy: SignalingStrategy,
        screen_resolution: str,
        job_timeout_seconds: int,
        idle_timeout_seconds: int,
    ) -> None:
        logging.info(f"Creating job worker {self.config.job_name}")
        client = run_v2.JobsAsyncClient()
        try:
            # Fetch the current job:
            get_job_request = run_v2.GetJobRequest(
                name=self.config.job_name,
            )
            job = await client.get_job(request=get_job_request)
            job = self._configure_job(
                job=job,
                session_id=session_id,
                session_type=session_type,
                signaling_strategy=signaling_strategy,
                screen_resolution=screen_resolution,
                job_timeout_seconds=job_timeout_seconds,
                idle_timeout_seconds=idle_timeout_seconds,
            )

            # Send the request to the Cloud Run control plane:
            request = run_v2.UpdateJobRequest(
                job=job,
            )
            operation = await client.update_job(request=request)
            response = await operation.result()
            logging.info(response.latest_created_execution)
        except NotFound:
            logging.info("Job does not exist, creating it...")
            job = self._configure_job(
                job=run_v2.Job(),
                session_id=session_id,
                session_type=session_type,
                signaling_strategy=signaling_strategy,
                screen_resolution=screen_resolution,
                job_timeout_seconds=job_timeout_seconds,
                idle_timeout_seconds=idle_timeout_seconds,
            )

            request = run_v2.CreateJobRequest(
                job=job, parent=self.config.job_parent(), job_id=self.config.job_id()
            )
            operation = await client.create_job(request=request)
            response = await operation.result()
            logging.info(response.latest_created_execution)

    def _configure_job(
        self,
        job: run_v2.Job,
        session_id: str,
        session_type: SessionType,
        signaling_strategy: SignalingStrategy,
        screen_resolution: str,
        job_timeout_seconds: int,
        idle_timeout_seconds: int,
    ) -> run_v2.Job:
        # Add a start_execution_token so the job will execute when we create/update it.
        job.start_execution_token = session_id
        job.template.template.max_retries = 1
        job.template.template.timeout = {
            "seconds": job_timeout_seconds,
        }

        # If we are creating the Job we need to add a container.
        if len(job.template.template.containers) < 1:
            job.template.template.containers.append(run_v2.Container())

        # Always set the image in case there is a new one.
        job.template.template.containers[0].image = self.config.job_image

        # Set the environment variables.
        env_vars = self._env_vars(
            session_id,
            session_type,
            signaling_strategy,
            screen_resolution,
            idle_timeout_seconds,
        )
        keys = set(map(lambda x: x[0], env_vars))
        # Clear the entire env list.
        job.template.template.containers[0].env = []
        for env in env_vars:
            job.template.template.containers[0].env.append(
                run_v2.EnvVar(
                    name=env[0],
                    value=env[1],
                )
            )

        # Bump up the available CPU and Memory
        job.template.template.containers[0].resources = run_v2.ResourceRequirements()
        job.template.template.containers[0].resources.limits = {
            "cpu": "2",
            "memory": "8G",
        }

        # Add startup probe
        job.template.template.containers[0].startup_probe = run_v2.Probe(
            initial_delay_seconds=0,
            period_seconds=1,
            timeout_seconds=1,
            failure_threshold=180,
            http_get=run_v2.HTTPGetAction(path="/ready", port=8000),
        )

        return job

    def _env_vars(
        self,
        session_id: str,
        session_type: SessionType,
        signaling_strategy: SignalingStrategy,
        screen_resolution: str,
        idle_timeout_seconds: int,
    ) -> List[Tuple[str, str]]:
        env_vars = [("SESSION_ID", session_id)]
        env_vars.append(
            ("HEADFULCHROME", str(session_type == SessionType.headful).lower())
        )
        env_vars.append(("FULLOS", str(session_type == SessionType.os).lower()))
        env_vars.append(("PUBSUB_PROJECT_ID", self.config.project_id))
        env_vars.append(
            ("USE_PUBSUB", str(signaling_strategy == SignalingStrategy.PUBSUB).lower())
        )
        env_vars.append(("SCREEN_RESOLUTION", screen_resolution))
        env_vars.append(("IDLE_TIMEOUT", f"{idle_timeout_seconds}s"))
        return env_vars

    def _docker_env_flags(self, env_vars: List[Tuple[str, str]]) -> List[str]:
        flags = []
        for env in env_vars:
            flags.append("-e")
            flags.append(f"{env[0]}={env[1]}")
        return flags
