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
from typing import Literal, Optional, Union, Any, Dict

import termcolor
from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.types import (
    Content, 
    Part, 
    Candidate, 
    FunctionCall, 
    FunctionResponse, 
    GenerateContentConfig, 
    FinishReason, 
    Blob
)
from rich.console import Console
from rich.table import Table

# load environment variable in .env
load_dotenv()
console = Console()

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
        model_name: str = 'gemini-2.5-computer-use-preview-10-2025',
        verbose: bool = True,
    ):
        self._model_name = model_name
        self._verbose = verbose
        self._client = genai.Client(
            api_key=os.environ.get("GEMINI_API_KEY"),
            vertexai=os.environ.get("USE_VERTEXAI", "0").lower() in ["true", "1"],
            project=os.environ.get("VERTEXAI_PROJECT"),
            location=os.environ.get("VERTEXAI_LOCATION"),
        )
        self._contents: list[Content] = [] # 대화 히스토리

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
                # AFC 메시지 해결 필요
                types.Tool(
                    function_declarations=custom_functions
                )
            ],
        )

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
    
    def _run_one_iteration(self) -> Literal["COMPLETE", "CONTINUE"]:
        """[CUAgent 내부] LLM을 호출하고 응답을 파싱합니다."""
        if self._verbose:
            print("[CUAgent] Gemini Thinking...")
        try:
            response = self.get_model_response()
        except Exception as e:
            return {"type": "ERROR", "message": f"Model generation error: {e}"}
        
        if not response.candidates:
            return {"type": "ERROR", "message": "No response from model."}

        # Extract the text and function call from the response.
        candidate = response.candidates[0]
        # Append the model turn to conversation history.
        if candidate.content:
            self._contents.append(candidate.content)

        reasoning = self.get_text(candidate)
        function_calls = self.extract_function_calls(candidate)

        if function_calls:
            fc = function_calls[0]
            
            if self._verbose:
                # 기존 테이블 출력 로직 복원
                function_call_strs = []
                function_call_str = f"Name: {fc.name}"
                if fc.args:
                    function_call_str += f"\nArgs:"
                    for key, value in fc.args.items():
                        function_call_str += f"\n  {key}: {value}"
                function_call_strs.append(function_call_str)

                table = Table(expand=True)
                table.add_column(
                    "Gemini Computer Use Reasoning", header_style="magenta", ratio=1
                )
                table.add_column("Function Call(s)", header_style="cyan", ratio=1)
                table.add_row(reasoning, "\n".join(function_call_strs))
                console.print(table)
                print()
            
            return {
                "type": "ACTION",
                "action": fc.name,
                "args": dict(fc.args)
            }
        
        # Function Call이 없는 경우 (Reasoning = 최종 응답)
        if reasoning:
            if self._verbose:
                print(f"[CUAgent] Final Response: {reasoning}")
            return {
                "type": "RESPONSE",
                "message": reasoning
            }

        return {"type": "ERROR", "message": "CUAgent: Unknown model response type."}
    
    def init_task(self, instruction: str, screenshot_data: Optional[bytes], url_or_activity: Optional[str]) -> Dict[str, Any]:
        """[서버] 새 작업을 시작합니다."""
        if self._verbose:
            print(f"[CUAgent] init_task: 새 작업 시작 (Instruction: {instruction})")
            
        parts = [Part(text=instruction)]
        if screenshot_data:
             parts.append(Part(inline_data=types.Blob(mime_type="image/png", data=screenshot_data)))
             parts.append(Part(text=f"현재 화면 상태: {url_or_activity or 'unknown'}"))
        else:
            parts.append(Part(text="현재 화면 정보 없음."))
            
        self._contents = [Content(role="user", parts=parts)]
        return self._run_and_parse_response()

    def step(self, previous_action: Dict[str, Any], current_screenshot_data: bytes, current_activity: Optional[str]) -> Dict[str, Any]:
        """[서버] 이전 액션의 결과(새 스크린샷)를 받아 다음 추론을 수행합니다."""
        if self._verbose:
            print(f"[CUAgent] step: 이전 액션 '{previous_action['action']}'의 결과 수신")

        self._contents.append(
            Content(
                role="user",
                parts=[
                    Part(
                        function_response=FunctionResponse(
                            name=previous_action['action'],
                            response={"result": "Action executed by client successfully."},
                        )
                    ),
                    Part(inline_data=types.Blob(mime_type="image/png", data=current_screenshot_data)),
                    Part(text=f"액션 수행 후 현재 화면 상태: {current_activity or 'unknown'}. 다음 행동 결정.")
                ]
            )
        )
        return self._run_and_parse_response()
