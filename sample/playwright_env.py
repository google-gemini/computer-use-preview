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
import termcolor
import time
from computer_use_environment import (
    ComputerUseEnvironment,
    EnvState,
)
from playwright.sync_api import sync_playwright

GOOGLE_URL = "https://www.google.com"


class PlaywrightComputer(ComputerUseEnvironment):
    """Connects to a Cloud Run server and uses Chromium there."""

    def __init__(self,  screen_size: tuple[int, int]):
        self._screen_size = screen_size

    def __enter__(self):
        print("Creating session...")
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=False)
        self._context = self._browser.new_context(
            viewport={
                'width': self._screen_size[0],
                'height': self._screen_size[1],
            }
        ) 
        self._page = self._context.new_page()
        self._page.goto(GOOGLE_URL)

        termcolor.cprint(
            f"Starting local playwright.",
            color="green",
            attrs=["bold"],
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._page:
            self._page.close()
        if self._context:
            self._context.close()
        self._browser.close()
        self._playwright.stop()


    def open_web_browser(self) -> EnvState:
        return self.current_state()

    def click_at(self, y, x):
        self._page.mouse.click(x, y)
        return self.current_state()

    def hover_at(self, y, x):
        self._page.mouse.move(x, y)
        return self.current_state()

    def type_text_at(self, x: int, y: int, text: str) -> EnvState:
        self._page.mouse.click(x, y)
        self._page.keyboard.type(text)
        self.key_combination(["Enter"])
        return self.current_state()

    def scroll_document(self, direction: str) -> EnvState:
        match direction.lower():
            case "down":
                return self.key_combination(["PageDown"])
            case "up":
                return self.key_combination(["PageUp"])
            case _:
                raise ValueError("Unsupported direction: ", direction)

    def wait_5_seconds(self) -> EnvState:
        time.sleep(5)
        return self.current_state()

    def go_back(self) -> EnvState:
        self._page.go_back()
        return self.current_state()

    def go_forward(self) -> EnvState:
        self._page.go_forward()
        return self.current_state()

    def search(self) -> EnvState:
        return self.navigate(GOOGLE_URL)

    def navigate(self, url: str) -> EnvState:
        self._page.goto(url)
        return self.current_state()

    def key_combination(self, keys: list[str]) -> EnvState:
        for key in keys[:-1]:
            self._page.keyboard.down(key)

        self._page.keyboard.press(keys[-1])

        for key in reversed(keys[:-1]):
            self._page.keyboard.up(key)

        return self.current_state()

    def current_state(self) -> EnvState:
        screenshot_bytes = self._page.screenshot(type="png")
        return EnvState(screenshot=screenshot_bytes, url = self._page.url)

    def screen_size(self) -> tuple[int, int]:
        return self._screen_size
