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

import computer_use_environment


class BrowserAgent:
    def __init__(
        self,
        browser_computer: computer_use_environment.ComputerUseEnvironment,
        query: str,
        model_name: Literal[
            "models/gemini-2.5-pro-jarvis"
        ] = "models/gemini-2.5-pro-jarvis",
    ):
        assert "jarvis" in model_name
        self._browser_computer = browser_computer
        self._query = query
        self._model_name = model_name
        self.client = genai.Client(
            api_key=os.environ.get("GEMINI_API_KEY"),
            http_options=types.HttpOptions(
                api_version="v1alpha",
                base_url="https://autopush-generativelanguage.sandbox.googleapis.com",
            ),
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

    def handle_action(
        self, action: types.FunctionCall
    ) -> computer_use_environment.EnvState:
        """Handles the action and returns the environment state."""
        match action.name:
            case "open_web_browser":
                return self._browser_computer.open_web_browser()
            case "click_at":
                y = action.args["y"]
                x = action.args["x"]
                x = self.normalize_x(x)
                y = self.normalize_y(y)
                return self._browser_computer.click_at(
                    x=x,
                    y=y,
                )
            case "hover_at":
                y = action.args["y"]
                x = action.args["x"]
                x = self.normalize_x(x)
                y = self.normalize_y(y)
                return self._browser_computer.hover_at(
                    x=x,
                    y=y,
                )
            case "type_text_at":
                y = action.args["y"]
                x = action.args["x"]
                x = self.normalize_x(x)
                y = self.normalize_y(y)
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
        response = self.client.models.generate_content(
            model=self._model_name,
            contents=self._contents,
            config=self._generate_content_config,
        )

        # Extract the text and function call from the response.
        candidate = response.candidates[0]
        text = self.get_text(candidate)
        function_call = self.get_function_call(candidate)

        # Append the model turn.
        self._contents.append(candidate.content)

        if text:
            termcolor.cprint(
                "Agent Reasoning",
                color="magenta",
                attrs=["bold"],
            )
            print(text)
            print()

        if not function_call:
            print("Agent Loop Complete.")
            return

        termcolor.cprint(
            "Agent Function Call",
            color="yellow",
            attrs=["bold"],
        )
        print(function_call.model_dump_json())
        print()
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

    def agent_loop(self):
        while True:
            status = self.run_one_iteration()
            if status == "COMPLETE":
                return

    def normalize_x(self, x: int) -> int:
        return int(x / 1000 * self._browser_computer.screen_size()[0])

    def normalize_y(self, y: int) -> int:
        # Note: the model measures the y coordinate from the bottom of the screen,
        # but traditionally image coordinates are measured from the top. We must
        # invert the y coordinate to get the correct position.
        return self._browser_computer.screen_size()[1] - int(
            y / 1000 * self._browser_computer.screen_size()[1]
        )
