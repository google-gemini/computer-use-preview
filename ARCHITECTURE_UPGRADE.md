# Computer Use Preview - 架构升级说明

## 概述

本次升级对Computer Use Preview项目进行了全面的架构优化，在保持向后兼容的前提下，引入了配置管理、插件系统、模块化架构等现代化特性。

## 🚀 新功能特性

### 1. 配置管理系统
- **YAML配置文件支持**: 使用`config/default_config.yaml`管理所有配置
- **环境变量覆盖**: 支持通过环境变量覆盖配置
- **类型安全**: 使用Pydantic确保配置类型安全
- **配置验证**: 自动验证配置项的有效性

### 2. 自定义异常体系
- **精确错误分类**: `ModelResponseError`, `ActionExecutionError`, `ConfigurationError`等
- **详细错误信息**: 包含错误代码、上下文信息和原始异常
- **调试友好**: 提供更清晰的错误堆栈和调试信息

### 3. 操作日志和性能监控
- **结构化日志**: JSON格式的操作日志，便于分析
- **性能指标**: 自动记录响应时间、执行时间等关键指标
- **会话跟踪**: 完整的会话生命周期记录
- **可配置输出**: 支持文件和控制台输出

### 4. 插件化动作系统
- **可扩展架构**: 支持自定义动作插件
- **内置插件**: 预定义浏览器操作作为插件
- **插件管理**: 动态注册、注销和验证插件
- **类型安全**: 强类型的插件接口

### 5. 模块化架构
- **职责分离**: 将大型文件拆分为专门模块
- **松耦合设计**: 各模块独立，便于测试和维护
- **清晰接口**: 明确的模块间通信协议

## 📁 新的文件结构

```
computer-use-preview/
├── agent/                    # 代理模块
│   ├── __init__.py
│   ├── browser_agent.py     # 主代理类
│   ├── action_handler.py    # 动作处理器
│   ├── conversation_manager.py # 对话管理器
│   └── response_processor.py   # 响应处理器
├── config/                   # 配置模块
│   ├── __init__.py
│   ├── config.py           # 配置管理类
│   └── default_config.yaml # 默认配置文件
├── plugins/                  # 插件模块
│   ├── __init__.py
│   ├── base_plugin.py      # 插件基类
│   ├── builtin_actions.py  # 内置动作插件
│   └── plugin_manager.py   # 插件管理器
├── utils/                    # 工具模块
│   ├── __init__.py
│   ├── logger.py           # 日志记录器
│   └── performance_monitor.py # 性能监控器
├── exceptions.py            # 自定义异常
├── agent.py                # 向后兼容入口
├── main.py                 # 更新后的主程序
└── demo_new_features.py    # 新功能演示
```

## 🔧 使用方法

### 基本使用（向后兼容）
```python
# 原有代码无需修改
from agent import BrowserAgent
from computers import PlaywrightComputer

with PlaywrightComputer() as computer:
    agent = BrowserAgent(computer, "搜索Python教程")
    agent.agent_loop()
```

### 使用配置系统
```python
from config import get_config

# 获取配置
config = get_config()
print(f"模型: {config.model.name}")
print(f"屏幕大小: {config.browser.screen_size}")

# 使用自定义配置文件
config = get_config("custom_config.yaml")
```

### 使用插件系统
```python
from plugins import PluginManager, BuiltinActionsPlugin

# 创建插件管理器
manager = PluginManager()
manager.register_plugin(BuiltinActionsPlugin())

# 处理动作
action = FunctionCall(name="click_at", args={"x": 100, "y": 200})
result = manager.handle_action(action, computer)
```

### 使用日志和监控
```python
from utils import get_logger, get_performance_monitor

# 获取日志记录器
logger = get_logger()
logger.start_session("my_session")
logger.log_action("click_at", {"x": 100, "y": 200}, {"success": True})

# 获取性能监控器
monitor = get_performance_monitor()
monitor.start_session("my_session")
with monitor.time_operation("my_operation"):
    # 执行操作
    pass
```

## ⚙️ 配置选项

### 模型配置
```yaml
model:
  name: "gemini-2.5-computer-use-preview-10-2025"
  temperature: 1.0
  top_p: 0.95
  max_output_tokens: 8192
```

### 浏览器配置
```yaml
browser:
  screen_size: [1440, 900]
  wait_timeout: 30000
  max_retries: 5
```

### 日志配置
```yaml
logging:
  enabled: true
  level: "INFO"
  log_file: "browser_agent.log"
  max_file_size: "10MB"
```

## 🧪 测试

运行所有测试：
```bash
python -m pytest test_agent.py test_main.py -v
```

运行新功能演示：
```bash
python demo_new_features.py
```

## 🔄 迁移指南

### 对于现有用户
- **无需修改代码**: 所有现有代码继续工作
- **可选升级**: 可以逐步采用新功能
- **配置优化**: 建议使用新的配置系统

### 对于开发者
- **使用新模块**: 优先使用`agent/`目录下的模块
- **插件开发**: 继承`ActionPlugin`基类开发自定义插件
- **配置扩展**: 通过修改`default_config.yaml`添加新配置项

## 📊 性能改进

- **模块化加载**: 按需加载模块，减少内存占用
- **异步支持**: 为未来的异步操作做准备
- **缓存机制**: 截图和配置缓存，提升响应速度
- **监控优化**: 实时性能监控，便于优化

## 🛡️ 可靠性提升

- **错误处理**: 更精确的异常分类和处理
- **配置验证**: 启动时验证配置有效性
- **日志记录**: 完整的操作历史记录
- **测试覆盖**: 全面的单元测试和集成测试

## 🔮 未来规划

- **异步操作**: 支持异步浏览器操作
- **更多插件**: 扩展插件生态系统
- **Web界面**: 基于配置的Web管理界面
- **云集成**: 更好的云端部署支持

## 📝 更新日志

### v2.0.0 (当前版本)
- ✅ 配置管理系统
- ✅ 自定义异常体系
- ✅ 操作日志和性能监控
- ✅ 插件化动作系统
- ✅ 模块化架构重构
- ✅ 向后兼容性保证

---

**注意**: 这是一个重大架构升级，虽然保持了向后兼容性，但建议用户逐步迁移到新的API以获得更好的体验和性能。
