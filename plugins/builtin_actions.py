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

from typing import Union, Dict, Any, List
from google.genai import types

from ..computers import Computer, EnvState
from ..exceptions import ActionExecutionError, ValidationError
from .base_plugin import ActionPlugin


class BuiltinActionsPlugin(ActionPlugin):
    """内置动作插件，处理所有预定义的浏览器操作"""
    
    # 支持的动作列表
    SUPPORTED_ACTIONS = [
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
    
    def __init__(self):
        super().__init__(
            name="builtin_actions",
            description="Built-in browser actions plugin"
        )
    
    def can_handle(self, action_name: str) -> bool:
        """判断是否可以处理指定的动作"""
        return action_name in self.SUPPORTED_ACTIONS
    
    def execute(self, action: types.FunctionCall, computer: Computer) -> Union[EnvState, Dict[str, Any]]:
        """执行内置动作"""
        try:
            # 验证参数
            if not self.validate_action_args(action):
                raise ValidationError(f"Invalid arguments for action '{action.name}'", action.name, action.args)
            
            # 预处理
            self.pre_execute(action, computer)
            
            # 执行具体动作
            result = self._execute_action(action, computer)
            
            # 后处理
            self.post_execute(action, computer, result)
            
            return result
            
        except Exception as e:
            raise ActionExecutionError(
                f"Failed to execute builtin action '{action.name}': {str(e)}",
                action.name,
                action.args,
                e
            )
    
    def get_supported_actions(self) -> List[str]:
        """获取支持的动作列表"""
        return self.SUPPORTED_ACTIONS.copy()
    
    def validate_action_args(self, action: types.FunctionCall) -> bool:
        """验证动作参数"""
        args = action.args or {}
        
        if action.name == "click_at":
            return "x" in args and "y" in args
        elif action.name == "hover_at":
            return "x" in args and "y" in args
        elif action.name == "type_text_at":
            return "x" in args and "y" in args and "text" in args
        elif action.name == "scroll_document":
            return "direction" in args and args["direction"] in ["up", "down", "left", "right"]
        elif action.name == "scroll_at":
            return "x" in args and "y" in args and "direction" in args
        elif action.name == "navigate":
            return "url" in args
        elif action.name == "key_combination":
            return "keys" in args
        elif action.name == "drag_and_drop":
            return all(key in args for key in ["x", "y", "destination_x", "destination_y"])
        
        # 对于不需要参数的动作，总是返回True
        return True
    
    def _execute_action(self, action: types.FunctionCall, computer: Computer) -> Union[EnvState, Dict[str, Any]]:
        """执行具体的动作"""
        args = action.args or {}
        
        if action.name == "open_web_browser":
            return computer.open_web_browser()
        elif action.name == "click_at":
            x = self._denormalize_x(args["x"], computer)
            y = self._denormalize_y(args["y"], computer)
            return computer.click_at(x=x, y=y)
        elif action.name == "hover_at":
            x = self._denormalize_x(args["x"], computer)
            y = self._denormalize_y(args["y"], computer)
            return computer.hover_at(x=x, y=y)
        elif action.name == "type_text_at":
            x = self._denormalize_x(args["x"], computer)
            y = self._denormalize_y(args["y"], computer)
            press_enter = args.get("press_enter", False)
            clear_before_typing = args.get("clear_before_typing", True)
            return computer.type_text_at(
                x=x,
                y=y,
                text=args["text"],
                press_enter=press_enter,
                clear_before_typing=clear_before_typing,
            )
        elif action.name == "scroll_document":
            return computer.scroll_document(args["direction"])
        elif action.name == "scroll_at":
            x = self._denormalize_x(args["x"], computer)
            y = self._denormalize_y(args["y"], computer)
            magnitude = args.get("magnitude", 800)
            direction = args["direction"]

            if direction in ("up", "down"):
                magnitude = self._denormalize_y(magnitude, computer)
            elif direction in ("left", "right"):
                magnitude = self._denormalize_x(magnitude, computer)
            else:
                raise ValidationError(f"Unknown direction: {direction}", "direction", direction)

            return computer.scroll_at(
                x=x, y=y, direction=direction, magnitude=magnitude
            )
        elif action.name == "wait_5_seconds":
            return computer.wait_5_seconds()
        elif action.name == "go_back":
            return computer.go_back()
        elif action.name == "go_forward":
            return computer.go_forward()
        elif action.name == "search":
            return computer.search()
        elif action.name == "navigate":
            return computer.navigate(args["url"])
        elif action.name == "key_combination":
            return computer.key_combination(args["keys"].split("+"))
        elif action.name == "drag_and_drop":
            x = self._denormalize_x(args["x"], computer)
            y = self._denormalize_y(args["y"], computer)
            destination_x = self._denormalize_x(args["destination_x"], computer)
            destination_y = self._denormalize_y(args["destination_y"], computer)
            return computer.drag_and_drop(
                x=x,
                y=y,
                destination_x=destination_x,
                destination_y=destination_y,
            )
        else:
            raise ValidationError(f"Unknown action: {action.name}", action.name, action.args)
    
    def _denormalize_x(self, x: int, computer: Computer) -> int:
        """将归一化的x坐标转换为屏幕坐标"""
        return int(x / 1000 * computer.screen_size()[0])

    def _denormalize_y(self, y: int, computer: Computer) -> int:
        """将归一化的y坐标转换为屏幕坐标"""
        return int(y / 1000 * computer.screen_size()[1])
