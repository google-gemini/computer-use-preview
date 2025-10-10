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
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ModelConfig:
    """模型配置类"""
    name: str = "gemini-2.5-computer-use-preview-10-2025"
    temperature: float = 1.0
    top_p: float = 0.95
    top_k: int = 40
    max_output_tokens: int = 8192


@dataclass
class BrowserConfig:
    """浏览器配置类"""
    screen_size: Tuple[int, int] = (1440, 900)
    wait_timeout: int = 30000
    max_retries: int = 5
    base_delay_s: int = 1
    max_recent_turns_with_screenshots: int = 3


@dataclass
class PlaywrightConfig:
    """Playwright配置类"""
    headless: bool = False
    highlight_mouse: bool = False
    initial_url: str = "https://www.google.com"
    search_engine_url: str = "https://www.google.com"


@dataclass
class BrowserbaseConfig:
    """Browserbase配置类"""
    initial_url: str = "https://www.google.com"
    fingerprint: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.fingerprint is None:
            self.fingerprint = {
                "screen": {
                    "maxWidth": 1920,
                    "maxHeight": 1080,
                    "minWidth": 1024,
                    "minHeight": 768,
                }
            }


@dataclass
class LoggingConfig:
    """日志配置类"""
    enabled: bool = True
    level: str = "INFO"
    log_file: str = "browser_agent.log"
    max_file_size: str = "10MB"
    backup_count: int = 5


@dataclass
class PerformanceConfig:
    """性能监控配置类"""
    enabled: bool = True
    metrics_file: str = "performance_metrics.json"
    track_screenshot_time: bool = True
    track_model_response_time: bool = True
    track_action_execution_time: bool = True


class Config:
    """配置管理类"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件路径，如果为None则使用默认配置
        """
        self.config_file = config_file
        self._config_data = self._load_config()
        
        # 初始化各个配置模块
        self.model = ModelConfig(**self._config_data.get("model", {}))
        self.browser = BrowserConfig(**self._config_data.get("browser", {}))
        self.playwright = PlaywrightConfig(**self._config_data.get("playwright", {}))
        self.browserbase = BrowserbaseConfig(**self._config_data.get("browserbase", {}))
        self.logging = LoggingConfig(**self._config_data.get("logging", {}))
        self.performance = PerformanceConfig(**self._config_data.get("performance", {}))
        
        # 应用环境变量覆盖
        self._apply_env_overrides()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if self.config_file and os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        
        # 尝试加载默认配置文件
        default_config_path = Path(__file__).parent / "default_config.yaml"
        if default_config_path.exists():
            with open(default_config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        
        # 如果都没有，返回空配置
        return {}
    
    def _apply_env_overrides(self):
        """应用环境变量覆盖"""
        # 模型配置覆盖
        if os.environ.get("GEMINI_API_KEY"):
            # API key通过环境变量管理
            pass
        
        if os.environ.get("USE_VERTEXAI", "0").lower() in ["true", "1"]:
            # Vertex AI相关配置
            pass
        
        # Playwright配置覆盖
        if os.environ.get("PLAYWRIGHT_HEADLESS"):
            self.playwright.headless = os.environ.get("PLAYWRIGHT_HEADLESS", "false").lower() == "true"
        
        # Browserbase配置覆盖
        if os.environ.get("BROWSERBASE_API_KEY"):
            # Browserbase API key通过环境变量管理
            pass
        
        if os.environ.get("BROWSERBASE_PROJECT_ID"):
            # Browserbase Project ID通过环境变量管理
            pass
    
    def get_model_config(self) -> Dict[str, Any]:
        """获取模型配置字典"""
        return {
            "model_name": self.model.name,
            "temperature": self.model.temperature,
            "top_p": self.model.top_p,
            "top_k": self.model.top_k,
            "max_output_tokens": self.model.max_output_tokens,
        }
    
    def get_browser_config(self) -> Dict[str, Any]:
        """获取浏览器配置字典"""
        return {
            "screen_size": self.browser.screen_size,
            "wait_timeout": self.browser.wait_timeout,
            "max_retries": self.browser.max_retries,
            "base_delay_s": self.browser.base_delay_s,
            "max_recent_turns_with_screenshots": self.browser.max_recent_turns_with_screenshots,
        }
    
    def get_playwright_config(self) -> Dict[str, Any]:
        """获取Playwright配置字典"""
        return {
            "screen_size": self.browser.screen_size,
            "initial_url": self.playwright.initial_url,
            "highlight_mouse": self.playwright.highlight_mouse,
            "search_engine_url": self.playwright.search_engine_url,
        }
    
    def get_browserbase_config(self) -> Dict[str, Any]:
        """获取Browserbase配置字典"""
        return {
            "screen_size": self.browser.screen_size,
            "initial_url": self.browserbase.initial_url,
            "fingerprint": self.browserbase.fingerprint,
        }
    
    def get_logging_config(self) -> Dict[str, Any]:
        """获取日志配置字典"""
        return {
            "enabled": self.logging.enabled,
            "level": self.logging.level,
            "log_file": self.logging.log_file,
            "max_file_size": self.logging.max_file_size,
            "backup_count": self.logging.backup_count,
        }
    
    def get_performance_config(self) -> Dict[str, Any]:
        """获取性能监控配置字典"""
        return {
            "enabled": self.performance.enabled,
            "metrics_file": self.performance.metrics_file,
            "track_screenshot_time": self.performance.track_screenshot_time,
            "track_model_response_time": self.performance.track_model_response_time,
            "track_action_execution_time": self.performance.track_action_execution_time,
        }
    
    def reload(self):
        """重新加载配置"""
        self._config_data = self._load_config()
        self._apply_env_overrides()
    
    def save(self, file_path: str):
        """保存当前配置到文件"""
        config_dict = {
            "model": {
                "name": self.model.name,
                "temperature": self.model.temperature,
                "top_p": self.model.top_p,
                "top_k": self.model.top_k,
                "max_output_tokens": self.model.max_output_tokens,
            },
            "browser": {
                "screen_size": list(self.browser.screen_size),
                "wait_timeout": self.browser.wait_timeout,
                "max_retries": self.browser.max_retries,
                "base_delay_s": self.browser.base_delay_s,
                "max_recent_turns_with_screenshots": self.browser.max_recent_turns_with_screenshots,
            },
            "playwright": {
                "headless": self.playwright.headless,
                "highlight_mouse": self.playwright.highlight_mouse,
                "initial_url": self.playwright.initial_url,
                "search_engine_url": self.playwright.search_engine_url,
            },
            "browserbase": {
                "initial_url": self.browserbase.initial_url,
                "fingerprint": self.browserbase.fingerprint,
            },
            "logging": {
                "enabled": self.logging.enabled,
                "level": self.logging.level,
                "log_file": self.logging.log_file,
                "max_file_size": self.logging.max_file_size,
                "backup_count": self.logging.backup_count,
            },
            "performance": {
                "enabled": self.performance.enabled,
                "metrics_file": self.performance.metrics_file,
                "track_screenshot_time": self.performance.track_screenshot_time,
                "track_model_response_time": self.performance.track_model_response_time,
                "track_action_execution_time": self.performance.track_action_execution_time,
            },
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)


# 全局配置实例
_global_config: Optional[Config] = None


def get_config(config_file: Optional[str] = None) -> Config:
    """获取全局配置实例"""
    global _global_config
    if _global_config is None:
        _global_config = Config(config_file)
    return _global_config


def reload_config():
    """重新加载全局配置"""
    global _global_config
    if _global_config is not None:
        _global_config.reload()
