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
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from contextlib import contextmanager
from collections import defaultdict, deque


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self,
                 enabled: bool = True,
                 metrics_file: str = "performance_metrics.json",
                 track_screenshot_time: bool = True,
                 track_model_response_time: bool = True,
                 track_action_execution_time: bool = True,
                 max_history_size: int = 1000):
        """
        初始化性能监控器
        
        Args:
            enabled: 是否启用性能监控
            metrics_file: 性能指标文件路径
            track_screenshot_time: 是否跟踪截图时间
            track_model_response_time: 是否跟踪模型响应时间
            track_action_execution_time: 是否跟踪动作执行时间
            max_history_size: 最大历史记录数量
        """
        self.enabled = enabled
        self.metrics_file = metrics_file
        self.track_screenshot_time = track_screenshot_time
        self.track_model_response_time = track_model_response_time
        self.track_action_execution_time = track_action_execution_time
        self.max_history_size = max_history_size
        
        # 性能指标存储
        self.metrics: Dict[str, List[float]] = defaultdict(list)
        self.metadata: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.session_metrics: Dict[str, Any] = {}
        
        # 会话信息
        self.session_id = None
        self.session_start_time = None
        
        # 当前正在跟踪的操作
        self.active_timings: Dict[str, float] = {}
    
    def start_session(self, session_id: Optional[str] = None):
        """开始新的性能监控会话"""
        if not self.enabled:
            return
        
        self.session_id = session_id or f"perf_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.session_start_time = time.time()
        
        self.session_metrics = {
            "session_id": self.session_id,
            "start_time": self.session_start_time,
            "total_actions": 0,
            "total_model_calls": 0,
            "total_screenshots": 0,
            "errors": 0
        }
    
    def end_session(self):
        """结束性能监控会话"""
        if not self.enabled or not self.session_start_time:
            return
        
        end_time = time.time()
        duration = end_time - self.session_start_time
        
        self.session_metrics.update({
            "end_time": end_time,
            "duration": duration,
            "average_action_time": self._calculate_average("action_execution"),
            "average_model_response_time": self._calculate_average("model_response"),
            "average_screenshot_time": self._calculate_average("screenshot"),
            "total_actions": len(self.metrics.get("action_execution", [])),
            "total_model_calls": len(self.metrics.get("model_response", [])),
            "total_screenshots": len(self.metrics.get("screenshot", []))
        })
        
        # 保存会话总结
        self._save_session_summary()
    
    @contextmanager
    def time_operation(self, operation_name: str, metadata: Optional[Dict[str, Any]] = None):
        """上下文管理器，用于计时操作"""
        if not self.enabled:
            yield
            return
        
        start_time = time.time()
        self.active_timings[operation_name] = start_time
        
        try:
            yield
        finally:
            end_time = time.time()
            duration = end_time - start_time
            
            self._record_metric(operation_name, duration, metadata)
            self.active_timings.pop(operation_name, None)
    
    def record_metric(self, 
                     metric_name: str, 
                     value: float, 
                     metadata: Optional[Dict[str, Any]] = None):
        """记录性能指标"""
        if not self.enabled:
            return
        
        self._record_metric(metric_name, value, metadata)
    
    def _record_metric(self, 
                      metric_name: str, 
                      value: float, 
                      metadata: Optional[Dict[str, Any]] = None):
        """内部方法：记录性能指标"""
        # 添加到指标列表
        self.metrics[metric_name].append(value)
        
        # 添加到元数据列表
        metric_metadata = {
            "timestamp": time.time(),
            "session_id": self.session_id,
            "value": value
        }
        if metadata:
            metric_metadata.update(metadata)
        
        self.metadata[metric_name].append(metric_metadata)
        
        # 限制历史记录大小
        if len(self.metrics[metric_name]) > self.max_history_size:
            self.metrics[metric_name] = self.metrics[metric_name][-self.max_history_size:]
            self.metadata[metric_name] = self.metadata[metric_name][-self.max_history_size:]
        
        # 更新会话统计
        if metric_name == "action_execution":
            self.session_metrics["total_actions"] += 1
        elif metric_name == "model_response":
            self.session_metrics["total_model_calls"] += 1
        elif metric_name == "screenshot":
            self.session_metrics["total_screenshots"] += 1
        elif metric_name.endswith("_error"):
            self.session_metrics["errors"] += 1
    
    def get_statistics(self, metric_name: str) -> Dict[str, float]:
        """获取特定指标的统计信息"""
        if metric_name not in self.metrics or not self.metrics[metric_name]:
            return {}
        
        values = self.metrics[metric_name]
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "mean": sum(values) / len(values),
            "median": sorted(values)[len(values) // 2],
            "p95": sorted(values)[int(len(values) * 0.95)] if len(values) > 20 else max(values),
            "p99": sorted(values)[int(len(values) * 0.99)] if len(values) > 100 else max(values)
        }
    
    def get_all_statistics(self) -> Dict[str, Dict[str, float]]:
        """获取所有指标的统计信息"""
        return {
            metric_name: self.get_statistics(metric_name)
            for metric_name in self.metrics.keys()
        }
    
    def _calculate_average(self, metric_name: str) -> float:
        """计算平均值"""
        if metric_name not in self.metrics or not self.metrics[metric_name]:
            return 0.0
        return sum(self.metrics[metric_name]) / len(self.metrics[metric_name])
    
    def get_session_summary(self) -> Dict[str, Any]:
        """获取会话总结"""
        if not self.enabled or not self.session_metrics:
            return {}
        
        summary = self.session_metrics.copy()
        summary.update({
            "statistics": self.get_all_statistics(),
            "current_active_operations": list(self.active_timings.keys())
        })
        
        return summary
    
    def _save_session_summary(self):
        """保存会话总结到文件"""
        if not self.enabled:
            return
        
        summary = self.get_session_summary()
        
        # 确保目录存在
        metrics_path = Path(self.metrics_file)
        metrics_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 保存到文件
        with open(self.metrics_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
    
    def export_metrics(self, output_file: Optional[str] = None) -> str:
        """导出性能指标"""
        if not self.enabled:
            return ""
        
        if not output_file:
            output_file = f"{self.session_id}_metrics.json" if self.session_id else "performance_metrics_export.json"
        
        export_data = {
            "session_summary": self.get_session_summary(),
            "detailed_metrics": {
                metric_name: {
                    "values": self.metrics[metric_name],
                    "metadata": self.metadata[metric_name]
                }
                for metric_name in self.metrics.keys()
            },
            "export_time": datetime.now().isoformat()
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        return output_file
    
    def reset(self):
        """重置性能监控器"""
        if not self.enabled:
            return
        
        self.metrics.clear()
        self.metadata.clear()
        self.session_metrics.clear()
        self.active_timings.clear()
        self.session_id = None
        self.session_start_time = None
    
    def is_tracking(self, operation_name: str) -> bool:
        """检查是否正在跟踪某个操作"""
        return operation_name in self.active_timings
    
    def get_current_operation_time(self, operation_name: str) -> float:
        """获取当前操作的运行时间"""
        if operation_name not in self.active_timings:
            return 0.0
        return time.time() - self.active_timings[operation_name]


# 全局性能监控器实例
_global_monitor: Optional[PerformanceMonitor] = None


def get_performance_monitor() -> PerformanceMonitor:
    """获取全局性能监控器实例"""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = PerformanceMonitor()
    return _global_monitor


def set_performance_monitor(monitor: PerformanceMonitor):
    """设置全局性能监控器实例"""
    global _global_monitor
    _global_monitor = monitor
