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

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union
from google.genai import types

from ..exceptions import ConfigurationError


class OperationLogger:
    """操作日志记录器"""
    
    def __init__(self, 
                 log_file: str = "browser_agent.log",
                 log_level: str = "INFO",
                 enabled: bool = True,
                 max_file_size: str = "10MB",
                 backup_count: int = 5):
        """
        初始化操作日志记录器
        
        Args:
            log_file: 日志文件路径
            log_level: 日志级别
            enabled: 是否启用日志记录
            max_file_size: 最大文件大小
            backup_count: 备份文件数量
        """
        self.enabled = enabled
        self.log_file = log_file
        self.log_level = log_level
        self.max_file_size = max_file_size
        self.backup_count = backup_count
        
        self.logger = None
        self.session_id = None
        
        if self.enabled:
            self._setup_logger()
    
    def _setup_logger(self):
        """设置日志记录器"""
        self.logger = logging.getLogger("browser_agent")
        self.logger.setLevel(getattr(logging, self.log_level.upper()))
        
        # 避免重复添加处理器
        if self.logger.handlers:
            return
        
        # 创建文件处理器
        file_handler = logging.handlers.RotatingFileHandler(
            self.log_file,
            maxBytes=self._parse_size(self.max_file_size),
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        
        # 设置日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def _parse_size(self, size_str: str) -> int:
        """解析文件大小字符串"""
        size_str = size_str.upper()
        multipliers = {
            'B': 1,
            'KB': 1024,
            'MB': 1024 * 1024,
            'GB': 1024 * 1024 * 1024
        }
        
        for unit, multiplier in multipliers.items():
            if size_str.endswith(unit):
                try:
                    return int(float(size_str[:-len(unit)]) * multiplier)
                except ValueError:
                    raise ConfigurationError(f"Invalid size format: {size_str}")
        
        # 默认假设是字节
        try:
            return int(size_str)
        except ValueError:
            raise ConfigurationError(f"Invalid size format: {size_str}")
    
    def start_session(self, session_id: Optional[str] = None):
        """开始新的会话"""
        if not self.enabled or not self.logger:
            return
        
        self.session_id = session_id or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.logger.info(f"Session started: {self.session_id}")
    
    def log_action(self, 
                   action: Union[str, types.FunctionCall],
                   args: Optional[Dict[str, Any]] = None,
                   result: Optional[Dict[str, Any]] = None,
                   execution_time: Optional[float] = None,
                   success: bool = True,
                   error: Optional[Exception] = None):
        """记录操作日志"""
        if not self.enabled or not self.logger:
            return
        
        timestamp = datetime.now().isoformat()
        
        # 处理不同类型的action参数
        if isinstance(action, types.FunctionCall):
            action_name = action.name
            action_args = action.args or {}
        else:
            action_name = str(action)
            action_args = args or {}
        
        log_entry = {
            "timestamp": timestamp,
            "session_id": self.session_id,
            "action": action_name,
            "args": action_args,
            "result": result,
            "execution_time": execution_time,
            "success": success,
            "error": str(error) if error else None
        }
        
        if success:
            self.logger.info(f"Action executed: {json.dumps(log_entry, ensure_ascii=False)}")
        else:
            self.logger.error(f"Action failed: {json.dumps(log_entry, ensure_ascii=False)}")
    
    def log_model_interaction(self,
                             query: str,
                             response: Optional[str] = None,
                             function_calls: Optional[list] = None,
                             execution_time: Optional[float] = None,
                             success: bool = True,
                             error: Optional[Exception] = None):
        """记录模型交互日志"""
        if not self.enabled or not self.logger:
            return
        
        timestamp = datetime.now().isoformat()
        
        log_entry = {
            "timestamp": timestamp,
            "session_id": self.session_id,
            "type": "model_interaction",
            "query": query,
            "response": response,
            "function_calls": function_calls,
            "execution_time": execution_time,
            "success": success,
            "error": str(error) if error else None
        }
        
        if success:
            self.logger.info(f"Model interaction: {json.dumps(log_entry, ensure_ascii=False)}")
        else:
            self.logger.error(f"Model interaction failed: {json.dumps(log_entry, ensure_ascii=False)}")
    
    def log_state_change(self,
                        url: str,
                        screenshot_size: Optional[int] = None,
                        state_info: Optional[Dict[str, Any]] = None):
        """记录状态变化日志"""
        if not self.enabled or not self.logger:
            return
        
        timestamp = datetime.now().isoformat()
        
        log_entry = {
            "timestamp": timestamp,
            "session_id": self.session_id,
            "type": "state_change",
            "url": url,
            "screenshot_size": screenshot_size,
            "state_info": state_info or {}
        }
        
        self.logger.debug(f"State change: {json.dumps(log_entry, ensure_ascii=False)}")
    
    def log_configuration(self, config: Dict[str, Any]):
        """记录配置信息"""
        if not self.enabled or not self.logger:
            return
        
        timestamp = datetime.now().isoformat()
        
        log_entry = {
            "timestamp": timestamp,
            "session_id": self.session_id,
            "type": "configuration",
            "config": config
        }
        
        self.logger.info(f"Configuration loaded: {json.dumps(log_entry, ensure_ascii=False)}")
    
    def log_performance_metric(self,
                              metric_name: str,
                              value: float,
                              unit: str = "seconds",
                              metadata: Optional[Dict[str, Any]] = None):
        """记录性能指标"""
        if not self.enabled or not self.logger:
            return
        
        timestamp = datetime.now().isoformat()
        
        log_entry = {
            "timestamp": timestamp,
            "session_id": self.session_id,
            "type": "performance_metric",
            "metric_name": metric_name,
            "value": value,
            "unit": unit,
            "metadata": metadata or {}
        }
        
        self.logger.info(f"Performance metric: {json.dumps(log_entry, ensure_ascii=False)}")
    
    def end_session(self, summary: Optional[Dict[str, Any]] = None):
        """结束会话"""
        if not self.enabled or not self.logger:
            return
        
        timestamp = datetime.now().isoformat()
        
        log_entry = {
            "timestamp": timestamp,
            "session_id": self.session_id,
            "type": "session_end",
            "summary": summary or {}
        }
        
        self.logger.info(f"Session ended: {json.dumps(log_entry, ensure_ascii=False)}")
    
    def export_session_logs(self, output_file: Optional[str] = None) -> str:
        """导出会话日志"""
        if not self.enabled or not self.logger:
            return ""
        
        if not output_file:
            output_file = f"{self.session_id}_logs.json" if self.session_id else "session_logs.json"
        
        # 这里简化实现，实际应该从日志文件中提取特定会话的日志
        log_data = {
            "session_id": self.session_id,
            "export_time": datetime.now().isoformat(),
            "log_file": self.log_file,
            "note": "Full logs are available in the main log file"
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)
        
        return output_file


# 全局日志记录器实例
_global_logger: Optional[OperationLogger] = None


def get_logger() -> OperationLogger:
    """获取全局日志记录器实例"""
    global _global_logger
    if _global_logger is None:
        _global_logger = OperationLogger()
    return _global_logger


def set_logger(logger: OperationLogger):
    """设置全局日志记录器实例"""
    global _global_logger
    _global_logger = logger
