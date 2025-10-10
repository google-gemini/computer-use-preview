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

from abc import ABC, abstractmethod
from typing import Union, Dict, Any, List
from google.genai import types

from ..computers import Computer, EnvState


class ActionPlugin(ABC):
    """动作插件基类"""
    
    def __init__(self, name: str, description: str = ""):
        """
        初始化动作插件
        
        Args:
            name: 插件名称
            description: 插件描述
        """
        self.name = name
        self.description = description
    
    @abstractmethod
    def can_handle(self, action_name: str) -> bool:
        """
        判断是否可以处理指定的动作
        
        Args:
            action_name: 动作名称
            
        Returns:
            是否可以处理
        """
        pass
    
    @abstractmethod
    def execute(self, action: types.FunctionCall, computer: Computer) -> Union[EnvState, Dict[str, Any]]:
        """
        执行动作
        
        Args:
            action: 函数调用对象
            computer: 计算机实例
            
        Returns:
            环境状态或自定义结果
        """
        pass
    
    def get_supported_actions(self) -> List[str]:
        """
        获取支持的动作列表
        
        Returns:
            支持的动作名称列表
        """
        return []
    
    def get_plugin_info(self) -> Dict[str, Any]:
        """
        获取插件信息
        
        Returns:
            插件信息字典
        """
        return {
            "name": self.name,
            "description": self.description,
            "supported_actions": self.get_supported_actions()
        }
    
    def validate_action_args(self, action: types.FunctionCall) -> bool:
        """
        验证动作参数
        
        Args:
            action: 函数调用对象
            
        Returns:
            参数是否有效
        """
        return True
    
    def pre_execute(self, action: types.FunctionCall, computer: Computer) -> None:
        """
        动作执行前的预处理
        
        Args:
            action: 函数调用对象
            computer: 计算机实例
        """
        pass
    
    def post_execute(self, action: types.FunctionCall, computer: Computer, result: Union[EnvState, Dict[str, Any]]) -> None:
        """
        动作执行后的后处理
        
        Args:
            action: 函数调用对象
            computer: 计算机实例
            result: 执行结果
        """
        pass
