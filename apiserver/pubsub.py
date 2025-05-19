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
import logging
from fastapi import Request
import subprocess
from models import Message
import asyncio


class BaseManager:
    def __init__(self):
        self.streaming_listeners = dict()

    async def stream_screenshots(self, session_id: str, request: Request):
        if session_id not in self.streaming_listeners:
            self.streaming_listeners[session_id] = dict()

        queue = []
        listener_id = id(queue)
        self.streaming_listeners[session_id][listener_id] = queue

        while True:
            if await request.is_disconnected():
                break
            while len(self.streaming_listeners[session_id][listener_id]) > 0:
                message = self.streaming_listeners[session_id][listener_id].pop(0)
                yield message
        await asyncio.sleep(0.1)

    async def _notify_streamers(self, session_id: str, screenshot: str) -> None:
        if session_id in self.streaming_listeners:
            for queue in self.streaming_listeners[session_id].values():
                queue.append(f"event: screenshot\ndata: {screenshot}\n\n")

    async def start(self) -> None:
        pass


class DevManager(BaseManager):
    def __init__(self):
        super().__init__()
        self.pending_messages = dict()
        self.streaming_listeners = dict()

    async def publish_message(
        self, session_id: str, message: Message, timeout: int = None
    ) -> None:
        result = subprocess.run(
            ["docker", "exec", session_id, "run-command", f"{message.json()}"],
            stdout=subprocess.PIPE,
        )
        data_str = result.stdout.decode("utf-8")
        parsed_data = json.loads(data_str)
        message.set_screenshot(
            screenshot=parsed_data["screenshot"], url=parsed_data["url"]
        )
        await self._notify_streamers(
            session_id=session_id, screenshot=parsed_data["screenshot"]
        )

    def end_session(self, session_id: str) -> None:
        result = subprocess.run(["docker", "stop", session_id], stdout=subprocess.PIPE)
        logging.info(result)

    async def start(self) -> None:
        pass

    async def shutdown(self) -> None:
        pass

    def start_session(self, session_id: str) -> None:
        pass
