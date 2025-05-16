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
import json
import subprocess
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import Request
from models import Message
from pubsub import BaseManager, DevManager


@pytest.fixture
def base_manager():
    return BaseManager()


@pytest.fixture
def dev_manager():
    return DevManager()


@pytest.fixture
def mock_message():
    msg = MagicMock(spec=Message)
    msg.id = "test-message-id"
    msg.type = "test_command"
    msg.data = {"action": "click", "x": 100, "y": 200}
    msg.json = MagicMock(return_value=json.dumps({"id": msg.id, "command": msg.data}))
    msg._event = asyncio.Event()
    msg.screenshot = None
    msg.url = ""

    def mock_set_screenshot_sync(screenshot, url=""):
        msg.screenshot = screenshot
        msg.url = url
        msg._event.set()

    msg.set_screenshot = MagicMock(side_effect=mock_set_screenshot_sync)

    async def mock_get_screenshot(timeout=1):
        await asyncio.wait_for(msg._event.wait(), timeout=timeout)
        return msg.screenshot

    async def mock_get_url(timeout=1):
        await asyncio.wait_for(msg._event.wait(), timeout=timeout)
        return msg.url

    msg.get_screenshot = mock_get_screenshot
    msg.get_url = mock_get_url
    return msg


@pytest.fixture
def mock_request():
    request = MagicMock(spec=Request)
    request.is_disconnected = AsyncMock(return_value=False)
    return request


@pytest.mark.asyncio
async def test_base_manager_stream_screenshots_empty_queue_and_disconnect(
    base_manager, mock_request
):
    session_id = "test-session"
    mock_request.is_disconnected = AsyncMock(
        side_effect=[False, True]
    )  # Disconnect after first check

    messages = []
    async for message in base_manager.stream_screenshots(session_id, mock_request):
        messages.append(message)

    assert not messages
    assert session_id in base_manager.streaming_listeners


@pytest.mark.asyncio
async def test_base_manager_notify_streamers(base_manager):
    session_id = "test-notify-session"
    screenshot_data = "anotherbase64data"
    expected_message = f"event: screenshot\ndata: {screenshot_data}\n\n"

    # Setup listeners
    queue1 = []
    queue2 = []
    base_manager.streaming_listeners[session_id] = {
        "listener1_id": queue1,
        "listener2_id": queue2,
    }

    await base_manager._notify_streamers(session_id, screenshot_data)

    assert len(queue1) == 1
    assert queue1[0] == expected_message
    assert len(queue2) == 1
    assert queue2[0] == expected_message


@pytest.mark.asyncio
async def test_base_manager_notify_streamers_no_listeners(base_manager):
    session_id = "test-notify-no-listeners"
    screenshot_data = "somedata"

    # No listeners for this session_id
    await base_manager._notify_streamers(session_id, screenshot_data)
    assert session_id not in base_manager.streaming_listeners


@pytest.mark.asyncio
@patch("subprocess.run")
async def test_dev_manager_publish_message_success(
    mock_subprocess_run,
    dev_manager,
    mock_message,
):
    session_id = "test-docker-session"
    screenshot_data = "iVBORw0KGgoAAAANSUhEUgA="
    url_data = "http://example.com"
    docker_response = {"screenshot": screenshot_data, "url": url_data}

    mock_subprocess_run.return_value = MagicMock(
        stdout=json.dumps(docker_response).encode("utf-8"),
        returncode=0,
    )

    dev_manager._notify_streamers = AsyncMock()

    await dev_manager.publish_message(session_id, mock_message)

    mock_message.json.assert_called_once()
    mock_subprocess_run.assert_called_once_with(
        ["docker", "exec", session_id, "run-command", mock_message.json.return_value],
        stdout=subprocess.PIPE,
    )

    mock_message.set_screenshot.assert_called_once_with(
        screenshot=screenshot_data, url=url_data
    )

    assert await mock_message.get_screenshot() == screenshot_data
    assert await mock_message.get_url() == url_data

    dev_manager._notify_streamers.assert_called_once_with(
        session_id=session_id, screenshot=screenshot_data
    )


@pytest.mark.asyncio
@patch("subprocess.run")
async def test_dev_manager_publish_message_docker_error(
    mock_subprocess_run, dev_manager, mock_message
):
    session_id = "test-docker-error-session"

    mock_subprocess_run.return_value = MagicMock(
        stdout="Error from docker".encode("utf-8"),
        stderr="Some error".encode("utf-8"),
        returncode=1,
    )
    dev_manager._notify_streamers = AsyncMock()

    with pytest.raises(json.JSONDecodeError):
        await dev_manager.publish_message(session_id, mock_message)

    mock_message.json.assert_called_once()
    mock_subprocess_run.assert_called_once_with(
        ["docker", "exec", session_id, "run-command", mock_message.json.return_value],
        stdout=subprocess.PIPE,
    )

    mock_message.set_screenshot.assert_not_called()
    assert mock_message.screenshot is None
    dev_manager._notify_streamers.assert_not_called()


@patch("subprocess.run")
def test_dev_manager_end_session(mock_subprocess_run, dev_manager):
    session_id = "test-end-session"
    mock_subprocess_run.return_value = MagicMock(
        stdout="stopped".encode("utf-8"), returncode=0
    )

    dev_manager.end_session(session_id)

    mock_subprocess_run.assert_called_once_with(
        ["docker", "stop", session_id],
        stdout=subprocess.PIPE,
    )


@pytest.mark.asyncio
async def test_dev_manager_start_and_shutdown_do_nothing(dev_manager):
    await dev_manager.start()
    await dev_manager.shutdown()
    dev_manager.start_session("some-id")


@pytest.mark.asyncio
async def test_message_get_screenshot_and_url_timeout():
    msg = Message(type="test", data={"command": "noop"})

    with pytest.raises(asyncio.TimeoutError):
        await msg.get_screenshot(timeout=0.01)

    with pytest.raises(asyncio.TimeoutError):
        await msg.get_url(timeout=0.01)


@pytest.mark.asyncio
async def test_message_set_and_get_screenshot_url():
    msg = Message(type="test", data={"command": "action"})
    test_screenshot = "base64imagetest"
    test_url = "https://test.dev"

    msg.set_screenshot(test_screenshot, test_url)

    screenshot = await msg.get_screenshot(timeout=1)
    url = await msg.get_url(timeout=1)

    assert screenshot == test_screenshot
    assert url == test_url


def test_message_json_serialization():
    command_data = {"action": "navigate", "target_url": "http://google.com"}
    msg = Message(type="navigation_command", data=command_data)
    msg_id = msg.id

    expected_json = json.dumps({"id": msg_id, "command": command_data})
    assert msg.json() == expected_json
