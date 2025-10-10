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

from typing import Optional, List
from google.genai.types import Candidate, FinishReason
from google.genai import types

from ..exceptions import ModelResponseError


class ResponseProcessor:
    """响应处理器，负责处理AI模型的响应"""
    
    def __init__(self):
        """初始化响应处理器"""
        pass
    
    def get_text(self, candidate: Candidate) -> Optional[str]:
        """
        从候选中提取文本内容
        
        Args:
            candidate: AI模型响应候选
            
        Returns:
            提取的文本内容，如果没有则返回None
        """
        if not candidate.content or not candidate.content.parts:
            return None
        
        text_parts = []
        for part in candidate.content.parts:
            if part.text:
                text_parts.append(part.text)
        
        return " ".join(text_parts) or None
    
    def extract_function_calls(self, candidate: Candidate) -> List[types.FunctionCall]:
        """
        从候选中提取函数调用
        
        Args:
            candidate: AI模型响应候选
            
        Returns:
            函数调用列表
        """
        if not candidate.content or not candidate.content.parts:
            return []
        
        function_calls = []
        for part in candidate.content.parts:
            if part.function_call:
                function_calls.append(part.function_call)
        
        return function_calls
    
    def validate_response(self, response: types.GenerateContentResponse) -> bool:
        """
        验证响应是否有效
        
        Args:
            response: AI模型响应
            
        Returns:
            响应是否有效
            
        Raises:
            ModelResponseError: 响应无效时抛出
        """
        if not response.candidates:
            raise ModelResponseError("Response has no candidates", response_data={"response": str(response)})
        
        if len(response.candidates) == 0:
            raise ModelResponseError("Empty candidates list")
        
        # 检查第一个候选是否有效
        candidate = response.candidates[0]
        if not candidate:
            raise ModelResponseError("First candidate is None")
        
        return True
    
    def should_retry_response(self, candidate: Candidate) -> bool:
        """
        判断是否应该重试响应
        
        Args:
            candidate: AI模型响应候选
            
        Returns:
            是否应该重试
        """
        # 检查是否有畸形的函数调用
        reasoning = self.get_text(candidate)
        function_calls = self.extract_function_calls(candidate)
        
        return (
            not function_calls
            and not reasoning
            and candidate.finish_reason == FinishReason.MALFORMED_FUNCTION_CALL
        )
    
    def is_task_complete(self, candidate: Candidate) -> bool:
        """
        判断任务是否完成
        
        Args:
            candidate: AI模型响应候选
            
        Returns:
            任务是否完成
        """
        function_calls = self.extract_function_calls(candidate)
        reasoning = self.get_text(candidate)
        
        # 如果没有函数调用但有推理文本，认为任务完成
        return not function_calls and reasoning is not None
    
    def process_candidate(self, candidate: Candidate) -> dict:
        """
        处理单个候选，提取所有有用信息
        
        Args:
            candidate: AI模型响应候选
            
        Returns:
            包含提取信息的字典
        """
        reasoning = self.get_text(candidate)
        function_calls = self.extract_function_calls(candidate)
        
        return {
            "reasoning": reasoning,
            "function_calls": function_calls,
            "finish_reason": candidate.finish_reason,
            "should_retry": self.should_retry_response(candidate),
            "is_complete": self.is_task_complete(candidate),
            "has_content": bool(candidate.content),
            "has_parts": bool(candidate.content and candidate.content.parts) if candidate.content else False
        }
    
    def format_function_call_for_display(self, function_call: types.FunctionCall) -> str:
        """
        格式化函数调用用于显示
        
        Args:
            function_call: 函数调用对象
            
        Returns:
            格式化的字符串
        """
        function_call_str = f"Name: {function_call.name}"
        if function_call.args:
            function_call_str += "\nArgs:"
            for key, value in function_call.args.items():
                function_call_str += f"\n  {key}: {value}"
        return function_call_str
    
    def format_function_calls_for_display(self, function_calls: List[types.FunctionCall]) -> List[str]:
        """
        格式化多个函数调用用于显示
        
        Args:
            function_calls: 函数调用列表
            
        Returns:
            格式化的字符串列表
        """
        return [self.format_function_call_for_display(fc) for fc in function_calls]
