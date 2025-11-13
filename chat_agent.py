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
import base64
from typing import Literal, Optional, Union, Any, Dict
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
import time
from rich.console import Console
from rich.table import Table

from cu_agent import CUAgent
from dotenv import load_dotenv

load_dotenv()
console = Console()

FunctionResponseT = dict

# 사용자 지정 앱 조작 함수
def control_app(user_instruction: str) -> dict:
    """
    사용자의 요청에 따라 모바일 앱 조작을 시작한다.
    이 함수는 앱 조작 에이전트(App Agent)에게 요청을 토스하는 데 사용된다.
    """
    # ChatAgent의 handle_action에서 실제 CUAgent 호출 및 결과 처리를 수행합니다.
    return {
        "status": "App_AGENT_INVOKED",
        "task": user_instruction
    }

class ChatAgent:
    PREDEFINED_USER_APP = ["Chrome", "메세지", "캘린더", "지도", "카메라", "녹음", "갤러리", "브라우저", "설정"]

    def __init__(
        self,
        cu_agent: CUAgent,
        model_name: str,
        verbose: bool = True,
    ):
        self._model_name = model_name
        self._verbose = verbose
        self._cu_agent = cu_agent
        self._client = genai.Client(
            api_key=os.getenv("GEMINI_API_KEY"),
            vertexai=os.environ.get("USE_VERTEXAI", "0").lower() in ["true", "1"],
            project=os.environ.get("VERTEXAI_PROJECT"),
            location=os.environ.get("VERTEXAI_LOCATION"),
        )
        self._contents: list[Content] = []
        self._final_reasoning: str = ""

        # 상태 변수
        self._cu_task_in_progress: bool = False
        self._last_cu_action_json: Optional[Dict[str, Any]] = None
        self._pending_instruction: Optional[str] = None # 스크린샷을 기다리는 작업 지시
        self._latest_action_result: Optional[Dict[str, Any]] = None # run_one_iteration의 임시 결과
        
        cu_abilities = ", ".join(self._cu_agent.PREDEFINED_COMPUTER_USE_FUNCTIONS) + " 등"
        user_app_list = ", ".join(self.PREDEFINED_USER_APP) + " 등"

        # 일상 대화를 위한 system instruction - 앱 조작 버전
        app_system_instruction = (
            "당신은 사용자의 일상 대화를 처리하는 친절하고 유능한 AI 비서입니다.",
            "사용자의 의도를 파악하여 앱 조작이 필요한지 여부를 판단하는 것이 핵심 임무입니다.",
            "당신이 직접 휴대폰을 조작하는 것이 아니고, CU Agent에게 구체적인 앱 조작 명령을 전달해야 합니다.",
            "CU Agent는 휴대폰 앱 조작을 담당합니다.",
            f"휴대폰에는 {user_app_list}과 같은 기본 앱들이 설치되어 있습니다.",
            "사용자가 휴대폰 앱을 조작(검색, 클릭, 타이핑, 스크롤 등)하도록 요청하면, 지체 없이 control_app 함수를 호출하십시오.",
            f"control_app 함수는 CU Agent에게 작업을 토스합니다. CU Agent는 {cu_abilities}과 같은 다양한 UI 조작을 수행할 수 있습니다. "
            "control_app 함수 실행 결과로 앱 조작의 결과를 받으면, 그 결과를 바탕으로 사용자에게 친절하고 이해하기 쉬운 최종 요약 응답을 제공하십시오."
        )

        # Add your own custom functions here.
        custom_functions = [
            types.FunctionDeclaration.from_callable(
                client=self._client, callable=control_app
            )
        ]

        self._generate_content_config = GenerateContentConfig(
            temperature=1,
            top_p=0.95,
            top_k=40,
            max_output_tokens=8192,
            system_instruction=app_system_instruction,
            tools=[
                types.Tool(function_declarations=custom_functions),
            ],
        )

    def process_query(self, query: str) -> Dict[str, Any]:
        """/chat/query 에서 호출"""
        
        self._final_reasoning = ""
        self._cu_task_in_progress = False 
        self._last_cu_action_json = None
        
        self._contents.append(Content(role="user", parts=[Part(text=query)]))
        
        status = self.run_one_iteration()
        
        if self._latest_action_result: 
            # control_app이 호출된 경우
            result = self._latest_action_result
            self._latest_action_result = None
            return result
        else: 
            # 일반 텍스트 응답
            return {"type": "RESPONSE", "message": self.final_reasoning}
        
    def process_step(self, screenshot_bytes: bytes, activity: str) -> Dict[str, Any]:
        """/chat/step 에서 호출"""
        
        if self._cu_task_in_progress and self._last_cu_action_json:
            # 작업 계속
            if self._verbose:
                print(f"[ChatAgent] 작업 계속 진행 (이전 액션: {self._last_cu_action_json['action']})")
            cu_result = self._cu_agent.step(
                previous_action=self._last_cu_action_json, 
                current_screenshot_data=screenshot_bytes,
                current_activity=activity
            )
        elif self._pending_instruction:
            # 작업 시작
            if self._verbose:
                print(f"[ChatAgent] CUAgent 작업 시작: {self._pending_instruction}")
            cu_result = self._cu_agent.init_task(
                self._pending_instruction, screenshot_bytes, activity
            )
            self._pending_instruction = None
        else:
            return {"type": "ERROR", "message": "스크린샷을 받았으나, 대기 중인 작업이 없습니다."}

        # CUAgent 응답에 따라 상태 업데이트
        if cu_result["type"] == "ACTION":
            self._cu_task_in_progress = True
            self._last_cu_action_json = cu_result
        else: # RESPONSE or ERROR
            self._cu_task_in_progress = False 
            self._last_cu_action_json = None
            # TODO: CUAgent의 최종 응답(cu_result)을 ChatAgent의 LLM에게 알려 
            # 더 친절한 사용자용 응답(self.final_reasoning)을 생성하도록 run_one_iteration()을 한 번 더 호출.
            # (현재는 CUAgent의 응답을 바로 반환)

        return cu_result
    
    def handle_action(self, action: types.FunctionCall) -> FunctionResponseT:
        """ChatAgent의 LLM이 control_app을 호출하면, 스크린샷이 필요한지 확인."""
        if action.name == control_app.__name__:
            user_instruction = action.args["user_instruction"]
            
            # 스크린샷이 필요한 작업이므로, 대기 상태로 전환
            self._pending_instruction = user_instruction
            
            # 클라이언트에게 스크린샷을 요청하는 응답을 생성
            result = {
                "type": "REQUIRE_SCREENSHOT", 
                "message": "작업을 위해 현재 화면 스크린샷이 필요합니다. 전송해주세요."
            }
            # 이 결과를 process_query가 반환할 수 있도록 저장
            self._latest_action_result = result 
            
            # LLM에게는 "스크린샷 요청함"이라고 보고
            return {"status": "REQUIRE_SCREENSHOT"}
        else:
            raise ValueError(f"Unsupported function: {action.name}")

    def get_model_response(
        self, max_retries=5, base_delay_s=1
    ) -> types.GenerateContentResponse:
        for attempt in range(max_retries):
            try:
                response = self._client.models.generate_content(
                    model=self._model_name,
                    contents=self._contents,
                    config=self._generate_content_config,
                )
                return response  # Return response on success
            except Exception as e:
                print(e)
                if attempt < max_retries - 1:
                    delay = base_delay_s * (2**attempt)
                    message = (
                        f"Generating content failed on attempt {attempt + 1}. "
                        f"Retrying in {delay} seconds...\n"
                    )
                    termcolor.cprint(
                        message,
                        color="yellow",
                    )
                    time.sleep(delay)
                else:
                    termcolor.cprint(
                        f"Generating content failed after {max_retries} attempts.\n",
                        color="red",
                    )
                    raise

    def get_text(self, candidate: Candidate) -> Optional[str]:
        """Extracts the text from the candidate."""
        if not candidate.content or not candidate.content.parts:
            return None
        text = []
        for part in candidate.content.parts:
            if part.text:
                text.append(part.text)
        return " ".join(text) or None

    def extract_function_calls(self, candidate: Candidate) -> list[types.FunctionCall]:
        """Extracts the function call from the candidate."""
        if not candidate.content or not candidate.content.parts:
            return []
        ret = []
        for part in candidate.content.parts:
            if part.function_call:
                ret.append(part.function_call)
        return ret

    def run_one_iteration(self) -> Literal["COMPLETE", "CONTINUE"]:
        if self._verbose:
            print("[ChatAgent] Gemini Thinking...")
        
        try:
            response = self.get_model_response()
        except Exception as e:
            return "COMPLETE"

        if not response.candidates:
            raise ValueError("Response has no candidates!")

        candidate = response.candidates[0]
        if candidate.content:
            self._contents.append(candidate.content)

        reasoning = self.get_text(candidate)
        function_calls = self.extract_function_calls(candidate)

        if not function_calls:
            self.final_reasoning = reasoning
            return "COMPLETE"
        
        if self._verbose:
            table = Table(expand=True)
            table.add_column("Chat Agent Reasoning", header_style="magenta", ratio=1)
            table.add_column("Function Call(s)", header_style="cyan", ratio=1)
            table.add_row(reasoning, function_calls[0].name)
            console.print(table)
            print()
            
        fc_result = self.handle_action(function_calls[0])

        self._contents.append(
            Content(role="user", parts=[FunctionResponse(name=function_calls[0].name, response=fc_result)])
        )
        return "CONTINUE"


    