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
import asyncio
import json
import base64
from models import (
    CreateSessionRequest,
    CreateSessionResponse,
    DeleteSessionResponse,
    CreateCommandResponse,
    Message,
    SessionType,
)


def test_create_session_request_defaults():
    """Tests CreateSessionRequest uses defaults correctly."""
    req = CreateSessionRequest()
    assert req.type == SessionType.browser
    assert req.screen_resolution == "1920x1000x16"
    assert req.timeout_seconds == 60 * 60 * 24
    assert req.idle_timeout_seconds == 60 * 60


def test_create_session_request_custom():
    """Tests CreateSessionRequest with custom values."""
    req = CreateSessionRequest(
        type=SessionType.os,
        screen_resolution="800x600",
        timeout_seconds=10,
        idle_timeout_seconds=5,
    )
    assert req.type == SessionType.os
    assert req.screen_resolution == "800x600"
    assert req.timeout_seconds == 10
    assert req.idle_timeout_seconds == 5


def test_create_session_response():
    resp = CreateSessionResponse(id="uuid-123")
    assert resp.id == "uuid-123"


def test_delete_session_response():
    resp = DeleteSessionResponse(id="uuid-456")
    assert resp.id == "uuid-456"


def test_create_command_response():
    b64 = base64.b64encode(b"foo").decode("utf-8")
    url = "https://google.com/"
    resp = CreateCommandResponse(id="cmd-123", screenshot=b64, url=url)
    assert resp.id == "cmd-123"
    assert resp.screenshot == b64
    assert resp.url == url


def test_message_init_and_json():
    """Tests Message constructor and json() output."""
    cmd_data = {"a": 1, "b": "test"}
    msg = Message(type="COMMAND", data=cmd_data)

    # Override random UUID for predictable testing
    msg.id = "fixed-id-for-test"

    assert msg.type == "COMMAND"
    assert msg.data == cmd_data
    assert msg.id == "fixed-id-for-test"
    assert msg.screenshot is None
    assert not msg._event.is_set()

    # Test json rendering
    parsed = json.loads(msg.json())
    assert parsed == {"id": "fixed-id-for-test", "command": {"a": 1, "b": "test"}}


@pytest.mark.asyncio
async def test_message_async_get_set():
    """Tests that set_screenshot unblocks awaiters on get_screenshot and get_url."""
    msg = Message(type="CMD", data={})
    TEST_SS = "base64_string"
    TEST_URL = "http://url.com"

    async def setter(delay, ss, url):
        await asyncio.sleep(delay)
        msg.set_screenshot(screenshot=ss, url=url)

    # Start setter task
    asyncio.create_task(setter(0.02, TEST_SS, TEST_URL))

    # Await getters - should block briefly until setter runs
    ss = await msg.get_screenshot(timeout=1.0)
    url = await msg.get_url(timeout=1.0)

    assert msg._event.is_set()
    assert ss == TEST_SS
    assert url == TEST_URL


@pytest.mark.asyncio
async def test_message_async_timeout():
    """
    Tests that get_screenshot and get_url timeout correctly if
    set_screenshot is not called.
    """
    msg = Message(type="CMD", data={})

    with pytest.raises(asyncio.TimeoutError):
        await msg.get_screenshot(timeout=0.01)

    with pytest.raises(asyncio.TimeoutError):
        await msg.get_url(timeout=0.01)
