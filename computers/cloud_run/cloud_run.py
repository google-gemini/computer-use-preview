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
import base64
import termcolor
import time
from typing import Any, Optional, Literal
import requests
from urllib.parse import urljoin
from ..computer import (
    Computer,
    EnvState,
)
from rich.console import Console

console = Console()


class CloudRunComputer(Computer):
    """Connects to a Cloud Run server and uses Chromium there."""

    def __init__(
        self,
        api_server: str,
        screen_size: tuple[int, int],
        api_key: Optional[str] = None,
    ):
        self._screen_size = screen_size
        self._api_server = api_server
        self._api_key = api_key
        self._headers = {}
        if self._api_key:
            self._headers = {"X-API-Key": self._api_key}

    def __enter__(self):
        screen_resolution = f"{self._screen_size[0]}x{self._screen_size[1]}"
        sessions_url = urljoin(self._api_server, "sessions")
        start_time = time.time()
        with console.status("Creating session...", spinner_style=None):
            response = requests.post(
                sessions_url,
                json={
                    "type": "browser",
                    "screen_resolution": screen_resolution,
                    # Erase the VM after 600 seconds of total runtime.
                    "timeout_seconds": 600,
                    # Or after 60 seconds of inactivity.
                    "idle_timeout_seconds": 60,
                },
                headers=self._headers,
            )
        end_time = time.time()
        termcolor.cprint(
            f"Session created in {end_time - start_time:.2f} seconds.",
            color="green",
            attrs=["bold"],
        )
        if response.status_code != 200:
            termcolor.cprint(
                f"Error creating session: {response.status_code} {response.text}",
                color="red",
                attrs=["bold"],
            )
            raise Exception(
                f"Error creating session: {response.status_code} {response.text}"
            )
        self._session_id = response.json()["id"]
        # Use urljoin for robust URL construction
        session_viewer_url = urljoin(
            self._api_server, f"session.html?session_id={self._session_id}"
        )
        if self._api_key:
            session_viewer_url += f"&api_key={self._api_key}"
        print(f"Follow along at: {session_viewer_url}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Use urljoin for robust URL construction
        session_url = urljoin(self._api_server, "sessions/" + self._session_id)
        requests.delete(session_url, headers=self._headers)

    def _run_command(
        self, command: str, args: Optional[dict[str, Any]] = None
    ) -> EnvState:
        url = urljoin(self._api_server, f"sessions/{self._session_id}/commands")
        response = requests.post(
            url,
            json={
                "name": command,
                "args": args,
            },
            headers=self._headers,
        )
        response.raise_for_status()
        screenshot_str: str = response.json()["screenshot"]
        screenshot_bytes = base64.b64decode(screenshot_str)
        url = response.json()["url"]
        return EnvState(screenshot=screenshot_bytes, url=url)

    def open_web_browser(self) -> EnvState:
        return self._run_command("open_web_browser")

    def click_at(self, x: int, y: int) -> EnvState:
        return self._run_command("click_at", args={"x": x, "y": y})

    def hover_at(self, x: int, y: int) -> EnvState:
        return self._run_command("hover_at", args={"x": x, "y": y})

    def type_text_at(
        self,
        x: int,
        y: int,
        text: str,
        press_enter: bool,
        clear_before_typing: bool,
    ) -> EnvState:
        return self._run_command(
            "type_text_at",
            args={
                "x": x,
                "y": y,
                "text": text,
                "press_enter": press_enter,
                "clear_before_typing": clear_before_typing,
            },
        )

    def scroll_document(self, direction: str) -> EnvState:
        return self._run_command("scroll_document", args={"direction": direction})

    def scroll_at(
        self,
        x: int,
        y: int,
        direction: Literal["up", "down", "left", "right"],
        magnitude: int,
    ) -> EnvState:
        return self._run_command(
            "scroll_at",
            args={"x": x, "y": y, "direction": direction, "magnitude": magnitude},
        )

    def wait_5_seconds(self) -> EnvState:
        return self._run_command("wait_5_seconds")

    def go_back(self) -> EnvState:
        return self._run_command("go_back")

    def go_forward(self) -> EnvState:
        return self._run_command("go_forward")

    def search(self) -> EnvState:
        return self._run_command("search")

    def navigate(self, url: str) -> EnvState:
        return self._run_command("navigate", args={"url": url})

    def key_combination(self, keys: list[str]) -> EnvState:
        return self._run_command("key_combination", args={"keys": "+".join(keys)})

    def drag_and_drop(
        self, x: int, y: int, destination_x: int, destination_y: int
    ) -> EnvState:
        return self._run_command(
            "drag_and_drop",
            args={
                "x": x,
                "y": y,
                "destination_x": destination_x,
                "destination_y": destination_y,
            },
        )

    def current_state(self) -> EnvState:
        return self._run_command("screenshot")

    def screen_size(self) -> tuple[int, int]:
        return self._screen_size
