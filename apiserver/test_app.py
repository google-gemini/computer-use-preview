# test_app.py

import pytest
from fastapi import status, Request
from unittest.mock import patch, MagicMock, AsyncMock
import uuid
import asyncio
import json
import app as fastapiapp

from models import (
    Message,
    SignalingStrategy,
    SessionType,
)
from commands import (
    TypeTextAt,
    Navigate,
    TypeTextAtArgs,
    NavigateArgs,
)
from config import Config as AppConfig  # Alias to avoid conflict with pytest's 'config'
from app import get_command_timeout


API_KEY_HEADER_NAME_FOR_TESTS = "X-API-Key"

FIXED_TEST_UUID_SESSION = "123e4567-e89b-12d3-a456-426614174000"
FIXED_TEST_UUID_COMMAND = "baadf00d-e89b-12d3-a456-426614174001"


@pytest.fixture(scope="module")
def app_module():
    """Fixture to import the app module. Allows setting API_KEY_HEADER_NAME_FOR_TESTS."""
    global API_KEY_HEADER_NAME_FOR_TESTS
    API_KEY_HEADER_NAME_FOR_TESTS = fastapiapp.API_KEY_HEADER_NAME
    return fastapiapp


@pytest.fixture
def mock_config_instance():
    """Provides a mock Config instance."""
    mc = MagicMock(spec=AppConfig)
    mc.api_key = None
    mc.use_pubsub = False
    mc.project_id = "test-project"
    mc.cmd_timeout = 10
    mc.job_name = None
    mc.job_image = "test-image"
    mc.on_cloud_run = False
    return mc


@pytest.fixture
def mock_session_manager_instance():
    """Provides a mock SessionManager instance."""
    msm = MagicMock()
    msm.start_worker = AsyncMock()
    return msm


@pytest.fixture
def mock_pubsub_manager_instance():
    """Provides a mock PubSubManager instance."""
    mpsm = AsyncMock()
    mpsm.start = AsyncMock()
    mpsm.shutdown = AsyncMock()
    mpsm.start_session = MagicMock()
    mpsm.end_session = MagicMock()
    mpsm.publish_message = AsyncMock()
    mpsm.stream_screenshots = MagicMock(return_value=iter([]))
    mpsm.pending_messages = {}
    return mpsm


@pytest.fixture
def client(
    app_module,
    mock_config_instance,
    mock_session_manager_instance,
    mock_pubsub_manager_instance,
):
    """
    Provides a TestClient for the FastAPI application with mocked dependencies.
    Handles lifespan events by ensuring mocks for start/shutdown are called.
    """
    with patch.object(app_module, "config", mock_config_instance), patch.object(
        app_module, "session_manager", mock_session_manager_instance
    ), patch.object(app_module, "pubsub_manager", mock_pubsub_manager_instance):

        mock_pubsub_manager_instance.start.reset_mock()
        mock_pubsub_manager_instance.shutdown.reset_mock()

        from fastapi.testclient import (
            TestClient as FastAPIClient,
        )

        test_app_instance = app_module.app

        with FastAPIClient(test_app_instance) as c:
            yield c

        mock_pubsub_manager_instance.start.assert_awaited_once()
        mock_pubsub_manager_instance.shutdown.assert_awaited_once()


def test_get_command_timeout_standard_command():
    command = Navigate(name="navigate", args=NavigateArgs(url="http://example.com"))
    base_timeout = 10
    key_delay = 0.1
    timeout = get_command_timeout(command, base_timeout, key_delay)
    assert timeout == base_timeout


def test_get_command_timeout_type_text_at_command():
    text = "hello"
    command = TypeTextAt(name="type_text_at", args=TypeTextAtArgs(y=0, x=0, text=text))
    base_timeout = 10
    key_delay = 0.1
    expected_timeout = base_timeout + (len(text) * key_delay)
    timeout = get_command_timeout(command, base_timeout, key_delay)
    assert timeout == expected_timeout


def test_get_command_timeout_type_text_at_command_zero_delay():
    text = "world"
    command = TypeTextAt(name="type_text_at", args=TypeTextAtArgs(y=0, x=0, text=text))
    base_timeout = 20
    key_delay = 0.0
    expected_timeout = base_timeout
    timeout = get_command_timeout(command, base_timeout, key_delay)
    assert timeout == expected_timeout


