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

from typing import List
from google.genai.types import Content, Part, FunctionResponse
from google.genai import types

from ..config import get_config


class ConversationManager:
    """对话历史管理器，负责管理AI对话历史和截图清理"""
    
    # 预定义的计算机使用函数列表
    PREDEFINED_COMPUTER_USE_FUNCTIONS = [
        "open_web_browser",
        "click_at",
        "hover_at",
        "type_text_at",
        "scroll_document",
        "scroll_at",
        "wait_5_seconds",
        "go_back",
        "go_forward",
        "search",
        "navigate",
        "key_combination",
        "drag_and_drop",
    ]
    
    def __init__(self, initial_query: str, max_recent_turns_with_screenshots: int = None):
        """
        初始化对话管理器
        
        Args:
            initial_query: 初始用户查询
            max_recent_turns_with_screenshots: 最大保留截图的历史轮数
        """
        self._contents: List[Content] = [
            Content(
                role="user",
                parts=[
                    Part(text=initial_query),
                ],
            )
        ]
        
        # 从配置获取最大轮数，如果没有则使用默认值
        config = get_config()
        self.max_recent_turns_with_screenshots = (
            max_recent_turns_with_screenshots or 
            config.browser.max_recent_turns_with_screenshots
        )
    
    def add_model_response(self, content: Content):
        """
        添加模型响应到对话历史
        
        Args:
            content: 模型响应内容
        """
        self._contents.append(content)
    
    def add_function_responses(self, function_responses: List[FunctionResponse]):
        """
        添加函数响应到对话历史
        
        Args:
            function_responses: 函数响应列表
        """
        self._contents.append(
            Content(
                role="user",
                parts=[Part(function_response=fr) for fr in function_responses],
            )
        )
    
    def get_contents(self) -> List[Content]:
        """获取当前对话内容"""
        return self._contents
    
    def cleanup_old_screenshots(self):
        """清理旧的截图，只保留最近的几个轮次"""
        turn_with_screenshots_found = 0
        
        for content in reversed(self._contents):
            if content.role == "user" and content.parts:
                # 检查内容是否有预定义计算机使用函数的截图
                has_screenshot = False
                for part in content.parts:
                    if (
                        part.function_response
                        and part.function_response.parts
                        and part.function_response.name in self.PREDEFINED_COMPUTER_USE_FUNCTIONS
                    ):
                        has_screenshot = True
                        break

                if has_screenshot:
                    turn_with_screenshots_found += 1
                    # 如果截图数量超过限制，移除截图图像
                    if turn_with_screenshots_found > self.max_recent_turns_with_screenshots:
                        for part in content.parts:
                            if (
                                part.function_response
                                and part.function_response.parts
                                and part.function_response.name in self.PREDEFINED_COMPUTER_USE_FUNCTIONS
                            ):
                                part.function_response.parts = None
    
    def get_conversation_summary(self) -> dict:
        """获取对话摘要"""
        total_turns = len(self._contents)
        user_turns = sum(1 for content in self._contents if content.role == "user")
        model_turns = sum(1 for content in self._contents if content.role == "model")
        
        # 统计函数调用数量
        function_calls = 0
        for content in self._contents:
            if content.parts:
                for part in content.parts:
                    if part.function_call:
                        function_calls += 1
        
        return {
            "total_turns": total_turns,
            "user_turns": user_turns,
            "model_turns": model_turns,
            "function_calls": function_calls,
            "max_recent_turns_with_screenshots": self.max_recent_turns_with_screenshots
        }
    
    def clear_conversation(self):
        """清空对话历史"""
        self._contents.clear()
    
    def export_conversation(self) -> dict:
        """导出对话内容（用于调试）"""
        conversation_data = []
        
        for i, content in enumerate(self._contents):
            turn_data = {
                "turn": i + 1,
                "role": content.role,
                "parts": []
            }
            
            if content.parts:
                for part in content.parts:
                    part_data = {}
                    if part.text:
                        part_data["text"] = part.text
                    if part.function_call:
                        part_data["function_call"] = {
                            "name": part.function_call.name,
                            "args": part.function_call.args
                        }
                    if part.function_response:
                        part_data["function_response"] = {
                            "name": part.function_response.name,
                            "response": part.function_response.response,
                            "has_parts": bool(part.function_response.parts)
                        }
                    turn_data["parts"].append(part_data)
            
            conversation_data.append(turn_data)
        
        return {
            "conversation": conversation_data,
            "summary": self.get_conversation_summary()
        }
