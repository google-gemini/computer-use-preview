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

import json
import os
import unittest
from unittest.mock import MagicMock, patch

import httpx

from computers.browser_use import browser_use as browser_use_module
from computers import BrowserUseComputer


class TestBrowserUseComputer(unittest.TestCase):

    def setUp(self):
        self.requests = []

        def handler(request):
            self.requests.append(request)
            if request.method == 'POST':
                return httpx.Response(201, json={
                    'id': 'session-1',
                    'cdpUrl': 'wss://cdp.example/session-1',
                    'liveUrl': 'https://live.example/session-1',
                })
            return httpx.Response(200, json={'id': 'session-1', 'status': 'stopped'})

        real_client = httpx.Client
        client_patcher = patch.object(
            browser_use_module.httpx, 'Client',
            side_effect=lambda **kwargs: real_client(transport=httpx.MockTransport(handler), **kwargs),
        )
        client_patcher.start()
        self.addCleanup(client_patcher.stop)

        playwright_patcher = patch.object(browser_use_module, 'sync_playwright')
        self.mock_sync_playwright = playwright_patcher.start()
        self.addCleanup(playwright_patcher.stop)
        self.mock_playwright = self.mock_sync_playwright.return_value.start.return_value
        self.mock_browser = self.mock_playwright.chromium.connect_over_cdp.return_value
        self.mock_page = MagicMock()
        self.mock_browser.contexts = [MagicMock(pages=[self.mock_page])]

        env_patcher = patch.dict(os.environ, {'BROWSER_USE_API_KEY': 'test-key'})
        env_patcher.start()
        self.addCleanup(env_patcher.stop)

    def test_creates_connects_and_stops_browser(self):
        computer = BrowserUseComputer(screen_size=(1440, 900), initial_url='https://example.com')
        with computer:
            self.mock_playwright.chromium.connect_over_cdp.assert_called_once_with('wss://cdp.example/session-1')
            self.mock_page.set_viewport_size.assert_called_once_with({'width': 1440, 'height': 900})
            self.mock_page.goto.assert_called_once_with('https://example.com')

        create, stop = self.requests
        self.assertEqual(create.method, 'POST')
        self.assertEqual(create.url.path, '/api/v4/browsers')
        self.assertEqual(create.headers['X-Browser-Use-API-Key'], 'test-key')
        self.assertEqual(json.loads(create.content), {'browserScreenWidth': 1440, 'browserScreenHeight': 900})
        self.assertEqual(stop.method, 'PATCH')
        self.assertEqual(stop.url.path, '/api/v4/browsers/session-1')
        self.assertEqual(json.loads(stop.content), {'action': 'stop'})
        self.mock_browser.close.assert_called_once()
        self.mock_playwright.stop.assert_called_once()

    def test_stops_browser_when_connect_fails(self):
        self.mock_playwright.chromium.connect_over_cdp.side_effect = RuntimeError('connect failed')
        computer = BrowserUseComputer(screen_size=(1440, 900))
        with self.assertRaises(RuntimeError):
            computer.__enter__()

        self.assertEqual([r.method for r in self.requests], ['POST', 'PATCH'])
        self.mock_playwright.stop.assert_called_once()


if __name__ == '__main__':
    unittest.main()
