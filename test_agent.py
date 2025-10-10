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
from google.genai import types
from agent import BrowserAgent, multiply_numbers
from computers import EnvState
from config import get_config
from exceptions import ActionExecutionError, ModelResponseError
from utils import OperationLogger, PerformanceMonitor
from plugins import PluginManager, BuiltinActionsPlugin

class TestBrowserAgent(unittest.TestCase):
    def setUp(self):
        os.environ["GEMINI_API_KEY"] = "test_api_key"
        self.mock_browser_computer = MagicMock()
        self.mock_browser_computer.screen_size.return_value = (1000, 1000)
        self.agent = BrowserAgent(
            browser_computer=self.mock_browser_computer,
            query="test query",
            model_name="test_model"
        )
        # Mock the genai client
        self.agent._client = MagicMock()
        # Mock the logger and performance monitor
        self.agent.logger = MagicMock()
        self.agent.performance_monitor = MagicMock()

    def test_multiply_numbers(self):
        self.assertEqual(multiply_numbers(2, 3), {"result": 6})

    def test_action_handler_open_web_browser(self):
        action = types.FunctionCall(name="open_web_browser", args={})
        self.agent.action_handler.handle_action(action)
        self.mock_browser_computer.open_web_browser.assert_called_once()

    def test_action_handler_click_at(self):
        action = types.FunctionCall(name="click_at", args={"x": 100, "y": 200})
        self.agent.action_handler.handle_action(action)
        self.mock_browser_computer.click_at.assert_called_once_with(x=100, y=200)

    def test_action_handler_type_text_at(self):
        action = types.FunctionCall(name="type_text_at", args={"x": 100, "y": 200, "text": "hello"})
        self.agent.action_handler.handle_action(action)
        self.mock_browser_computer.type_text_at.assert_called_once_with(
            x=100, y=200, text="hello", press_enter=False, clear_before_typing=True
        )

    def test_action_handler_scroll_document(self):
        action = types.FunctionCall(name="scroll_document", args={"direction": "down"})
        self.agent.action_handler.handle_action(action)
        self.mock_browser_computer.scroll_document.assert_called_once_with("down")

    def test_action_handler_navigate(self):
        action = types.FunctionCall(name="navigate", args={"url": "https://example.com"})
        self.agent.action_handler.handle_action(action)
        self.mock_browser_computer.navigate.assert_called_once_with("https://example.com")

    def test_action_handler_unknown_function(self):
        action = types.FunctionCall(name="unknown_function", args={})
        with self.assertRaises(ActionExecutionError):
            self.agent.action_handler.handle_action(action)

    def test_denormalize_x(self):
        self.assertEqual(self.agent.denormalize_x(500), 500)

    def test_denormalize_y(self):
        self.assertEqual(self.agent.denormalize_y(500), 500)

    @patch('agent.browser_agent.BrowserAgent.get_model_response')
    def test_run_one_iteration_no_function_calls(self, mock_get_model_response):
        mock_response = MagicMock()
        mock_candidate = MagicMock()
        mock_candidate.content.parts = [types.Part(text="some reasoning")]
        mock_response.candidates = [mock_candidate]
        mock_get_model_response.return_value = mock_response

        result = self.agent.run_one_iteration()

        self.assertEqual(result, "COMPLETE")
        contents = self.agent.conversation_manager.get_contents()
        self.assertEqual(len(contents), 2)
        self.assertEqual(contents[1], mock_candidate.content)

    @patch('agent.browser_agent.BrowserAgent.get_model_response')
    def test_run_one_iteration_with_function_call(self, mock_get_model_response):
        mock_response = MagicMock()
        mock_candidate = MagicMock()
        function_call = types.FunctionCall(name="navigate", args={"url": "https://example.com"})
        mock_candidate.content.parts = [types.Part(function_call=function_call)]
        mock_response.candidates = [mock_candidate]
        mock_get_model_response.return_value = mock_response

        # Mock the action handler
        mock_env_state = EnvState(screenshot=b"screenshot", url="https://example.com")
        self.agent.action_handler.handle_action = MagicMock(return_value=mock_env_state)

        result = self.agent.run_one_iteration()

        self.assertEqual(result, "CONTINUE")
        self.agent.action_handler.handle_action.assert_called_once_with(function_call)
        contents = self.agent.conversation_manager.get_contents()
        self.assertEqual(len(contents), 3)


