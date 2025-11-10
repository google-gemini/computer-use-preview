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
# import base64
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

# from mock import MockEnvState, MockComputer, MOCK_SCREENSHOTS

# load environment variable in .env
from dotenv import load_dotenv

load_dotenv()

ANDROID_SYSTEM_PROMPT = """
You are an intelligent agent tasked with operating an Android phone to complete user instructions.

### Your Environment and Capabilities
1.  **Device View:** All interactions occur on a **mobile-sized screen** (normalized coordinates 0-1000).
2.  **Core Actions (Predefined):** You can perform basic UI interactions like **click_at**, **type_text_at**, **scroll_at**, **wait_5_seconds**, and **go_back**.
3.  **Advanced Actions (Custom):** You have access to the following specialized functions for high-level mobile operations:
    * `open_app(app_name)`: To launch any application (e.g., '카메라', '설정').
    * `go_home()`: To navigate directly to the Android home screen.
    * `long_press_at(x, y)`: For long-press interactions.
    * `scroll_to_text(text)`: To efficiently find and bring specific text into view.
    * `swipe(start_x, start_y, end_x, end_y)`: To perform drag/swipe gestures.
    * `set_device_setting(setting_name, value)`: To change device-level settings (e.g., Wi-Fi, Bluetooth).
    * `close_current_app()`: To close the foreground application.
    * `go_recent_apps()`: To access the recent applications screen.
4.  **Browser Conventions:** Ignore conventions related to web browsers (URLs, forward/backward buttons, document scrolling) unless the current action is explicitly within a dedicated **browser app** (like '크롬').

### Strategy Guidelines
* **Action Clarity:** Always state your **reasoning** before calling a function.
* **Efficiency:** Use the advanced custom functions (e.g., `open_app`, `scroll_to_text`) whenever they offer a clear efficiency advantage over basic actions (e.g., multiple taps or scrolls).
"""

MAX_RECENT_TURN_WITH_SCREENSHOTS = 3

console = Console()

# Built-in Computer Use tools will return "EnvState".
# Custom provided functions will return "dict".
# FunctionResponseT = Union[MockEnvState, dict]
FunctionResponseT = Dict[str, Any]

def open_app(app_name: str, intent: Optional[str] = None) -> Dict[str, Any]:
    """Opens an app by name."""
    return {"status": "requested_open", "app_name": app_name, "intent": intent}

def long_press_at(x: int, y: int) -> Dict[str, int]:
    """Long-press at a specific screen coordinate."""
    return {"x": x, "y": y}

def go_home() -> Dict[str, str]:
    """Navigates to the device home screen."""
    return {"status": "home_requested"}

def scroll_to_text(text: str) -> Dict[str, Any]:
    """Scrolls the current view until the specified text is visible."""
    return {"status": "requested_scroll_to_text", "text": text}

def swipe(start_x: int, start_y: int, end_x: int, end_y: int, duration: float = 0.5) -> Dict[str, Any]:
    """Performs a swipe/drag gesture between two normalized coordinates."""
    return {"status": "requested_swipe", "start_x": start_x, "start_y": start_y, "end_x": end_x, "end_y": end_y, "duration": duration}

def set_device_setting(setting_name: str, value: Any) -> Dict[str, Any]:
    """Changes a specific device setting (e.g., WIFI, Bluetooth)."""
    return {"status": "requested_set_setting", "setting_name": setting_name, "value": value}

def close_current_app() -> Dict[str, str]:
    """Closes the currently active application."""
    return {"status": "requested_close_app"}

def go_recent_apps() -> Dict[str, str]:
    """Navigates to the device's recent applications screen."""
    return {"status": "requested_recent_apps"}

