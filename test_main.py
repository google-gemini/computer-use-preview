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

import unittest
from unittest.mock import patch, MagicMock
import main
from config import get_config
from exceptions import ConfigurationError

class TestMain(unittest.TestCase):

    @patch('main.get_config')
    @patch('main.argparse.ArgumentParser')
    @patch('main.PlaywrightComputer')
    @patch('main.BrowserAgent')
    def test_main_playwright(self, mock_browser_agent, mock_playwright_computer, mock_arg_parser, mock_get_config):
        # Mock config
        mock_config = MagicMock()
        mock_config.browser.screen_size = (1440, 900)
        mock_config.playwright.initial_url = 'https://www.google.com'
        mock_config.playwright.highlight_mouse = False
        mock_config.model.name = 'test_model'
        mock_get_config.return_value = mock_config
        
        mock_args = MagicMock()
        mock_args.env = 'playwright'
        mock_args.initial_url = 'test_url'
        mock_args.highlight_mouse = True
        mock_args.query = 'test_query'
        mock_args.model = 'test_model'
        mock_args.config = None
        mock_arg_parser.return_value.parse_args.return_value = mock_args

        result = main.main()

        mock_playwright_computer.assert_called_once_with(
            screen_size=(1440, 900),
            initial_url='test_url',
            highlight_mouse=True
        )
        mock_browser_agent.assert_called_once()
        mock_browser_agent.return_value.agent_loop.assert_called_once()
        self.assertEqual(result, 0)

    @patch('main.get_config')
    @patch('main.argparse.ArgumentParser')
    @patch('main.BrowserbaseComputer')
    @patch('main.BrowserAgent')
    def test_main_browserbase(self, mock_browser_agent, mock_browserbase_computer, mock_arg_parser, mock_get_config):
        # Mock config
        mock_config = MagicMock()
        mock_config.browser.screen_size = (1440, 900)
        mock_config.browserbase.initial_url = 'https://www.google.com'
        mock_config.model.name = 'test_model'
        mock_get_config.return_value = mock_config
        
        mock_args = MagicMock()
        mock_args.env = 'browserbase'
        mock_args.query = 'test_query'
        mock_args.model = 'test_model'
        mock_args.config = None
        mock_args.initial_url = 'test_url'
        mock_args.highlight_mouse = False
        mock_arg_parser.return_value.parse_args.return_value = mock_args

        result = main.main()

        mock_browserbase_computer.assert_called_once_with(
            screen_size=(1440, 900),
            initial_url='test_url'
        )
        mock_browser_agent.assert_called_once()
        mock_browser_agent.return_value.agent_loop.assert_called_once()
        self.assertEqual(result, 0)
    
    @patch('main.get_config')
    @patch('main.argparse.ArgumentParser')
    def test_main_unknown_environment(self, mock_arg_parser, mock_get_config):
        # Mock config
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config
        
        mock_args = MagicMock()
        mock_args.env = 'unknown'
        mock_args.query = 'test_query'
        mock_args.config = None
        mock_arg_parser.return_value.parse_args.return_value = mock_args

        result = main.main()

        self.assertEqual(result, 1)  # Should return error code

if __name__ == '__main__':
    unittest.main()
