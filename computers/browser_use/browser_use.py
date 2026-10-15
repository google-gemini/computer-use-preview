# Copyright 2026 Google LLC
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
import os

import httpx
import termcolor
from playwright.sync_api import sync_playwright

from ..playwright.playwright import PlaywrightComputer

BROWSER_USE_API_URL = "https://api.browser-use.com/api/v4"


class BrowserUseComputer(PlaywrightComputer):
    """Runs the agent in a Browser Use Cloud browser, connected over CDP."""

    def __init__(
        self,
        screen_size: tuple[int, int],
        initial_url: str = "https://www.google.com",
    ):
        super().__init__(screen_size, initial_url)
        self._session_id = None
        self._playwright = None
        self._browser = None
        self._context = None

    def __enter__(self):
        print("Creating session...")
        self._http = httpx.Client(
            base_url=BROWSER_USE_API_URL,
            headers={"X-Browser-Use-API-Key": os.environ["BROWSER_USE_API_KEY"]},
            timeout=60,
        )
        try:
            response = self._http.post(
                "/browsers",
                json={
                    "browserScreenWidth": self._screen_size[0],
                    "browserScreenHeight": self._screen_size[1],
                },
            )
            response.raise_for_status()
            session = response.json()
            self._session_id = session["id"]

            self._playwright = sync_playwright().start()
            self._browser = self._playwright.chromium.connect_over_cdp(
                session["cdpUrl"]
            )
            self._context = self._browser.contexts[0]
            self._page = (
                self._context.pages[0]
                if self._context.pages
                else self._context.new_page()
            )
            self._page.set_viewport_size(
                {"width": self._screen_size[0], "height": self._screen_size[1]}
            )
            self._page.goto(self._initial_url)
            self._context.on("page", self._handle_new_page)
        except BaseException:
            self._cleanup()
            raise

        termcolor.cprint(
            f"Session started. Watch it live at {session.get('liveUrl')}",
            color="green",
            attrs=["bold"],
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._cleanup()

    def _cleanup(self):
        # Closing the CDP connection does not stop a Browser Use Cloud browser,
        # so always stop it explicitly to end billing.
        try:
            if self._browser:
                self._browser.close()
            if self._playwright:
                self._playwright.stop()
        finally:
            if self._session_id:
                self._http.patch(
                    f"/browsers/{self._session_id}", json={"action": "stop"}
                ).raise_for_status()
                self._session_id = None
            self._http.close()