class TestConfiguration(unittest.TestCase):
    """测试配置系统"""
    
    def test_get_config(self):
        config = get_config()
        self.assertIsNotNone(config)
        self.assertIsNotNone(config.model)
        self.assertIsNotNone(config.browser)
        self.assertIsNotNone(config.playwright)
        self.assertIsNotNone(config.browserbase)
    
    def test_config_model_settings(self):
        config = get_config()
        self.assertIsInstance(config.model.name, str)
        self.assertIsInstance(config.model.temperature, float)
        self.assertIsInstance(config.model.max_output_tokens, int)
    
    def test_config_browser_settings(self):
        config = get_config()
        self.assertIsInstance(config.browser.screen_size, tuple)
        self.assertEqual(len(config.browser.screen_size), 2)
        self.assertIsInstance(config.browser.screen_size[0], int)
        self.assertIsInstance(config.browser.screen_size[1], int)


class TestExceptions(unittest.TestCase):
    """测试自定义异常"""
    
    def test_browser_agent_error(self):
        from exceptions import BrowserAgentError
        error = BrowserAgentError("Test error", "TEST_ERROR", {"key": "value"})
        self.assertEqual(error.message, "Test error")
        self.assertEqual(error.error_code, "TEST_ERROR")
        self.assertEqual(error.details, {"key": "value"})
    
    def test_model_response_error(self):
        from exceptions import ModelResponseError
        error = ModelResponseError("Model failed", "test_model", {"response": "data"})
        self.assertEqual(error.message, "Model failed")
        self.assertEqual(error.model_name, "test_model")
        self.assertEqual(error.response_data, {"response": "data"})
    
    def test_action_execution_error(self):
        from exceptions import ActionExecutionError
        original_error = Exception("Original error")
        error = ActionExecutionError("Action failed", "click_at", {"x": 100, "y": 200}, original_error)
        self.assertEqual(error.message, "Action failed")
        self.assertEqual(error.action_name, "click_at")
        self.assertEqual(error.action_args, {"x": 100, "y": 200})
        self.assertEqual(error.original_error, original_error)


class TestPluginSystem(unittest.TestCase):
    """测试插件系统"""
    
    def setUp(self):
        self.mock_computer = MagicMock()
        self.mock_computer.screen_size.return_value = (1000, 1000)
    
    def test_builtin_actions_plugin(self):
        plugin = BuiltinActionsPlugin()
        self.assertEqual(plugin.name, "builtin_actions")
        self.assertTrue(plugin.can_handle("click_at"))
        self.assertFalse(plugin.can_handle("unknown_action"))
        self.assertIn("click_at", plugin.get_supported_actions())
    
    def test_plugin_manager(self):
        manager = PluginManager()
        plugin = BuiltinActionsPlugin()
        
        # 测试注册插件
        manager.register_plugin(plugin)
        self.assertEqual(manager.get_plugin_count(), 1)
        
        # 测试获取插件
        retrieved_plugin = manager.get_plugin("builtin_actions")
        self.assertEqual(retrieved_plugin, plugin)
        
        # 测试处理动作
        action = types.FunctionCall(name="open_web_browser", args={})
        result = manager.handle_action(action, self.mock_computer)
        self.mock_computer.open_web_browser.assert_called_once()
    
    def test_plugin_manager_unknown_action(self):
        manager = PluginManager()
        plugin = BuiltinActionsPlugin()
        manager.register_plugin(plugin)
        
        action = types.FunctionCall(name="unknown_action", args={})
        with self.assertRaises(ActionExecutionError):
            manager.handle_action(action, self.mock_computer)


class TestUtils(unittest.TestCase):
    """测试工具类"""
    
    def test_operation_logger(self):
        logger = OperationLogger(enabled=False)  # 禁用以避免文件操作
        self.assertFalse(logger.enabled)
        
        # 测试日志记录（不会实际写入文件）
        logger.log_action("test_action", {"arg": "value"}, {"result": "success"})
        logger.log_model_interaction("test query", "test response")
    
    def test_performance_monitor(self):
        monitor = PerformanceMonitor(enabled=True)
        monitor.start_session("test_session")
        
        # 测试记录指标
        monitor.record_metric("test_metric", 1.5, {"unit": "seconds"})
        
        # 测试上下文管理器
        with monitor.time_operation("test_operation"):
            pass
        
        # 获取统计信息
        stats = monitor.get_statistics("test_metric")
        self.assertEqual(stats["count"], 2)  # 一次record_metric，一次time_operation
        
        monitor.end_session()


if __name__ == "__main__":
    unittest.main()
