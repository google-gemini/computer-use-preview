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
from typing import Literal
from google import genai
from google.genai import types
import termcolor
from google.genai.types import (
    Part,
    GenerateContentConfig,
    Content,
    Candidate,
    FunctionResponse,
)
import base64
import time
from rich.console import Console
from rich.table import Table

from computers import EnvState, Computer

console = Console()


class BrowserAgent:
    def __init__(
        self,
        browser_computer: Computer,
        query: str,
        model_name: Literal[
            "models/computer-use-exp"
        ] = "models/computer-use-exp",
    ):
        self._browser_computer = browser_computer
        self._query = query
        self._model_name = model_name
        self._client = genai.Client(
            api_key=os.environ.get("GEMINI_API_KEY"),
        )
        self._contents: list[Content] = [
            Content(
                role="user",
                parts=[
                    Part(text=self._query),
                ],
            )
        ]
        self._generate_content_config = GenerateContentConfig(
            temperature=1,
            top_p=0.95,
            top_k=40,
            max_output_tokens=8192,
            tools=[
                types.Tool(
                    computer_use=types.ComputerUse(
                        environment=types.Environment.ENVIRONMENT_BROWSER
                    )
                )
            ],
        )

    def handle_action(self, action: types.FunctionCall) -> EnvState:
        """Handles the action and returns the environment state."""
        match action.name:
            case "open_web_browser":
                return self._browser_computer.open_web_browser()
            case "click_at":
                x = self.normalize_x(action.args["x"])
                y = self.normalize_y(action.args["y"])
                return self._browser_computer.click_at(
                    x=x,
                    y=y,
                )
            case "hover_at":
                x = self.normalize_x(action.args["x"])
                y = self.normalize_y(action.args["y"])
                return self._browser_computer.hover_at(
                    x=x,
                    y=y,
                )
            case "type_text_at":
                x = self.normalize_x(action.args["x"])
                y = self.normalize_y(action.args["y"])
                return self._browser_computer.type_text_at(
                    x=x,
                    y=y,
                    text=action.args["text"],
                )
            case "scroll_document":
                return self._browser_computer.scroll_document(action.args["direction"])
            case "wait_5_seconds":
                return self._browser_computer.wait_5_seconds()
            case "go_back":
                return self._browser_computer.go_back()
            case "go_forward":
                return self._browser_computer.go_forward()
            case "search":
                return self._browser_computer.search()
            case "navigate":
                return self._browser_computer.navigate(action.args["url"])
            case "key_combination":
                return self._browser_computer.key_combination(
                    action.args["keys"].split("+")
                )
            case _:
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

    def get_text(self, candidate: Candidate) -> str | None:
        """Extracts the text from the candidate."""
        text = []
        for part in candidate.content.parts:
            if part.text:
                text.append(part.text)
        return " ".join(text) or None

    def get_function_call(self, candidate: Candidate) -> types.FunctionCall | None:
        """Extracts the function call from the candidate."""
        for part in candidate.content.parts:
            if part.function_call:
                return part.function_call
        return None

    def run_one_iteration(self) -> Literal["COMPLETE", "CONTINUE"]:
        # Generate a response from the model.
        with console.status("Generating response from Gemini...", spinner_style=None):
            try:
                response = self.get_model_response()
            except Exception as e:
                return "COMPLETE"

        # Extract the text and function call from the response.
        candidate = response.candidates[0]
        reasoning = self.get_text(candidate)
        function_call = self.get_function_call(candidate)

        # Append the model turn.
        self._contents.append(candidate.content)

        if not function_call or not function_call.name:
            print(f"Agent Loop Complete: {reasoning}")
            return "COMPLETE"

        # Print the function call and any reasoning.
        function_call_str = f"Name: {function_call.name}"
        if function_call.args:
            function_call_str += f"\nArgs:"
            for key, value in function_call.args.items():
                function_call_str += f"\n  {key}: {value}"
        table = Table(expand=True)
        table.add_column("Gemini Reasoning", header_style="magenta", ratio=1)
        table.add_column("Function Call", header_style="cyan", ratio=1)
        table.add_row(
            reasoning,
            function_call_str,
        )
        console.print(table)
        print()

        if safety := function_call.args.get("safety_decision"):
            match safety["decision"]:
                case "block":
                    termcolor.cprint(
                        "Terminating loop due to safety block!",
                        color="yellow",
                        attrs=["bold"],
                    )
                    print(safety["explanation"])
                    return "COMPLETE"
                case "require_confirmation":
                    termcolor.cprint(
                        "Safety service requires explicit confirmation!",
                        color="yellow",
                        attrs=["bold"],
                    )
                    print(safety["explanation"])
                    decision = ""
                    while decision.lower() not in ("y", "n", "ye", "yes", "no"):
                        decision = input("Do you wish to proceed? [Y]es/[n]o\n")
                    if decision.lower() in ("n", "no"):
                        print("Terminating agent loop.")
                        return "COMPLETE"
                    print("Proceeding with agent loop.\n")

        with console.status("Sending command to Computer...", spinner_style=None):
            environment_state = self.handle_action(function_call)

        self._contents.append(
            Content(
                role="user",
                parts=[
                    Part(
                        function_response=FunctionResponse(
                            name=function_call.name,
                            response={
                                "image": {
                                    "mimetype": "image/png",
                                    "data": base64.b64encode(
                                        environment_state.screenshot
                                    ).decode("utf-8"),
                                },
                                "url": environment_state.url,
                            },
                        )
                    )
                ],
            )
        )
        return "CONTINUE"

    def agent_loop(self):
        while True:
            status = self.run_one_iteration()
            if status == "COMPLETE":
                return

    def normalize_x(self, x: int) -> int:
        return int(x / 1000 * self._browser_computer.screen_size()[0])

    def normalize_y(self, y: int) -> int:
        return int(y / 1000 * self._browser_computer.screen_size()[1])
