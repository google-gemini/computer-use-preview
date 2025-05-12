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
import pytest
from unittest.mock import AsyncMock
from google.cloud import run_v2
from google.api_core.exceptions import NotFound
from config import Config
from models import SessionType, SignalingStrategy
from sessions import SessionManager


@pytest.fixture
def mock_config(mocker):
    """Fixture for a mocked Config object."""
    mock_cfg = mocker.MagicMock(spec=Config)
    mock_cfg.project_id = "test-project"
    mock_cfg.job_name = "projects/test-project/locations/us-east1/jobs/test-job"
    mock_cfg.job_image = "test/image:latest"
    mock_cfg.job_parent.return_value = "projects/test-project/locations/us-east1"
    mock_cfg.job_id.return_value = "test-job"
    return mock_cfg


@pytest.fixture
def mock_config_local(mock_config):
    """Fixture for Config that forces local (job_name=None) execution."""
    mock_config.job_name = None
    return mock_config


@pytest.fixture
def mock_run_client(mocker):
    """
    Mocks the run_v2.JobsAsyncClient,
    but ALLOWS REAL Job/Container/EnvVar objects to be used.
    """
    mock_operation = AsyncMock()
    mock_operation.done.return_value = True  # Make polling loop finish instantly
    mock_operation.result.return_value = AsyncMock()  # Return a mock result

    mock_client_instance = AsyncMock(spec=run_v2.JobsAsyncClient)
    mock_client_instance.get_job.return_value = run_v2.Job()
    mock_client_instance.update_job.return_value = mock_operation
    mock_client_instance.create_job.return_value = mock_operation

    mocker.patch("sessions.run_v2.JobsAsyncClient", return_value=mock_client_instance)
    mocker.patch("sessions.asyncio.sleep", return_value=None)

    return mock_client_instance


@pytest.fixture
def mock_popen(mocker):
    """Mocks subprocess.Popen"""
    return mocker.patch("sessions.subprocess.Popen")


def get_env_vars_as_dict(job: run_v2.Job):
    """Helper to extract EnvVars from a job for easier testing"""
    if not job.template.template.containers:
        return {}
    return {env.name: env.value for env in job.template.template.containers[0].env}


@pytest.mark.asyncio
async def test_start_worker_local_http(mock_config_local, mock_popen):
    """
    Tests that start_worker calls _create_local_worker which calls
    Popen with correct args for local HTTP.
    """
    manager = SessionManager(config=mock_config_local)

    await manager.start_worker(
        session_id="local-sess-http",
        session_type=SessionType.browser,
        signaling_strategy=SignalingStrategy.HTTP,
        screen_resolution="800x600",
        job_timeout_seconds=600,
        idle_timeout_seconds=60,
    )

    mock_popen.assert_called_once()
    args, _ = mock_popen.call_args

    # Check basic command
    assert args[0][0:5] == ["docker", "run", "--rm", "-it", "--name=local-sess-http"]
    assert args[0][-1] == "puppeteer-worker"

    # Check env vars passed as flags
    cmd_str = " ".join(args[0])
    assert "-e SESSION_ID=local-sess-http" in cmd_str
    assert "-e HEADFULCHROME=false" in cmd_str
    assert "-e FULLOS=false" in cmd_str
    assert f"-e PUBSUB_PROJECT_ID={mock_config_local.project_id}" in cmd_str
    assert "-e USE_PUBSUB=false" in cmd_str
    assert "-e SCREEN_RESOLUTION=800x600" in cmd_str
    assert "-e IDLE_TIMEOUT=60s" in cmd_str

    # Ensure PubSub Emulator flags are NOT present
    assert "PUBSUB_EMULATOR_HOST" not in cmd_str
    assert "--add-host=host.docker.internal:host-gateway" not in cmd_str


@pytest.mark.asyncio
async def test_start_worker_local_pubsub(mock_config_local, mock_popen):
    """
    Tests that start_worker calls _create_local_worker
    which calls Popen with correct args for local PUBSUB,
    including the emulator flags.
    """
    manager = SessionManager(config=mock_config_local)

    await manager.start_worker(
        session_id="local-sess-ps",
        session_type=SessionType.os,
        signaling_strategy=SignalingStrategy.PUBSUB,
        screen_resolution="800x600",
        job_timeout_seconds=600,
        idle_timeout_seconds=60,
    )

    mock_popen.assert_called_once()
    args, kwargs = mock_popen.call_args

    # Check basic command
    assert args[0][0:5] == ["docker", "run", "--rm", "-it", "--name=local-sess-ps"]
    assert args[0][-1] == "puppeteer-worker"  # Image name

    # Check env vars passed as flags
    cmd_str = " ".join(args[0])
    assert "-e SESSION_ID=local-sess-ps" in cmd_str
    assert "-e HEADFULCHROME=false" in cmd_str
    assert "-e FULLOS=true" in cmd_str
    assert "-e USE_PUBSUB=true" in cmd_str

    # Ensure PubSub Emulator flags ARE present
    assert "-e PUBSUB_EMULATOR_HOST=host.docker.internal:8085" in cmd_str
    assert "--add-host=host.docker.internal:host-gateway" in cmd_str


