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

from typing import List, Dict, Any, Union
from google.genai import types

from ..computers import Computer, EnvState
from ..exceptions import PluginError, ActionExecutionError
from .base_plugin import ActionPlugin


class PluginManager:
    """插件管理器，负责管理所有动作插件"""
    
    def __init__(self):
        """初始化插件管理器"""
        self.plugins: List[ActionPlugin] = []
        self._plugin_registry: Dict[str, ActionPlugin] = {}
    
    def register_plugin(self, plugin: ActionPlugin):
        """
        注册插件
        
        Args:
            plugin: 要注册的插件
            
        Raises:
            PluginError: 插件注册失败时抛出
        """
        if not isinstance(plugin, ActionPlugin):
            raise PluginError(f"Plugin must be an instance of ActionPlugin, got {type(plugin)}")
        
        if plugin.name in self._plugin_registry:
            raise PluginError(f"Plugin '{plugin.name}' is already registered")
        
        self.plugins.append(plugin)
        self._plugin_registry[plugin.name] = plugin
    
    def unregister_plugin(self, plugin_name: str):
        """
        注销插件
        
        Args:
            plugin_name: 要注销的插件名称
        """
        if plugin_name in self._plugin_registry:
            plugin = self._plugin_registry[plugin_name]
            self.plugins.remove(plugin)
            del self._plugin_registry[plugin_name]
    
    def get_plugin(self, plugin_name: str) -> ActionPlugin:
        """
        获取指定名称的插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            插件实例
            
        Raises:
            PluginError: 插件不存在时抛出
        """
        if plugin_name not in self._plugin_registry:
            raise PluginError(f"Plugin '{plugin_name}' not found")
        
        return self._plugin_registry[plugin_name]
    
    def handle_action(self, action: types.FunctionCall, computer: Computer) -> Union[EnvState, Dict[str, Any]]:
        """
        处理动作，通过插件执行
        
        Args:
            action: 函数调用对象
            computer: 计算机实例
            
        Returns:
            执行结果
            
        Raises:
            ActionExecutionError: 没有找到合适的插件处理动作时抛出
        """
        # 查找可以处理该动作的插件
        for plugin in self.plugins:
            if plugin.can_handle(action.name):
                try:
                    return plugin.execute(action, computer)
                except Exception as e:
                    raise ActionExecutionError(
                        f"Plugin '{plugin.name}' failed to execute action '{action.name}': {str(e)}",
                        action.name,
                        action.args,
                        e
                    )
        
        # 如果没有插件可以处理该动作
        raise ActionExecutionError(
            f"No plugin found to handle action '{action.name}'",
            action.name,
            action.args
        )
    
    def can_handle_action(self, action_name: str) -> bool:
        """
        检查是否有插件可以处理指定的动作
        
        Args:
            action_name: 动作名称
            
        Returns:
            是否有插件可以处理
        """
        return any(plugin.can_handle(action_name) for plugin in self.plugins)
    
    def get_supported_actions(self) -> List[str]:
        """
        获取所有支持的动作列表
        
        Returns:
            支持的动作名称列表
        """
        actions = set()
        for plugin in self.plugins:
            actions.update(plugin.get_supported_actions())
        return list(actions)
    
    def get_plugin_info(self) -> Dict[str, Any]:
        """
        获取所有插件的信息
        
        Returns:
            插件信息字典
        """
        return {
            plugin.name: plugin.get_plugin_info()
            for plugin in self.plugins
        }
    
    def get_plugins_for_action(self, action_name: str) -> List[ActionPlugin]:
        """
        获取可以处理指定动作的所有插件
        
        Args:
            action_name: 动作名称
            
        Returns:
            可以处理该动作的插件列表
        """
        return [plugin for plugin in self.plugins if plugin.can_handle(action_name)]
    
    def validate_all_plugins(self) -> Dict[str, List[str]]:
        """
        验证所有插件
        
        Returns:
            验证结果，键为插件名称，值为错误信息列表
        """
        results = {}
        
        for plugin in self.plugins:
            errors = []
            
            # 检查插件基本信息
            if not plugin.name:
                errors.append("Plugin name is empty")
            
            if not isinstance(plugin.name, str):
                errors.append("Plugin name must be a string")
            
            # 检查支持的动作
            supported_actions = plugin.get_supported_actions()
            if not supported_actions:
                errors.append("Plugin has no supported actions")
            
            # 检查动作处理能力
            for action in supported_actions:
                if not plugin.can_handle(action):
                    errors.append(f"Plugin claims to support '{action}' but can_handle returns False")
            
            if errors:
                results[plugin.name] = errors
        
        return results
    
    def clear_plugins(self):
        """清空所有插件"""
        self.plugins.clear()
        self._plugin_registry.clear()
    
    def reload_plugins(self, plugins: List[ActionPlugin]):
        """
        重新加载插件列表
        
        Args:
            plugins: 新的插件列表
        """
        self.clear_plugins()
        for plugin in plugins:
            self.register_plugin(plugin)
    
    def get_plugin_count(self) -> int:
        """获取插件数量"""
        return len(self.plugins)
    
    def is_empty(self) -> bool:
        """检查是否没有插件"""
        return len(self.plugins) == 0
