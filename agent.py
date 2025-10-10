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

"""
向后兼容性模块 - 保留原有的agent.py作为导入入口

这个文件现在只是一个向后兼容的导入入口，实际的BrowserAgent实现已经移动到agent/目录下。
新的代码应该直接从agent模块导入BrowserAgent。
"""

# 从新的模块化结构中导入BrowserAgent
from agent import BrowserAgent

# 为了保持向后兼容，我们也导出一些可能被外部代码使用的常量和函数
from computers import EnvState, Computer
from typing import Union

# 保持原有的类型别名
FunctionResponseT = Union[EnvState, dict]

# 保持原有的常量（为了向后兼容）
MAX_RECENT_TURN_WITH_SCREENSHOTS = 3
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

# 保持原有的示例函数（为了向后兼容）
def multiply_numbers(x: float, y: float) -> dict:
    """Multiplies two numbers."""
    return {"result": x * y}

# 导出所有需要的内容以保持向后兼容
__all__ = [
    "BrowserAgent",
    "EnvState", 
    "Computer",
    "FunctionResponseT",
    "MAX_RECENT_TURN_WITH_SCREENSHOTS",
    "PREDEFINED_COMPUTER_USE_FUNCTIONS",
    "multiply_numbers",
]