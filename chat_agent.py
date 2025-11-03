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
from dotenv import load_dotenv
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
import time
from rich.console import Console
from rich.table import Table

from computers import EnvState, Computer

from browser_agent import BrowserAgent

console = Console()

# Built-in Computer Use tools will return "EnvState".
# Custom provided functions will return "dict".
FunctionResponseT = Union[EnvState, dict]

# 사용자 지정 앱 조작 함수
def control_app(user_instruction: str) -> dict:
    """
    사용자의 요청에 따라 모바일 앱 조작을 시작한다.
    이 함수는 앱 조작 에이전트(App Agent)에게 요청을 토스하는 데 사용된다.
    """
    # 이 함수는 실제로 앱을 조작하지 않고, App Agent에게 넘겨줌.
    # user_instruction: 사용자가 요청한 조작 내용
    # return: 앱 조작 요청이 App Agent에게 전달되었음을 나타내는 상태메세지.
    #
    ### TODO: 어떤 앱이 있는지 Char Agent가 미리 알고 있어야하나? 알아야 한다면 앱 목록을 어떻게 제공하면 좋을까?
    # 
    # 현재는 dummy.
    return {
        "status": "App_AGENT_INVOKED",
        "task": user_instruction
    }

class ChatAgent:
    def __init__(
        self,
        browser_agent: BrowserAgent,
        model_name: str,
        verbose: bool = True,
    ):
        self._model_name = model_name
        self._verbose = verbose
        self._browser_agent = browser_agent
        load_dotenv()
        self._client = genai.Client(
            api_key=os.getenv("GEMINI_API_KEY"),
            vertexai=os.environ.get("USE_VERTEXAI", "0").lower() in ["true", "1"],
            project=os.environ.get("VERTEXAI_PROJECT"),
            location=os.environ.get("VERTEXAI_LOCATION"),
        )
        # 유저 쿼리와 LLM 응답이 저장되는 리스트
        self._contents: list[Content] = []

        browser_abilities = ", ".join(BrowserAgent.PREDEFINED_COMPUTER_USE_FUNCTIONS) + " 등"

        # 일상 대화를 위한 system instruction
        system_instruction = (
            "당신은 사용자의 일상 대화를 처리하는 친절하고 유능한 AI 비서입니다.",
            "사용자의 대화 요청에 응대하는 것이 기본 목표이며, 앱 조작이 필요한지 여부를 판단하는 것이 핵심 임무입니다.",
            "사용자가 휴대폰 앱을 조작(클릭, 타이핑, 스크롤 등)하도록 요청하면, 지체 없이 control_app 함수를 사용해야 합니다.",
            f"당신은 앱 조작이 필요할 때 control_app 함수를 사용합니다. 이 함수를 호출받는 에이전트는 {browser_abilities}과 같은 다양한 UI 조작을 수행할 수 있습니다. "
            "control_app 함수 실행 결과로 앱 조작의 성공/실패 메시지를 받으면, 그 결과를 바탕으로 사용자에게 친절하고 이해하기 쉬운 최종 요약 응답을 제공하십시오."
        )

        # Exclude any predefined functions here.
        excluded_predefined_functions = []

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
            system_instruction=system_instruction,
            tools=[
                # types.Tool(
                #     computer_use=types.ComputerUse(
                #         environment=types.Environment.ENVIRONMENT_BROWSER,
                #         excluded_predefined_functions=excluded_predefined_functions,
                #     ),
                # ),
                types.Tool(function_declarations=custom_functions),
            ],
        )

    def handle_action(self, action: types.FunctionCall) -> FunctionResponseT:
        """Handles the action and returns the environment state."""
        if action.name == control_app.__name__:
            user_instruction=action.args["user_instruction"]

            print(f"GCU Agent로 토스: 앱 조작 요청 수신")
            print(f"요청: {user_instruction}")

            self._contents.append
            browser_result = self._browser_agent.execute_function_app(
                instruction=user_instruction
            )
            print(f"GCU Agent로부터 응답 수신 완료\n" + browser_result)
            return {
                "success_status": "TASK_COMPLETED_BY_GCU",
                "result_message": f"앱 조작 결과: {browser_result.summary}"
            }
        # elif:
        else:
            raise ValueError(f"Unsupported function: {action}")

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

    # 중요
    def run_one_iteration(self) -> Literal["COMPLETE", "CONTINUE"]:
        # Generate a response from the model.
        if self._verbose:
            with console.status(
                "Generating response from Gemini Computer Use...", spinner_style=None
            ):
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
            print(f"{reasoning}")
            self.final_reasoning = reasoning
            return "CONTINUE"

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
            if function_call.args and (
                safety := function_call.args.get("safety_decision")
            ):
                decision = self._get_safety_confirmation(safety)
                if decision == "TERMINATE":
                    print("Terminating agent loop")
                    return "COMPLETE"
                # Explicitly mark the safety check as acknowledged.
                extra_fr_fields["safety_acknowledgement"] = "true"
            if self._verbose:
                with console.status(
                    "Sending command to Computer...", spinner_style=None
                ):
                    fc_result = self.handle_action(function_call)
            else:
                fc_result = self.handle_action(function_call)
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
            elif isinstance(fc_result, dict):
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

    def _get_safety_confirmation(
        self, safety: dict[str, Any]
    ) -> Literal["CONTINUE", "TERMINATE"]:
        if safety["decision"] != "require_confirmation":
            raise ValueError(f"Unknown safety decision: safety['decision']")
        termcolor.cprint(
            "Safety service requires explicit confirmation!",
            color="yellow",
            attrs=["bold"],
        )
        print(safety["explanation"])
        decision = ""
        while decision.lower() not in ("y", "n", "ye", "yes", "no"):
            decision = input("Do you wish to proceed? [Yes]/[No]\n")
        if decision.lower() in ("n", "no"):
            return "TERMINATE"
        return "CONTINUE"

    def agent_loop(self):
        status = "CONTINUE"
        while status == "CONTINUE":
            user_query = input("Enter your query (or '-q' to quit): ")
            if( user_query.lower() in ('-q', 'exit', '--quit')):
                print("Exiting the agent loop.")
                status = "COMPLETE"
                continue
            self._contents.append(Content(
                    role="user",
                    parts=[
                        Part(text=user_query),
                    ],
                ))
            status = self.run_one_iteration()