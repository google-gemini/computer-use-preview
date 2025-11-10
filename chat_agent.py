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
from mock import MockComputer, MOCK_SCREENSHOTS 
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
        load_dotenv()
        self._client = genai.Client(
            api_key=os.getenv("GEMINI_API_KEY"),
            vertexai=os.environ.get("USE_VERTEXAI", "0").lower() in ["true", "1"],
            project=os.environ.get("VERTEXAI_PROJECT"),
            location=os.environ.get("VERTEXAI_LOCATION"),
        )
        # 유저 쿼리와 LLM 응답이 저장되는 리스트
        self._contents: list[Content] = []

        cu_abilities = ", ".join(self._cu_agent.PREDEFINED_COMPUTER_USE_FUNCTIONS) + " 등"
        user_app_list = ", ".join(self.PREDEFINED_USER_APP) + " 등"

        # 일상 대화를 위한 system instruction
        # 일단 browser에서 진행하는 프롬프트를 사용
        # system_instruction = (
        #     "당신은 사용자의 일상 대화를 처리하는 친절하고 유능한 AI 비서입니다.",
        #     "사용자의 대화 요청에 응대하는 것이 기본 목표이며, 브라우저 조작이 필요한지 여부를 판단하는 것이 핵심 임무입니다.",
        #     "당신이 직접 브라우저를 조작하는 것이 아니고, 브라우저를 조작하도록 전담하는 Browser Agent에게 구체적인 조작 명령을 내려야 합니다.",
        #     "사용자가 브라우저가 필요한 query를 요청하면, 지체 없이 control_app 함수를 사용해야 합니다.",
        #     "control_app 함수 실행 결과로 앱 조작의 성공/실패 메시지를 받으면, 그 결과를 바탕으로 사용자에게 친절하고 이해하기 쉬운 최종 요약 응답을 제공하십시오."
        # )

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

        # Exclude any predefined functions here.
        # excluded_predefined_functions = []

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

    def handle_action(self, action: types.FunctionCall) -> FunctionResponseT:
        """ChatAgent가 control_app을 호출하면 CUAgent로 명령을 토스"""
        if action.name == control_app.__name__:
            user_instruction=action.args["user_instruction"]

            # Mock 데이터는 CUAgent가 내부적으로 처리할 수 있도록 명령만 전달
            
            print(f"CU Agent로 토스: 앱 조작 요청 수신")
            print(f"요청: {user_instruction}")

            # CU Agent 실행 (단일 실행) -> Action JSON 또는 최종 응답 반환
            # CU Agent의 execute_task는 이제 단일 실행을 처리하고 Dict를 반환합니다.
            final_result_text = self._cu_agent.execute_task(
                instruction=user_instruction,
                # ChatAgent에서 초기 스크린샷 데이터를 준비하여 전달합니다.
                screenshot_data=base64.b64decode(MOCK_SCREENSHOTS["initial"]), 
                url_or_activity=MockComputer().current_url()
            )
            
            print("\n--- CU Agent로부터 최종 결과 수신 완료 ---")
            
            # ChatAgent가 LLM에게 전달할 FunctionResponse 반환
            # CU Agent가 작업을 완료했으므로, 최종 결과 메시지를 반환합니다.
            return {
                "status": "CU_AGENT_TASK_COMPLETE",
                "message": final_result_text
            }
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

    # 검증 필요 : 중요 수정: function_calls가 없으면 최종 응답을 출력하고 COMPLETE (종료)
    def run_one_iteration(self) -> Literal["COMPLETE", "CONTINUE"]:
        # Generate a response from the model.
        if self._verbose:
            print("Generating response from Gemini ...")
            try:
                response = self.get_model_response()
            except Exception as e:
                return "COMPLETE"
        else:
            try:
                response = self.get_model_response()
            except Exception as e:
                return "COMPLETE"

        if not response.candidates:
            print("Response has no candidates!")
            print(response)
            raise ValueError("Empty response")

        # Extract the text and function call from the response.
        candidate = response.candidates[0]
        # Append the model turn to conversation history.
        if candidate.content:
            self._contents.append(candidate.content)

        reasoning = self.get_text(candidate)
        function_calls = self.extract_function_calls(candidate)

        # Retry the request in case of malformed FCs.
        if (
            not function_calls
            and not reasoning
            and candidate.finish_reason == FinishReason.MALFORMED_FUNCTION_CALL
        ):
            return "CONTINUE"

        if not function_calls:
            print(f"Chat Agent Response: {reasoning}") # 최종 응답 출력
            self.final_reasoning = reasoning
            return "COMPLETE" # COMPLETE로 수정: 최종 응답 후 루프 종료

        function_call_strs = []
        for function_call in function_calls:
            # Print the function call and any reasoning.
            function_call_str = f"Name: {function_call.name}"
            if function_call.args:
                function_call_str += f"\nArgs:"
                for key, value in function_call.args.items():
                    function_call_str += f"\n  {key}: {value}"
            function_call_strs.append(function_call_str)

        table = Table(expand=True)
        table.add_column(
            "Gemini Computer Use Reasoning", header_style="magenta", ratio=1
        )
        table.add_column("Function Call(s)", header_style="cyan", ratio=1)
        table.add_row(reasoning, "\n".join(function_call_strs))
        if self._verbose:
            console.print(table)
            print()

        function_responses = []
        for function_call in function_calls:
            extra_fr_fields = {}
            
            if self._verbose:
                print("Sending command to Computer...")
                fc_result = self.handle_action(function_call)
            else:
                fc_result = self.handle_action(function_call)
            if isinstance(fc_result, dict):
                function_responses.append(
                    FunctionResponse(name=function_call.name, response=fc_result)
                )

        self._contents.append(
            Content(
                role="user",
                parts=[Part(function_response=fr) for fr in function_responses],
            )
        )
        return "CONTINUE"

    def start_chat_loop(self):
        """사용자 입력을 반복적으로 받아 다중 턴 채팅을 처리하는 루프."""
        print("\n--- 계층적 에이전트 채팅 시작 (CU Agent 활성화) ---")
        print("--- 'q' 또는 'quit' 입력 시 종료됩니다. ---")
        
        # 1. 무한 루프 시작
        while True:
            # 2. 사용자 입력 받기
            user_query = input("\n사용자 쿼리 입력: ")
            
            if user_query.lower() in ('q', 'quit', 'exit'):
                print("채팅을 종료합니다.")
                break
            
            if not user_query.strip():
                continue
                
            # 3. 새로운 쿼리를 contents에 추가 (이전 대화 내용 유지)
            self._contents.append(Content(
                role="user",
                parts=[
                    Part(text=user_query),
                ],
            ))
            
            # 4. 쿼리 처리를 위한 run_one_iteration 루프 실행
            # (ChatAgent가 CU Agent를 호출하고 최종 응답을 출력할 때까지)
            status = "CONTINUE"
            while status == "CONTINUE":
                status = self.run_one_iteration()
                
            # run_one_iteration이 COMPLETE를 반환하면 루프 종료 및 다음 사용자 입력 대기
