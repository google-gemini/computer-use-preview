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
import unittest
from unittest.mock import MagicMock, patch
from computers.playwright.playwright import PlaywrightComputer


class TestPlaywrightHeadless(unittest.TestCase):

    @patch("computers.playwright.playwright.sync_playwright")
    def test_playwright_headless_false_env(self, mock_sync_playwright):
        mock_playwright = MagicMock()
        mock_sync_playwright.return_value.start.return_value = mock_playwright

        with patch.dict(os.environ, {"PLAYWRIGHT_HEADLESS": "false"}):
            with PlaywrightComputer(screen_size=(1024, 768)):
                mock_playwright.chromium.launch.assert_called_once()
                _, kwargs = mock_playwright.chromium.launch.call_args
                self.assertFalse(kwargs["headless"])

    @patch("computers.playwright.playwright.sync_playwright")
    def test_playwright_headless_true_env(self, mock_sync_playwright):
        mock_playwright = MagicMock()
        mock_sync_playwright.return_value.start.return_value = mock_playwright

        with patch.dict(os.environ, {"PLAYWRIGHT_HEADLESS": "true"}):
            with PlaywrightComputer(screen_size=(1024, 768)):
                mock_playwright.chromium.launch.assert_called_once()
                _, kwargs = mock_playwright.chromium.launch.call_args
                self.assertTrue(kwargs["headless"])

    @patch("computers.playwright.playwright.sync_playwright")
    def test_playwright_headless_default_unset(self, mock_sync_playwright):
        mock_playwright = MagicMock()
        mock_sync_playwright.return_value.start.return_value = mock_playwright

        with patch.dict(os.environ, {}, clear=True):
            with PlaywrightComputer(screen_size=(1024, 768)):
                mock_playwright.chromium.launch.assert_called_once()
                _, kwargs = mock_playwright.chromium.launch.call_args
                self.assertFalse(kwargs["headless"])


if __name__ == "__main__":
    unittest.main()
