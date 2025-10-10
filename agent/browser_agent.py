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
import time
from typing import Literal, Optional, Union, Any
from google import genai
from google.genai import types
import termcolor
from google.genai.types import (
    Part,
    GenerateContentConfig,
    Content,
    Candidate,
    FunctionResponse,
    FinishReason,
)
from rich.console import Console
from rich.table import Table

from ..computers import Computer, EnvState
from ..config import get_config
from ..exceptions import ModelResponseError, ActionExecutionError, SafetyError
from ..utils import get_logger, get_performance_monitor

from .action_handler import ActionHandler
from .conversation_manager import ConversationManager
from .response_processor import ResponseProcessor


class BrowserAgent:
    """浏览器代理，负责与AI模型交互并执行浏览器操作"""
    
    def __init__(
        self,
        browser_computer: Computer,
        query: str,
        model_name: Optional[str] = None,
        verbose: bool = True,
    ):
        """
        初始化浏览器代理
        
        Args:
            browser_computer: 浏览器计算机实例
            query: 用户查询
            model_name: 模型名称，如果为None则从配置获取
            verbose: 是否显示详细输出
        """
        self._browser_computer = browser_computer
        self._query = query
        self._verbose = verbose
        self.final_reasoning = None
        
        # 获取配置
        self.config = get_config()
        self._model_name = model_name or self.config.model.name
        
        # 初始化各个组件
        self.action_handler = ActionHandler(browser_computer)
        self.conversation_manager = ConversationManager(query)
        self.response_processor = ResponseProcessor()
        
        # 初始化日志和性能监控
        self.logger = get_logger()
        self.performance_monitor = get_performance_monitor()
        
        # 初始化GenAI客户端
        self._client = genai.Client(
            api_key=os.environ.get("GEMINI_API_KEY"),
            vertexai=os.environ.get("USE_VERTEXAI", "0").lower() in ["true", "1"],
            project=os.environ.get("VERTEXAI_PROJECT"),
            location=os.environ.get("VERTEXAI_LOCATION"),
        )
        
        # 配置生成内容参数
        self._generate_content_config = self._create_generate_content_config()
        
        # 控制台输出
        self.console = Console()
        
        # 开始会话
        self._start_session()
    
    def _create_generate_content_config(self) -> GenerateContentConfig:
        """创建生成内容配置"""
        # 排除任何预定义函数
        excluded_predefined_functions = []
        
        # 添加自定义函数（保持原有的multiply_numbers示例）
        def multiply_numbers(x: float, y: float) -> dict:
            """Multiplies two numbers."""
            return {"result": x * y}
        
        custom_functions = [
            types.FunctionDeclaration.from_callable(
                client=self._client, callable=multiply_numbers
            )
        ]
        
        return GenerateContentConfig(
            temperature=self.config.model.temperature,
            top_p=self.config.model.top_p,
            top_k=self.config.model.top_k,
            max_output_tokens=self.config.model.max_output_tokens,
            tools=[
                types.Tool(
                    computer_use=types.ComputerUse(
                        environment=types.Environment.ENVIRONMENT_BROWSER,
                        excluded_predefined_functions=excluded_predefined_functions,
                    ),
                ),
                types.Tool(function_declarations=custom_functions),
            ],
        )
    
    def _start_session(self):
        """开始新的会话"""
        session_id = f"session_{int(time.time())}"
        
        # 启动日志记录
        if self.logger:
            self.logger.start_session(session_id)
        
        # 启动性能监控
        if self.performance_monitor:
            self.performance_monitor.start_session(session_id)
        
        # 记录配置
        if self.logger:
            self.logger.log_configuration(self.config.get_model_config())
    
    def _end_session(self):
        """结束当前会话"""
        summary = self.conversation_manager.get_conversation_summary()
        
        # 结束性能监控
        if self.performance_monitor:
            self.performance_monitor.end_session()
        
        # 结束日志记录
        if self.logger:
            self.logger.end_session(summary)
    
    def get_model_response(
        self, max_retries: Optional[int] = None, base_delay_s: Optional[int] = None
    ) -> types.GenerateContentResponse:
        """
        获取模型响应，支持重试机制
        
        Args:
            max_retries: 最大重试次数，如果为None则从配置获取
            base_delay_s: 基础延迟秒数，如果为None则从配置获取
            
        Returns:
            模型响应
            
        Raises:
            ModelResponseError: 获取响应失败时抛出
        """
        max_retries = max_retries or self.config.browser.max_retries
        base_delay_s = base_delay_s or self.config.browser.base_delay_s
        
        for attempt in range(max_retries):
            try:
                with self.performance_monitor.time_operation("model_response", {"attempt": attempt + 1}):
                    response = self._client.models.generate_content(
                        model=self._model_name,
                        contents=self.conversation_manager.get_contents(),
                        config=self._generate_content_config,
                    )
                
                # 验证响应
                self.response_processor.validate_response(response)
                
                # 记录成功的模型交互
                if self.logger:
                    reasoning = None
                    if response.candidates:
                        reasoning = self.response_processor.get_text(response.candidates[0])
                    self.logger.log_model_interaction(
                        query=self._query,
                        response=reasoning,
                        success=True
                    )
                
                return response
                
            except Exception as e:
                error_msg = f"Generating content failed on attempt {attempt + 1}: {str(e)}"
                
                # 记录失败的模型交互
                if self.logger:
                    self.logger.log_model_interaction(
                        query=self._query,
                        error=e,
                        success=False
                    )
                
                if attempt < max_retries - 1:
                    delay = base_delay_s * (2**attempt)
                    message = f"{error_msg} Retrying in {delay} seconds...\n"
                    
                    if self._verbose:
                        termcolor.cprint(message, color="yellow")
                    
                    time.sleep(delay)
                else:
                    termcolor.cprint(
                        f"Generating content failed after {max_retries} attempts.\n",
                        color="red",
                    )
                    raise ModelResponseError(
                        f"Failed to get model response after {max_retries} attempts",
                        self._model_name,
                        {"error": str(e), "attempts": max_retries}
                    )
    
    def run_one_iteration(self) -> Literal["COMPLETE", "CONTINUE"]:
        """
        运行一次迭代
        
        Returns:
            "COMPLETE" 表示任务完成，"CONTINUE" 表示继续执行
        """
        try:
            # 生成模型响应
            if self._verbose:
                with self.console.status("Generating response from Gemini Computer Use...", spinner_style=None):
                    response = self.get_model_response()
            else:
                response = self.get_model_response()
            
            # 处理响应
            if not response.candidates:
                raise ModelResponseError("Response has no candidates")
            
            candidate = response.candidates[0]
            
            # 添加模型响应到对话历史
            if candidate.content:
                self.conversation_manager.add_model_response(candidate.content)
            
            # 提取文本和函数调用
            reasoning = self.response_processor.get_text(candidate)
            function_calls = self.response_processor.extract_function_calls(candidate)
            
            # 检查是否需要重试
            if self.response_processor.should_retry_response(candidate):
                return "CONTINUE"
            
            # 检查任务是否完成
            if self.response_processor.is_task_complete(candidate):
                if self._verbose:
                    print(f"Agent Loop Complete: {reasoning}")
                self.final_reasoning = reasoning
                return "COMPLETE"
            
            # 处理函数调用
            if function_calls:
                self._process_function_calls(function_calls, reasoning)
            
            return "CONTINUE"
            
        except Exception as e:
            if self.logger:
                self.logger.log_model_interaction(
                    query=self._query,
                    error=e,
                    success=False
                )
            return "COMPLETE"
    
    def _process_function_calls(self, function_calls: list, reasoning: Optional[str]):
        """处理函数调用"""
        # 显示函数调用信息
        function_call_strs = self.response_processor.format_function_calls_for_display(function_calls)
        
        if self._verbose:
            table = Table(expand=True)
            table.add_column("Gemini Computer Use Reasoning", header_style="magenta", ratio=1)
            table.add_column("Function Call(s)", header_style="cyan", ratio=1)
            table.add_row(reasoning, "\n".join(function_call_strs))
            self.console.print(table)
            print()
        
        # 执行函数调用
        function_responses = []
        for function_call in function_calls:
            try:
                # 处理安全确认
                extra_fr_fields = {}
                if function_call.args and (safety := function_call.args.get("safety_decision")):
                    decision = self._get_safety_confirmation(safety)
                    if decision == "TERMINATE":
                        print("Terminating agent loop")
                        return
                    extra_fr_fields["safety_acknowledgement"] = "true"
                
                # 执行动作
                with self.performance_monitor.time_operation("action_execution", {"action": function_call.name}):
                    if self._verbose:
                        with self.console.status("Sending command to Computer...", spinner_style=None):
                            fc_result = self.action_handler.handle_action(function_call)
                    else:
                        fc_result = self.action_handler.handle_action(function_call)
                
                # 记录动作执行
                if self.logger:
                    self.logger.log_action(
                        action=function_call,
                        result={"success": True} if isinstance(fc_result, EnvState) else fc_result,
                        success=True
                    )
                
                # 处理结果
                if isinstance(fc_result, EnvState):
                    function_responses.append(
                        FunctionResponse(
                            name=function_call.name,
                            response={
                                "url": fc_result.url,
                                **extra_fr_fields,
                            },
                            parts=[
                                types.FunctionResponsePart(
                                    inline_data=types.FunctionResponseBlob(
                                        mime_type="image/png", data=fc_result.screenshot
                                    )
                                )
                            ],
                        )
                    )
                    
                    # 记录状态变化
                    if self.logger:
                        self.logger.log_state_change(
                            url=fc_result.url,
                            screenshot_size=len(fc_result.screenshot)
                        )
                        
                elif isinstance(fc_result, dict):
                    function_responses.append(
                        FunctionResponse(name=function_call.name, response=fc_result)
                    )
                
            except Exception as e:
                # 记录动作执行失败
                if self.logger:
                    self.logger.log_action(
                        action=function_call,
                        error=e,
                        success=False
                    )
                
                raise ActionExecutionError(
                    f"Failed to execute function call '{function_call.name}': {str(e)}",
                    function_call.name,
                    function_call.args,
                    e
                )
        
        # 添加函数响应到对话历史
        self.conversation_manager.add_function_responses(function_responses)
        
        # 清理旧的截图
        self.conversation_manager.cleanup_old_screenshots()
    
    def _get_safety_confirmation(self, safety: dict[str, Any]) -> Literal["CONTINUE", "TERMINATE"]:
        """
        获取安全确认
        
        Args:
            safety: 安全决策信息
            
        Returns:
            用户决策
        """
        if safety["decision"] != "require_confirmation":
            raise SafetyError(f"Unknown safety decision: {safety['decision']}", 
                            safety.get("decision"), 
                            safety.get("explanation"))
        
        termcolor.cprint(
            "Safety service requires explicit confirmation!",
            color="yellow",
            attrs=["bold"],
        )
        print(safety["explanation"])
        
        decision = ""
        while decision.lower() not in ("y", "n", "ye", "yes", "no"):
            decision = input("Do you wish to proceed? [Yes]/[No]\n")
        
        return "TERMINATE" if decision.lower() in ("n", "no") else "CONTINUE"
    
    def agent_loop(self):
        """主代理循环"""
        try:
            status = "CONTINUE"
            while status == "CONTINUE":
                status = self.run_one_iteration()
        finally:
            self._end_session()
    
    def denormalize_x(self, x: int) -> int:
        """将归一化的x坐标转换为屏幕坐标"""
        return int(x / 1000 * self._browser_computer.screen_size()[0])

    def denormalize_y(self, y: int) -> int:
        """将归一化的y坐标转换为屏幕坐标"""
        return int(y / 1000 * self._browser_computer.screen_size()[1])