def test_api_key_not_configured_allows_access(
    client,
    mock_config_instance,
    mock_session_manager_instance,
    mock_pubsub_manager_instance,
):
    mock_config_instance.api_key = None

    mock_uuid_obj = uuid.UUID(FIXED_TEST_UUID_SESSION)
    with patch("uuid.uuid4", return_value=mock_uuid_obj):
        response = client.post(
            "/sessions",
            json={
                "type": "browser",
                "screen_resolution": "1000x1000",
                "timeout_seconds": 60,
                "idle_timeout_seconds": 30,
            },
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["id"] == FIXED_TEST_UUID_SESSION
        mock_pubsub_manager_instance.start_session.assert_called_once_with(
            session_id=FIXED_TEST_UUID_SESSION
        )
        mock_session_manager_instance.start_worker.assert_awaited_once()


def test_api_key_configured_blocks_if_no_key_provided(client, mock_config_instance):
    mock_config_instance.api_key = "supersecretkey"
    response = client.post("/sessions", json={"type": "browser"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert API_KEY_HEADER_NAME_FOR_TESTS in response.json()["detail"]


def test_api_key_configured_blocks_if_incorrect_key_provided(
    client, mock_config_instance
):
    mock_config_instance.api_key = "supersecretkey"
    headers = {API_KEY_HEADER_NAME_FOR_TESTS: "wrongkey"}
    response = client.post("/sessions", json={"type": "browser"}, headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Invalid API Key" in response.json()["detail"]


def test_api_key_configured_allows_access_if_correct_key_provided(
    client,
    mock_config_instance,
    mock_session_manager_instance,
    mock_pubsub_manager_instance,
):
    mock_config_instance.api_key = "supersecretkey"
    headers = {API_KEY_HEADER_NAME_FOR_TESTS: "supersecretkey"}

    mock_uuid_obj = uuid.UUID(FIXED_TEST_UUID_SESSION)
    with patch("uuid.uuid4", return_value=mock_uuid_obj):
        response = client.post(
            "/sessions",
            json={
                "type": "browser",
                "screen_resolution": "1000x1000",
                "timeout_seconds": 60,
                "idle_timeout_seconds": 30,
            },
            headers=headers,
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["id"] == FIXED_TEST_UUID_SESSION
        mock_pubsub_manager_instance.start_session.assert_called_once_with(
            session_id=FIXED_TEST_UUID_SESSION
        )
        mock_session_manager_instance.start_worker.assert_awaited_once()


def test_create_session_success(
    app_module,
    client,
    mock_config_instance,
    mock_session_manager_instance,
    mock_pubsub_manager_instance,
):
    request_data = {
        "type": "headful",
        "screen_resolution": "1920x1080",
        "timeout_seconds": 7200,
        "idle_timeout_seconds": 1200,
    }
    mock_config_instance.use_pubsub = True
    expected_signaling_strategy = SignalingStrategy.PUBSUB

    mock_uuid_obj = uuid.UUID(FIXED_TEST_UUID_SESSION)
    with patch("uuid.uuid4", return_value=mock_uuid_obj), patch.object(
        app_module, "signaling_strategy", expected_signaling_strategy
    ):
        response = client.post("/sessions", json=request_data)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["id"] == FIXED_TEST_UUID_SESSION

        mock_pubsub_manager_instance.start_session.assert_called_once_with(
            session_id=FIXED_TEST_UUID_SESSION
        )
        mock_session_manager_instance.start_worker.assert_awaited_once_with(
            session_id=FIXED_TEST_UUID_SESSION,
            session_type=SessionType(request_data["type"]),
            signaling_strategy=expected_signaling_strategy,
            screen_resolution=request_data["screen_resolution"],
            job_timeout_seconds=request_data["timeout_seconds"],
            idle_timeout_seconds=request_data["idle_timeout_seconds"],
        )


def test_create_session_start_worker_fails(
    client, mock_session_manager_instance, mock_pubsub_manager_instance
):
    request_data = {"type": "os"}
    mock_session_manager_instance.start_worker.side_effect = Exception(
        "Worker init explosion"
    )

    mock_uuid_obj = uuid.UUID(FIXED_TEST_UUID_SESSION)
    with patch("uuid.uuid4", return_value=mock_uuid_obj):
        response = client.post("/sessions", json=request_data)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Worker init explosion" in response.json()["detail"]
        mock_pubsub_manager_instance.start_session.assert_called_once_with(
            session_id=FIXED_TEST_UUID_SESSION
        )
        mock_session_manager_instance.start_worker.assert_awaited_once()


def test_create_session_pubsub_start_session_fails(
    client, mock_pubsub_manager_instance
):
    request_data = {"type": "browser"}
    mock_pubsub_manager_instance.start_session.side_effect = Exception(
        "PubSub broker unavailable"
    )

    mock_uuid_obj = uuid.UUID(FIXED_TEST_UUID_SESSION)
    with patch("uuid.uuid4", return_value=mock_uuid_obj):
        response = client.post("/sessions", json=request_data)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "PubSub broker unavailable" in response.json()["detail"]
        mock_pubsub_manager_instance.start_session.assert_called_once_with(
            session_id=FIXED_TEST_UUID_SESSION
        )


# Test GET /sessions/{session_id}/screenshots
def test_get_screenshot_stream(client, mock_pubsub_manager_instance):
    session_id = "live-stream-session"

    mock_stream_data = [
        "event: screenshot\ndata: image_data_1\n\n",
        "event: screenshot\ndata: image_data_2\n\n",
    ]
    mock_pubsub_manager_instance.stream_screenshots.return_value = iter(
        mock_stream_data
    )

    response = client.get(f"/sessions/{session_id}/screenshots")

    assert response.status_code == status.HTTP_200_OK
    assert response.headers["content-type"].startswith("text/event-stream")

    content = response.text
    expected_content = "".join(mock_stream_data)
    assert content == expected_content

    mock_pubsub_manager_instance.stream_screenshots.assert_called_once()
    args, _ = mock_pubsub_manager_instance.stream_screenshots.call_args
    assert args[0] == session_id
    assert isinstance(args[1], Request)


# Test POST /sessions/{session_id}/commands
@pytest.fixture
def mock_message_instance_for_command():
    msg_mock = AsyncMock(spec=Message)
    msg_mock.id = str(uuid.UUID(FIXED_TEST_UUID_COMMAND))
    msg_mock.get_screenshot = AsyncMock(return_value="base64_encoded_image_data")
    msg_mock.get_url = AsyncMock(return_value="https://example.com/currentpage")
    msg_mock.json = MagicMock(
        return_value=json.dumps({"id": msg_mock.id, "command": {"name": "test"}})
    )
    return msg_mock


def test_create_command_success(
    client,
    mock_config_instance,
    mock_pubsub_manager_instance,
    mock_message_instance_for_command,
):
    session_id = "active-session-for-commands"
    command_payload_for_request = {
        "name": "navigate",
        "args": {"url": "https://new.example.com"},
    }
    expected_message_data = command_payload_for_request
    expected_command_obj_for_timeout_func = Navigate(
        name="navigate", args=NavigateArgs(url="https://new.example.com")
    )

    with patch(
        "app.Message", return_value=mock_message_instance_for_command
    ) as MockedMessageClass, patch(
        "app.get_command_timeout", return_value=mock_config_instance.cmd_timeout
    ) as mock_get_timeout_func:

        response = client.post(
            f"/sessions/{session_id}/commands", json=command_payload_for_request
        )
        assert response.status_code == status.HTTP_200_OK
        json_response = response.json()
        assert json_response["id"] == mock_message_instance_for_command.id
        assert json_response["screenshot"] == "base64_encoded_image_data"
        assert json_response["url"] == "https://example.com/currentpage"

        MockedMessageClass.assert_called_once_with(
            type="command", data=expected_message_data
        )

        mock_get_timeout_func.assert_called_once()
        # create_command_request.root will be the Navigate instance
        assert (
            mock_get_timeout_func.call_args[1]["command"].model_dump()
            == expected_command_obj_for_timeout_func.model_dump()
        )
        assert (
            mock_get_timeout_func.call_args[1]["base_timeout"]
            == mock_config_instance.cmd_timeout
        )

        mock_pubsub_manager_instance.publish_message.assert_awaited_once_with(
            session_id=session_id,
            message=mock_message_instance_for_command,
            timeout=mock_config_instance.cmd_timeout,
        )
        mock_message_instance_for_command.get_screenshot.assert_awaited_once_with(
            timeout=mock_config_instance.cmd_timeout
        )
        mock_message_instance_for_command.get_url.assert_awaited_once()


def test_create_command_timeout_on_get_screenshot(
    client,
    mock_config_instance,
    mock_pubsub_manager_instance,
    mock_message_instance_for_command,
):
    session_id = "timeout-cmd-session"
    command_payload_for_request = {"name": "wait_5_seconds"}
    expected_message_data = {
        "name": "wait_5_seconds",
        "args": None,
    }

    mock_message_instance_for_command.get_screenshot.side_effect = asyncio.TimeoutError(
        "Screenshot retrieval timed out"
    )

    with patch(
        "app.Message", return_value=mock_message_instance_for_command
    ) as MockedMessageClass, patch(
        "app.get_command_timeout", return_value=mock_config_instance.cmd_timeout
    ):

        response = client.post(
            f"/sessions/{session_id}/commands", json=command_payload_for_request
        )
        assert response.status_code == status.HTTP_408_REQUEST_TIMEOUT
        assert "command timed out" in response.json()["detail"]
        MockedMessageClass.assert_called_once_with(
            type="command", data=expected_message_data
        )
        mock_pubsub_manager_instance.publish_message.assert_awaited_once()
        mock_message_instance_for_command.get_screenshot.assert_awaited_once()


def test_create_command_screenshot_is_none(
    client,
    mock_config_instance,
    mock_pubsub_manager_instance,
    mock_message_instance_for_command,
):
    session_id = "none-screenshot-cmd-session"
    command_payload_for_request = {"name": "screenshot"}
    expected_message_data = {"name": "screenshot", "args": None}

    mock_message_instance_for_command.get_screenshot.return_value = None
    mock_message_instance_for_command.get_url.return_value = "http://still-a-url.com"

    with patch(
        "app.Message", return_value=mock_message_instance_for_command
    ) as MockedMessageClass, patch(
        "app.get_command_timeout", return_value=mock_config_instance.cmd_timeout
    ):

        response = client.post(
            f"/sessions/{session_id}/commands", json=command_payload_for_request
        )
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "command failed" in response.json()["detail"]
        MockedMessageClass.assert_called_once_with(
            type="command", data=expected_message_data
        )
        mock_message_instance_for_command.get_screenshot.assert_awaited_once()


def test_create_command_publish_message_fails(
    client,
    mock_config_instance,
    mock_pubsub_manager_instance,
    mock_message_instance_for_command,
):
    session_id = "publish-fail-cmd-session"
    command_payload_for_request = {"name": "go_back"}
    expected_message_data = {"name": "go_back", "args": None}

    expected_exception_message = "Failed to send to PubSub"
    mock_pubsub_manager_instance.publish_message.side_effect = Exception(
        expected_exception_message
    )

    with patch(
        "app.Message", return_value=mock_message_instance_for_command
    ) as MockedMessageClass, patch(
        "app.get_command_timeout", return_value=mock_config_instance.cmd_timeout
    ), pytest.raises(
        Exception, match=expected_exception_message
    ):

        client.post(
            f"/sessions/{session_id}/commands", json=command_payload_for_request
        )

    MockedMessageClass.assert_called_once_with(
        type="command", data=expected_message_data
    )
    mock_pubsub_manager_instance.publish_message.assert_awaited_once()


# Test DELETE /sessions/{session_id}
def test_delete_session_success(
    client, mock_config_instance, mock_pubsub_manager_instance
):
    session_id = "terminating-session-id"

    with patch("app.Message") as MockedMessageClass:
        mock_internal_message = MagicMock(spec=Message)
        mock_internal_message.id = "shutdown-message-id"
        MockedMessageClass.return_value = mock_internal_message

        response = client.delete(f"/sessions/{session_id}")

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["id"] == session_id

        MockedMessageClass.assert_called_once_with(
            type="command", data={"name": "shutdown", "args": None}
        )

        mock_pubsub_manager_instance.publish_message.assert_awaited_once_with(
            session_id=session_id,
            message=mock_internal_message,
            timeout=mock_config_instance.cmd_timeout,
        )
        mock_pubsub_manager_instance.end_session.assert_called_once_with(
            session_id=session_id
        )


def test_delete_session_publish_fails(
    client, mock_config_instance, mock_pubsub_manager_instance
):
    session_id = "delete-publish-fail-session"
    expected_exception_message = "PubSub offline during delete"
    mock_pubsub_manager_instance.publish_message.side_effect = Exception(
        expected_exception_message
    )

    with patch("app.Message") as MockedMessageClass, pytest.raises(
        Exception, match=expected_exception_message
    ):
        mock_internal_message = MagicMock(spec=Message)
        MockedMessageClass.return_value = mock_internal_message

        client.delete(f"/sessions/{session_id}")

    MockedMessageClass.assert_called_once_with(
        type="command", data={"name": "shutdown", "args": None}
    )
    mock_pubsub_manager_instance.publish_message.assert_awaited_once()
    mock_pubsub_manager_instance.end_session.assert_not_called()
