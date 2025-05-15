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
from ..computer import (
    Computer,
    EnvState,
)
from playwright.sync_api import sync_playwright


class PlaywrightComputer(Computer):
    """Connects to a Cloud Run server and uses Chromium there."""

    def __init__(
        self,
        screen_size: tuple[int, int],
        initial_url: str = "https://www.google.com",
        search_engine_url: str = "https://www.google.com",
        highlight_mouse: bool = False,
    ):
        self._initial_url = initial_url
        self._screen_size = screen_size
        self._search_engine_url = search_engine_url
        self._highlight_mouse = highlight_mouse

    def __enter__(self):
        print("Creating session...")
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(
            args=[
                '--disable-blink-features=AutomationControlled'
            ],
            headless=False,
            )
        self._context = self._browser.new_context(
            viewport={
                "width": self._screen_size[0],
                "height": self._screen_size[1],
            }
        )
        self._page = self._context.new_page()
        self._page.goto(self._initial_url)

        termcolor.cprint(
            f"Started local playwright.",
            color="green",
            attrs=["bold"],
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._context:
            self._context.close()
        try:
            self._browser.close()
        except Exception as e:
            # Browser was already shut down because of SIGINT or such.
            if "Browser.close: Connection closed while reading from the driver" in str(
                e
            ):
                pass
            else:
                raise

        self._playwright.stop()

    def open_web_browser(self) -> EnvState:
        return self.current_state()

    def click_at(self, x: int, y: int):
        self.highlight_mouse(x, y)
        self._page.mouse.click(x, y)
        self._page.wait_for_load_state()
        return self.current_state()

    def hover_at(self, x: int, y: int):
        self.highlight_mouse(x, y)
        self._page.mouse.move(x, y)
        self._page.wait_for_load_state()
        return self.current_state()

    def type_text_at(self, x: int, y: int, text: str) -> EnvState:
        self.highlight_mouse(x, y)
        self._page.mouse.click(x, y)
        self._page.wait_for_load_state()
        self._page.keyboard.type(text)
        self._page.wait_for_load_state()
        self.key_combination(["Enter"])
        self._page.wait_for_load_state()
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
        self._page.wait_for_load_state()
        return self.current_state()

    def go_forward(self) -> EnvState:
        self._page.go_forward()
        self._page.wait_for_load_state()
        return self.current_state()

    def search(self) -> EnvState:
        return self.navigate(self._search_engine_url)

    def navigate(self, url: str) -> EnvState:
        self._page.goto(url)
        self._page.wait_for_load_state()
        return self.current_state()

    def key_combination(self, keys: list[str]) -> EnvState:
        for key in keys[:-1]:
            self._page.keyboard.down(key)

        self._page.keyboard.press(keys[-1])

        for key in reversed(keys[:-1]):
            self._page.keyboard.up(key)

        return self.current_state()

    def current_state(self) -> EnvState:
        self._page.wait_for_load_state()
        # Even if Playwright reports the page as loaded, it may not be so.
        # Add a manual sleep to make sure the page has finished rendering.
        time.sleep(0.5)
        screenshot_bytes = self._page.screenshot(type="png", full_page=False)
        return EnvState(screenshot=screenshot_bytes, url=self._page.url)

    def screen_size(self) -> tuple[int, int]:
        return self._screen_size

    def highlight_mouse(self, x: int, y: int):
        if not self._highlight_mouse:
            return
        self._page.evaluate(
            f"""
        () => {{
            const element_id = "playwright-feedback-circle";
            const div = document.createElement('div');
            div.id = element_id;
            div.style.pointerEvents = 'none';
            div.style.border = '4px solid red';
            div.style.borderRadius = '50%';
            div.style.width = '20px';
            div.style.height = '20px';
            div.style.position = 'absolute';
            div.style.zIndex = '9999';
            document.body.appendChild(div);

            div.hidden = false;
            div.style.left = {x} - 10 + 'px';
            div.style.top = {y} - 10 + 'px';

            setTimeout(() => {{
                div.hidden = true;
            }}, 2000);
        }}
    """
        )
        # Wait a bit for the user to see the cursor.
        time.sleep(1)
