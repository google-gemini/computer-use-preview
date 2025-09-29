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
import json
from typing import Optional
from pydantic import BaseModel, Field
import uuid
import asyncio
from enum import Enum
from commands import CommandModel


class SignalingStrategy(Enum):
    HTTP = 1
    PUBSUB = 3


class SessionType(str, Enum):
    browser = "browser"
    headful = "headful"
    os = "os"


class CreateSessionRequest(BaseModel):
    type: SessionType = Field(
        title="The type of computer to use.", default=SessionType.browser
    )
    screen_resolution: str = Field(
        title="The screen resolution specified in the format of WxH or WxHxD",
        examples=["1000x1000", "1280x1024x8"],
        default="1920x1000x16",
    )
    timeout_seconds: int = Field(
        title="The maximum session duration in seconds.",
        examples=[600],
        default=60 * 60 * 24,  # 24 hours
    )
    idle_timeout_seconds: int = Field(
        title="The idle timeout in seconds.", examples=[60], default=60 * 60  # 1 hour
    )
    puppeteer_host: str = Field(
        title="Optional puppeteer host", default=""
    )


class CreateSessionResponse(BaseModel):
    id: str = Field(
        title="The UUID of this session.",
        examples=["9652c8a2-4886-41ba-b779-dd658bed2722"],
    )


class ClickParams(BaseModel):
    x: int = Field(title="X coordinate", examples=[450])
    y: int = Field(title="Y coordinate", examples=[180])
    width: int = Field(title="Window width", examples=[450])
    height: int = Field(title="Window height", examples=[180])


class AddPermCheckRequest(BaseModel):
    details: str = Field(
        title="Details of this permission check",
        examples=["test action ABC"],
    )
    click_params: Optional[ClickParams] = Field(
        None,
        title="Parameters of the clickable object of permission request"
    )

class CompletePermCheckRequest(BaseModel):
    granted: bool
    reason: str

class GetPermCheckResponse(BaseModel):
    pending: bool
    details: str
    granted: bool
    reason: str
    click_params: Optional[ClickParams] = Field(
        None,
        title="Parameters of the current clickable object in the browser."
    )

class DeleteSessionResponse(BaseModel):
    id: str = Field(
        title="The UUID of this session.",
        examples=["9652c8a2-4886-41ba-b779-dd658bed2722"],
    )


CreateCommandRequest = CommandModel


class CreateCommandResponse(BaseModel):
    id: str = Field(
        title="The UUID of this command.",
        examples=["9652c8a2-4886-41ba-b449-dd658bed2722"],
    )
    screenshot: str = Field(
        title="A base64 encoded screenshot captured after issuing the command.",
        examples=[
            "iVBORw0KGgoAAAANSUhEUgAAAAgAAAAIAQMAAAD+wSzIAAAABlBMVEX///+/v7+jQ3Y5AAAADklEQVQI12P4AIX8EAgALgAD/aNpbtEAAAAASUVORK5CYII"
        ],
    )

    url: str = Field(
        title="The current URL open in the browser.",
        examples=["https://www.google.com/"],
    )


class Message:
    def __init__(self, type: str, data: dict):
        self.id = str(uuid.uuid4())
        self.type = type
        self.data = data
        self.screenshot = None
        self.url = ""
        self._event = asyncio.Event()

    async def get_screenshot(self, timeout=10) -> str:
        await asyncio.wait_for(self._event.wait(), timeout=timeout)
        return self.screenshot

    async def get_url(self, timeout=10) -> str:
        await asyncio.wait_for(self._event.wait(), timeout=timeout)
        return self.url

    def set_screenshot(self, screenshot, url=""):
        self.screenshot = screenshot
        self.url = url
        self._event.set()

    def json(self):
        return json.dumps({"id": self.id, "command": self.data})
