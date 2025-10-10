#!/usr/bin/env python3
"""
演示新功能的脚本

这个脚本展示了重构后的Computer Use Preview项目的新功能：
1. 配置管理系统
2. 自定义异常体系
3. 操作日志和性能监控
4. 插件化动作系统
5. 模块化架构
"""

import os
import time
from typing import Dict, Any

# 设置测试环境变量
os.environ["GEMINI_API_KEY"] = "demo_key"

def demo_config_system():
    """演示配置系统"""
    print("=== 配置系统演示 ===")
    
    from config import get_config, Config
    
    # 获取默认配置
    config = get_config()
    print(f"模型名称: {config.model.name}")
    print(f"温度参数: {config.model.temperature}")
    print(f"屏幕大小: {config.browser.screen_size}")
    print(f"最大重试次数: {config.browser.max_retries}")
    
    # 获取配置字典
    model_config = config.get_model_config()
    print(f"模型配置字典: {model_config}")
    
    print()

def demo_exception_system():
    """演示异常系统"""
    print("=== 异常系统演示 ===")
    
    from exceptions import (
        BrowserAgentError, 
        ModelResponseError, 
        ActionExecutionError,
        ConfigurationError,
        PluginError
    )
    
    # 演示不同类型的异常
    try:
        raise ModelResponseError("模型响应超时", "gemini-model", {"timeout": 30})
    except ModelResponseError as e:
        print(f"捕获模型响应错误: {e}")
        print(f"错误代码: {e.error_code}")
        print(f"模型名称: {e.model_name}")
    
    try:
        raise ActionExecutionError("点击操作失败", "click_at", {"x": 100, "y": 200})
    except ActionExecutionError as e:
        print(f"捕获动作执行错误: {e}")
        print(f"动作名称: {e.action_name}")
        print(f"动作参数: {e.action_args}")
    
    print()

def demo_logging_and_monitoring():
    """演示日志和监控系统"""
    print("=== 日志和监控系统演示 ===")
    
    from utils import OperationLogger, PerformanceMonitor
    
    # 演示操作日志记录器
    logger = OperationLogger(enabled=False)  # 禁用以避免文件操作
    logger.start_session("demo_session")
    
    logger.log_action("click_at", {"x": 100, "y": 200}, {"success": True})
    logger.log_model_interaction("搜索Python教程", "正在执行搜索...")
    logger.log_performance_metric("response_time", 1.5, "seconds")
    
    print("操作日志记录完成")
    
    # 演示性能监控器
    monitor = PerformanceMonitor(enabled=True)
    monitor.start_session("demo_perf_session")
    
    # 使用上下文管理器计时
    with monitor.time_operation("demo_operation"):
        time.sleep(0.1)  # 模拟操作
    
    # 记录指标
    monitor.record_metric("custom_metric", 2.5, {"unit": "seconds"})
    
    # 获取统计信息
    stats = monitor.get_statistics("demo_operation")
    print(f"操作统计: {stats}")
    
    monitor.end_session()
    print()

def demo_plugin_system():
    """演示插件系统"""
    print("=== 插件系统演示 ===")
    
    from plugins import PluginManager, BuiltinActionsPlugin
    from google.genai import types
    from unittest.mock import MagicMock
    
    # 创建插件管理器
    manager = PluginManager()
    
    # 注册内置动作插件
    builtin_plugin = BuiltinActionsPlugin()
    manager.register_plugin(builtin_plugin)
    
    print(f"已注册插件: {manager.get_plugin_count()}")
    print(f"支持的動作: {manager.get_supported_actions()[:5]}...")  # 显示前5个
    
    # 模拟计算机实例
    mock_computer = MagicMock()
    mock_computer.screen_size.return_value = (1000, 1000)
    
    # 演示动作处理
    action = types.FunctionCall(name="open_web_browser", args={})
    print(f"可以处理动作 '{action.name}': {manager.can_handle_action(action.name)}")
    
    # 获取插件信息
    plugin_info = manager.get_plugin_info()
    print(f"插件信息: {list(plugin_info.keys())}")
    
    print()

def demo_modular_architecture():
    """演示模块化架构"""
    print("=== 模块化架构演示 ===")
    
    from agent import BrowserAgent
    from agent.conversation_manager import ConversationManager
    from agent.action_handler import ActionHandler
    from agent.response_processor import ResponseProcessor
    
    print("成功导入模块化组件:")
    print(f"- BrowserAgent: {BrowserAgent}")
    print(f"- ConversationManager: {ConversationManager}")
    print(f"- ActionHandler: {ActionHandler}")
    print(f"- ResponseProcessor: {ResponseProcessor}")
    
    # 演示对话管理器
    conv_manager = ConversationManager("测试查询")
    print(f"对话管理器初始化完成，初始查询: '{conv_manager.get_contents()[0].parts[0].text}'")
    
    # 演示响应处理器
    response_processor = ResponseProcessor()
    print("响应处理器初始化完成")
    
    print()

def demo_backward_compatibility():
    """演示向后兼容性"""
    print("=== 向后兼容性演示 ===")
    
    # 演示可以从旧的agent.py导入
    from agent import BrowserAgent, multiply_numbers, PREDEFINED_COMPUTER_USE_FUNCTIONS
    
    print("成功从agent模块导入:")
    print(f"- BrowserAgent: {BrowserAgent}")
    print(f"- multiply_numbers函数: {multiply_numbers(2, 3)}")
    print(f"- 预定义函数数量: {len(PREDEFINED_COMPUTER_USE_FUNCTIONS)}")
    
    print()

def main():
    """主演示函数"""
    print("Computer Use Preview - 新功能演示")
    print("=" * 50)
    
    try:
        demo_config_system()
        demo_exception_system()
        demo_logging_and_monitoring()
        demo_plugin_system()
        demo_modular_architecture()
        demo_backward_compatibility()
        
        print("所有演示完成！")
        print("\n新功能总结:")
        print("✅ 配置管理系统 - 支持YAML配置和环境变量")
        print("✅ 自定义异常体系 - 更精确的错误处理")
        print("✅ 操作日志和性能监控 - 完整的可观测性")
        print("✅ 插件化动作系统 - 可扩展的架构")
        print("✅ 模块化架构 - 更好的代码组织")
        print("✅ 向后兼容性 - 保持现有API不变")
        
    except Exception as e:
        print(f"演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
