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

"""自定义异常体系"""

from typing import Any, Dict, Optional


class BrowserAgentError(Exception):
    """浏览器代理基础异常类"""
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
    
    def __str__(self) -> str:
        error_info = f"[{self.error_code}] " if self.error_code else ""
        return f"{error_info}{self.message}"


class ModelResponseError(BrowserAgentError):
    """模型响应错误"""
    
    def __init__(self, message: str, model_name: Optional[str] = None, response_data: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="MODEL_RESPONSE_ERROR",
            details={
                "model_name": model_name,
                "response_data": response_data or {}
            }
        )
        self.model_name = model_name
        self.response_data = response_data or {}


class ActionExecutionError(BrowserAgentError):
    """动作执行错误"""
    
    def __init__(self, message: str, action_name: Optional[str] = None, action_args: Optional[Dict[str, Any]] = None, original_error: Optional[Exception] = None):
        super().__init__(
            message=message,
            error_code="ACTION_EXECUTION_ERROR",
            details={
                "action_name": action_name,
                "action_args": action_args or {},
                "original_error": str(original_error) if original_error else None
            }
        )
        self.action_name = action_name
        self.action_args = action_args or {}
        self.original_error = original_error


class ConfigurationError(BrowserAgentError):
    """配置错误"""
    
    def __init__(self, message: str, config_key: Optional[str] = None, config_value: Optional[Any] = None):
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            details={
                "config_key": config_key,
                "config_value": config_value
            }
        )
        self.config_key = config_key
        self.config_value = config_value


class PluginError(BrowserAgentError):
    """插件错误"""
    
    def __init__(self, message: str, plugin_name: Optional[str] = None, plugin_type: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="PLUGIN_ERROR",
            details={
                "plugin_name": plugin_name,
                "plugin_type": plugin_type
            }
        )
        self.plugin_name = plugin_name
        self.plugin_type = plugin_type


class ComputerError(BrowserAgentError):
    """计算机环境错误"""
    
    def __init__(self, message: str, computer_type: Optional[str] = None, operation: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="COMPUTER_ERROR",
            details={
                "computer_type": computer_type,
                "operation": operation
            }
        )
        self.computer_type = computer_type
        self.operation = operation


class SafetyError(BrowserAgentError):
    """安全策略错误"""
    
    def __init__(self, message: str, safety_decision: Optional[str] = None, safety_explanation: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="SAFETY_ERROR",
            details={
                "safety_decision": safety_decision,
                "safety_explanation": safety_explanation
            }
        )
        self.safety_decision = safety_decision
        self.safety_explanation = safety_explanation


class NetworkError(BrowserAgentError):
    """网络连接错误"""
    
    def __init__(self, message: str, url: Optional[str] = None, status_code: Optional[int] = None):
        super().__init__(
            message=message,
            error_code="NETWORK_ERROR",
            details={
                "url": url,
                "status_code": status_code
            }
        )
        self.url = url
        self.status_code = status_code


class TimeoutError(BrowserAgentError):
    """超时错误"""
    
    def __init__(self, message: str, timeout_seconds: Optional[float] = None, operation: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="TIMEOUT_ERROR",
            details={
                "timeout_seconds": timeout_seconds,
                "operation": operation
            }
        )
        self.timeout_seconds = timeout_seconds
        self.operation = operation


class ValidationError(BrowserAgentError):
    """数据验证错误"""
    
    def __init__(self, message: str, field_name: Optional[str] = None, field_value: Optional[Any] = None, validation_rule: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details={
                "field_name": field_name,
                "field_value": field_value,
                "validation_rule": validation_rule
            }
        )
        self.field_name = field_name
        self.field_value = field_value
        self.validation_rule = validation_rule


# 向后兼容的异常别名
BrowserAgentTimeoutError = TimeoutError
BrowserAgentNetworkError = NetworkError
BrowserAgentValidationError = ValidationError
