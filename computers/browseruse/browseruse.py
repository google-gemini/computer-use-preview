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
import os

import requests
import termcolor
from playwright.sync_api import sync_playwright

from ..playwright.playwright import PlaywrightComputer


class BrowserUseComputer(PlaywrightComputer):
    def __init__(self):
        # Browser-use determines its own viewport size, pass dummy value
        super().__init__(screen_size=(1920, 1080))
        self._session = None

    def __enter__(self):
        self._playwright = sync_playwright().start()

        # Create a browser session using browser-use.com API
        api_key = os.environ["BROWSER_USE_API_KEY"]
        headers = {"X-Browser-Use-API-Key": api_key, "Content-Type": "application/json"}

        # Optional parameters for the session
        payload = {}

        # Add timeout if specified in environment
        if "BROWSER_USE_TIMEOUT" in os.environ:
            payload["timeout"] = int(os.environ["BROWSER_USE_TIMEOUT"])

        # Add proxy country code if specified
        if "BROWSER_USE_PROXY_COUNTRY" in os.environ:
            payload["proxyCountryCode"] = os.environ["BROWSER_USE_PROXY_COUNTRY"]

        # Add profile ID if specified
        if "BROWSER_USE_PROFILE_ID" in os.environ:
            payload["profileId"] = os.environ["BROWSER_USE_PROFILE_ID"]

        termcolor.cprint("Creating browser-use session...", color="yellow")
        response = requests.post(
            "https://api.browser-use.com/api/v2/browsers", headers=headers, json=payload
        )
        if response.status_code not in (200, 201):
            raise Exception(f"Failed to create browser session: {response.text}")

        self._session = response.json()

        termcolor.cprint(
            f"Browser-use session created with CDP URL: {self._session['cdpUrl']}",
            color="green",
        )

        # Connect to the browser using the CDP URL
        self._browser = self._playwright.chromium.connect_over_cdp(
            self._session["cdpUrl"]
        )
        self._context = self._browser.contexts[0]
        self._page = self._context.pages[0]
        self._page.goto(self._initial_url)

        termcolor.cprint(
            f"Session started with ID: {self._session['id']}",
            color="green",
            attrs=["bold"],
        )

        if "liveUrl" in self._session and self._session["liveUrl"]:
            termcolor.cprint(
                f"Live view available at: {self._session['liveUrl']}",
                color="cyan",
                attrs=["bold"],
            )

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._page.close()

        if self._context:
            self._context.close()

        if self._browser:
            self._browser.close()

        self._playwright.stop()