@pytest.mark.asyncio
async def test_start_worker_cloud_run_updates_job(mock_config, mock_run_client):
    """
    Tests that an existing Cloud Run Job is updated.
    """
    manager = SessionManager(config=mock_config)

    # Ensure the mock job returned by get_job has a container,
    # but with some dummy env vars, to test the replacement logic.
    mock_job_to_return = run_v2.Job()
    mock_job_to_return.template.template.containers.append(run_v2.Container())
    mock_job_to_return.template.template.containers[0].env.append(
        run_v2.EnvVar(name="OLD_VAR", value="OLD_VALUE")
    )
    mock_job_to_return.template.template.containers[0].env.append(
        run_v2.EnvVar(name="SESSION_ID", value="OLD_ID")
    )
    mock_run_client.get_job.return_value = mock_job_to_return

    # Act
    await manager.start_worker(
        session_id="cloud-sess-update",
        session_type=SessionType.browser,
        signaling_strategy=SignalingStrategy.PUBSUB,
        screen_resolution="1024x768",
        job_timeout_seconds=700,
        idle_timeout_seconds=70,
    )

    # Assert Correct API calls were made
    mock_run_client.get_job.assert_awaited_once()
    mock_run_client.update_job.assert_awaited_once()
    mock_run_client.create_job.assert_not_awaited()

    # Assert job passed to update_job has the right token
    args, kwargs = mock_run_client.update_job.call_args
    updated_job = kwargs["request"].job

    assert updated_job.start_execution_token == "cloud-sess-update"
    assert updated_job.template.template.timeout.seconds == 700
    assert updated_job.template.template.containers[0].image == "test/image:latest"

    env_dict = get_env_vars_as_dict(updated_job)

    assert env_dict.get("SESSION_ID") == "cloud-sess-update"
    assert env_dict.get("HEADFULCHROME") == "false"
    assert env_dict.get("FULLOS") == "false"
    assert env_dict.get("PUBSUB_PROJECT_ID") == "test-project"
    assert env_dict.get("USE_PUBSUB") == "true"
    assert env_dict.get("SCREEN_RESOLUTION") == "1024x768"
    assert env_dict.get("IDLE_TIMEOUT") == "70s"
    assert (
        "OLD_VAR" not in env_dict
    )  # Check old, non-colliding vars were removed by the code

    # Check Resources
    assert updated_job.template.template.containers[0].resources.limits == {
        "cpu": "2",
        "memory": "8G",
    }
    # Check Probe
    probe = updated_job.template.template.containers[0].startup_probe
    assert probe.failure_threshold == 180
    assert probe.http_get.path == "/ready"
    assert probe.period_seconds == 1


@pytest.mark.asyncio
async def test_start_worker_cloud_run_creates_job(mock_config, mock_run_client):
    """
    Tests that a new Cloud Run Job is created if GetJob raises NotFound.
    """
    # Arrange: Configure mock to raise NotFound
    mock_run_client.get_job.side_effect = NotFound("testing Not Found")

    manager = SessionManager(config=mock_config)

    # Act
    await manager.start_worker(
        session_id="cloud-sess-create",
        session_type=SessionType.headful,
        signaling_strategy=SignalingStrategy.HTTP,
        screen_resolution="1024x768x16",
        job_timeout_seconds=800,
        idle_timeout_seconds=80,
    )

    # Assert Correct API calls were made
    mock_run_client.get_job.assert_awaited_once()
    mock_run_client.create_job.assert_awaited_once()
    mock_run_client.update_job.assert_not_awaited()

    # Assert job passed to create_job has the right details
    args, kwargs = mock_run_client.create_job.call_args
    created_job = kwargs["request"].job
    parent = kwargs["request"].parent
    job_id = kwargs["request"].job_id

    assert parent == mock_config.job_parent()
    assert job_id == mock_config.job_id()

    assert created_job.start_execution_token == "cloud-sess-create"
    assert created_job.template.template.timeout.seconds == 800
    assert len(created_job.template.template.containers) == 1
    assert created_job.template.template.containers[0].image == "test/image:latest"

    env_dict = get_env_vars_as_dict(created_job)

    assert env_dict.get("SESSION_ID") == "cloud-sess-create"
    assert env_dict.get("HEADFULCHROME") == "true"
    assert env_dict.get("FULLOS") == "false"
    assert env_dict.get("USE_PUBSUB") == "false"
    assert env_dict.get("IDLE_TIMEOUT") == "80s"
    assert env_dict.get("SCREEN_RESOLUTION") == "1024x768x16"


def test_internal_env_vars(mock_config):
    """Directly test the _env_vars helper"""
    manager = SessionManager(config=mock_config)

    envs = manager._env_vars(
        session_id="s1",
        session_type=SessionType.os,
        signaling_strategy=SignalingStrategy.PUBSUB,
        screen_resolution="1x1",
        idle_timeout_seconds=5,
    )

    expected = [
        ("SESSION_ID", "s1"),
        ("HEADFULCHROME", "false"),
        ("FULLOS", "true"),
        ("PUBSUB_PROJECT_ID", "test-project"),
        ("USE_PUBSUB", "true"),
        ("SCREEN_RESOLUTION", "1x1"),
        ("IDLE_TIMEOUT", "5s"),
    ]
    assert envs == expected


def test_internal_docker_env_flags(mock_config):
    """Directly test the _docker_env_flags helper"""
    manager = SessionManager(config=mock_config)
    flags = manager._docker_env_flags([("A", "val_a"), ("B", "val_b")])
    assert flags == ["-e", "A=val_a", "-e", "B=val_b"]