class CUAgent:
    PREDEFINED_COMPUTER_USE_FUNCTIONS = [
        "click_at",
        "type_text_at",
        "scroll_at",
        "wait_5_seconds",
        "go_back",
        "open_app", 
        "long_press_at",
        "go_home",
        "scroll_to_text",
        "swipe",
        "set_device_setting",
        "close_current_app",
        "go_recent_apps",
    ]
    EXCLUDED_PREDEFINED_FUNCTIONS = [
        "open_web_browser",
        "hover_at",
        "scroll_document",
        "go_forward",
        "navigate",
        "key_combination",
        "drag_and_drop",
        "search",
    ]

    def __init__(
        self,
        # browser_computer: MockComputer,
        model_name: str = 'gemini-2.5-computer-use-preview-10-2025',
        verbose: bool = True,
    ):
        # self._browser_computer = browser_computer
        self._model_name = model_name
        self._verbose = verbose
        # self.final_reasoning = str = ""
        self._client = genai.Client(
            api_key=os.environ.get("GEMINI_API_KEY"),
            vertexai=os.environ.get("USE_VERTEXAI", "0").lower() in ["true", "1"],
            project=os.environ.get("VERTEXAI_PROJECT"),
            location=os.environ.get("VERTEXAI_LOCATION"),
        )
        self._contents: list[Content] = []

        # Exclude any predefined functions here.
        excluded_predefined_functions = self.EXCLUDED_PREDEFINED_FUNCTIONS

        # Add your own custom functions here.
        custom_functions = [
            types.FunctionDeclaration.from_callable(client=self._client, callable=open_app),
            types.FunctionDeclaration.from_callable(client=self._client, callable=long_press_at),
            types.FunctionDeclaration.from_callable(client=self._client, callable=go_home),
            types.FunctionDeclaration.from_callable(client=self._client, callable=scroll_to_text),
            types.FunctionDeclaration.from_callable(client=self._client, callable=swipe),
            types.FunctionDeclaration.from_callable(client=self._client, callable=set_device_setting),
            types.FunctionDeclaration.from_callable(client=self._client, callable=close_current_app),
            types.FunctionDeclaration.from_callable(client=self._client, callable=go_recent_apps),
        ]

        self._generate_content_config = GenerateContentConfig(
            temperature=1,
            top_p=0.95,
            top_k=40,
            max_output_tokens=8192,
            system_instruction=ANDROID_SYSTEM_PROMPT,
            tools=[
                types.Tool(
                    computer_use=types.ComputerUse(
                        environment=types.Environment.ENVIRONMENT_BROWSER,
                        excluded_predefined_functions=excluded_predefined_functions,
                    ),
                    
                ),
                # AFC 에러? 메시지 해결 필요
                types.Tool(
                    function_declarations=custom_functions
                )
            ],
        )

    # handle_action 메서드 제거 (서버는 직접 실행하지 않음)

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

    # def run_one_iteration(self) -> Literal["COMPLETE", "CONTINUE"]:
    #     # Generate a response from the model.
    #     if self._verbose:
    #         with console.status(
    #             "Generating response from Gemini Computer Use...", spinner_style=None
    #         ):
    #             try:
    #                 response = self.get_model_response()
    #             except Exception as e:
    #                 return "COMPLETE"
    #     else:
    #         try:
    #             response = self.get_model_response()
    #         except Exception as e:
    #             return "COMPLETE"

    #     if not response.candidates:
    #         print("Response has no candidates!")
    #         print(response)
    #         raise ValueError("Empty response")

    #     # Extract the text and function call from the response.
    #     candidate = response.candidates[0]
    #     # Append the model turn to conversation history.
    #     if candidate.content:
    #         self._contents.append(candidate.content)

    #     reasoning = self.get_text(candidate)
    #     function_calls = self.extract_function_calls(candidate)

    #     # Retry the request in case of malformed FCs.
    #     if (
    #         not function_calls
    #         and not reasoning
    #         and candidate.finish_reason == FinishReason.MALFORMED_FUNCTION_CALL
    #     ):
    #         return "CONTINUE"

    #     if not function_calls:
    #         print(f"Agent Loop Complete: {reasoning}")
    #         self.final_reasoning = reasoning
    #         return "COMPLETE"

    #     function_call_strs = []
    #     for function_call in function_calls:
    #         # Print the function call and any reasoning.
    #         function_call_str = f"Name: {function_call.name}"
    #         if function_call.args:
    #             function_call_str += f"\nArgs:"
    #             for key, value in function_call.args.items():
    #                 function_call_str += f"\n  {key}: {value}"
    #         function_call_strs.append(function_call_str)

    #     table = Table(expand=True)
    #     table.add_column(
    #         "Gemini Computer Use Reasoning", header_style="magenta", ratio=1
    #     )
    #     table.add_column("Function Call(s)", header_style="cyan", ratio=1)
    #     table.add_row(reasoning, "\n".join(function_call_strs))
    #     if self._verbose:
    #         console.print(table)
    #         print()

    #     function_responses = []
    #     for function_call in function_calls:
    #         extra_fr_fields = {}
    #         if function_call.args and (
    #             safety := function_call.args.get("safety_decision")
    #         ):
    #             decision = self._get_safety_confirmation(safety)
    #             if decision == "TERMINATE":
    #                 print("Terminating agent loop")
    #                 return "COMPLETE"
    #             # Explicitly mark the safety check as acknowledged.
    #             extra_fr_fields["safety_acknowledgement"] = "true"
    #         if self._verbose:
    #             with console.status(
    #                 "Sending command to Computer...", spinner_style=None
    #             ):
    #                 fc_result = self.handle_action(function_call)
    #         else:
    #             fc_result = self.handle_action(function_call)
    #         if isinstance(fc_result, MockEnvState):
    #             function_responses.append(
    #                 FunctionResponse(
    #                     name=function_call.name,
    #                     response={
    #                         "url": fc_result.url,
    #                         **extra_fr_fields,
    #                         "message": fc_result.message if hasattr(fc_result, 'message') else "Action successful.",
    #                     },
    #                     parts=[
    #                         types.FunctionResponsePart(
    #                             inline_data=types.FunctionResponseBlob(
    #                                 mime_type="image/png", data=fc_result.screenshot
    #                             )
    #                         )
    #                     ],
    #                 )
    #             )
    #         elif isinstance(fc_result, dict):
    #             function_responses.append(
    #                 FunctionResponse(name=function_call.name, response=fc_result)
    #             )

    #     self._contents.append(
    #         Content(
    #             role="user",
    #             parts=[Part(function_response=fr) for fr in function_responses],
    #         )
    #     )

    #     # only keep screenshots in the few most recent turns, remove the screenshot images from the old turns.
    #     turn_with_screenshots_found = 0
    #     for content in reversed(self._contents):
    #         if content.role == "user" and content.parts:
    #             # check if content has screenshot of the predefined computer use functions.
    #             has_screenshot = False
    #             for part in content.parts:
    #                 if (
    #                     part.function_response
    #                     and part.function_response.parts
    #                     and part.function_response.name
    #                     in self.PREDEFINED_COMPUTER_USE_FUNCTIONS
    #                 ):
    #                     has_screenshot = True
    #                     break

    #             if has_screenshot:
    #                 turn_with_screenshots_found += 1
    #                 # remove the screenshot image if the number of screenshots exceed the limit.
    #                 if turn_with_screenshots_found > MAX_RECENT_TURN_WITH_SCREENSHOTS:
    #                     for part in content.parts:
    #                         if (
    #                             part.function_response
    #                             and part.function_response.parts
    #                             and part.function_response.name
    #                             in self.PREDEFINED_COMPUTER_USE_FUNCTIONS
    #                         ):
    #                             part.function_response.parts = None

    #     return "CONTINUE"

    # def _get_safety_confirmation(
    #     self, safety: dict[str, Any]
    # ) -> Literal["CONTINUE", "TERMINATE"]:
    #     if safety["decision"] != "require_confirmation":
    #         raise ValueError(f"Unknown safety decision: safety['decision']")
    #     termcolor.cprint(
    #         "Safety service requires explicit confirmation!",
    #         color="yellow",
    #         attrs=["bold"],
    #     )
    #     print(safety["explanation"])
    #     decision = ""
    #     while decision.lower() not in ("y", "n", "ye", "yes", "no"):
    #         decision = input("Do you wish to proceed? [Yes]/[No]\n")
    #     if decision.lower() in ("n", "no"):
    #         return "TERMINATE"
    #     return "CONTINUE"
    
    def execute_task(
        self, 
        instruction: str, 
        screenshot_data: bytes,
        url_or_activity: str = "unknown_activity"
    ) -> Optional[Dict[str, Any]]:
        """
        CU Agent의 단일 실행 단계를 수행합니다. 클라이언트로부터 받은 실제 데이터를 사용합니다.        
        """
        if not screenshot_data:
             raise ValueError("Screenshot data is required for CU Agent execution.")

        # 1. 초기 Content 구성
        parts = [
            Part(text=instruction),
            Part(inline_data=types.Blob(mime_type="image/png", data=screenshot_data)),
            Part(text=f"현재 화면 상태: {url_or_activity}")
        ]

        # 2. _contents 초기화 (단일 턴 응답을 위한 시작)
        self._contents = [
            Content(
                role="user",
                parts=parts,
            )
        ]
        # self.final_reasoning = ""
        
        # 3. 모델 응답 생성 및 분석
        if self._verbose:
            print("⠴ Generating response from Gemini Computer Use...")
        
        try:
            response = self.get_model_response()
        except Exception as e:
            print(f"Error during model generation: {e}")
            return None
        
        if not response.candidates:
            return None

        candidate = response.candidates[0]
        if candidate.content:
            self._contents.append(candidate.content) # 히스토리 업데이트
        
        # 결과 분석 및 반환
        function_calls = self.extract_function_calls(candidate)
        if function_calls:
            # 첫 번째 Function Call을 Action으로 반환
            return {"action": function_calls[0].name, "args": dict(function_calls[0].args)}
        
        reasoning = self.get_text(candidate)
        if reasoning:
            return {"final_response": reasoning}
        
        return None

    # def agent_loop(self):
    #     status = "CONTINUE"
    #     while status == "CONTINUE":
    #         status = self.run_one_iteration()

    def denormalize_x(self, x: int) -> int:
        return int(x / 1000 * self._browser_computer.screen_size()[0])

    def denormalize_y(self, y: int) -> int:
        return int(y / 1000 * self._browser_computer.screen_size()[1])
