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

from typing import Union, Any
from google.genai import types

from ..computers import Computer, EnvState
from ..exceptions import ActionExecutionError


class ActionHandler:
    """动作处理器，负责处理AI返回的函数调用"""
    
    def __init__(self, browser_computer: Computer):
        """
        初始化动作处理器
        
        Args:
            browser_computer: 浏览器计算机实例
        """
        self._browser_computer = browser_computer
    
    def handle_action(self, action: types.FunctionCall) -> Union[EnvState, dict]:
        """
        处理动作并返回环境状态
        
        Args:
            action: AI返回的函数调用
            
        Returns:
            环境状态或自定义函数结果
            
        Raises:
            ActionExecutionError: 动作执行失败时抛出
        """
        try:
            if action.name == "open_web_browser":
                return self._browser_computer.open_web_browser()
            elif action.name == "click_at":
                x = self._denormalize_x(action.args["x"])
                y = self._denormalize_y(action.args["y"])
                return self._browser_computer.click_at(x=x, y=y)
            elif action.name == "hover_at":
                x = self._denormalize_x(action.args["x"])
                y = self._denormalize_y(action.args["y"])
                return self._browser_computer.hover_at(x=x, y=y)
            elif action.name == "type_text_at":
                x = self._denormalize_x(action.args["x"])
                y = self._denormalize_y(action.args["y"])
                press_enter = action.args.get("press_enter", False)
                clear_before_typing = action.args.get("clear_before_typing", True)
                return self._browser_computer.type_text_at(
                    x=x,
                    y=y,
                    text=action.args["text"],
                    press_enter=press_enter,
                    clear_before_typing=clear_before_typing,
                )
            elif action.name == "scroll_document":
                return self._browser_computer.scroll_document(action.args["direction"])
            elif action.name == "scroll_at":
                x = self._denormalize_x(action.args["x"])
                y = self._denormalize_y(action.args["y"])
                magnitude = action.args.get("magnitude", 800)
                direction = action.args["direction"]

                if direction in ("up", "down"):
                    magnitude = self._denormalize_y(magnitude)
                elif direction in ("left", "right"):
                    magnitude = self._denormalize_x(magnitude)
                else:
                    raise ActionExecutionError(f"Unknown direction: {direction}", "scroll_at", action.args)

                return self._browser_computer.scroll_at(
                    x=x, y=y, direction=direction, magnitude=magnitude
                )
            elif action.name == "wait_5_seconds":
                return self._browser_computer.wait_5_seconds()
            elif action.name == "go_back":
                return self._browser_computer.go_back()
            elif action.name == "go_forward":
                return self._browser_computer.go_forward()
            elif action.name == "search":
                return self._browser_computer.search()
            elif action.name == "navigate":
                return self._browser_computer.navigate(action.args["url"])
            elif action.name == "key_combination":
                return self._browser_computer.key_combination(
                    action.args["keys"].split("+")
                )
            elif action.name == "drag_and_drop":
                x = self._denormalize_x(action.args["x"])
                y = self._denormalize_y(action.args["y"])
                destination_x = self._denormalize_x(action.args["destination_x"])
                destination_y = self._denormalize_y(action.args["destination_y"])
                return self._browser_computer.drag_and_drop(
                    x=x,
                    y=y,
                    destination_x=destination_x,
                    destination_y=destination_y,
                )
            else:
                raise ActionExecutionError(f"Unsupported function: {action.name}", action.name, action.args)
                
        except Exception as e:
            raise ActionExecutionError(
                f"Failed to execute action '{action.name}': {str(e)}",
                action.name,
                action.args,
                e
            )
    
    def _denormalize_x(self, x: int) -> int:
        """将归一化的x坐标转换为屏幕坐标"""
        return int(x / 1000 * self._browser_computer.screen_size()[0])

    def _denormalize_y(self, y: int) -> int:
        """将归一化的y坐标转换为屏幕坐标"""
        return int(y / 1000 * self._browser_computer.screen_size()[1])
