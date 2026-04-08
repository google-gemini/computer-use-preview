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
import json
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

from agent import BrowserAgent
from computers import EnvState, Computer

MAX_RECENT_TURN_WITH_SCREENSHOTS = 3
PREDEFINED_COMPUTER_USE_FUNCTIONS = [
    "open_web_browser",
    "click_at",
    "hover_at",
    "type_text_at",
    "scroll_document",
    "scroll_at",
    "wait_5_seconds",
    "go_back",
    "go_forward",
    "search",
    "navigate",
    "key_combination",
    "drag_and_drop",
]


console = Console()

# Built-in Computer Use tools will return "EnvState".
# Custom provided functions will return "dict".
FunctionResponseT = Union[EnvState, dict]


def read_data_from_json(file_path: str) -> dict:
    """Reads data from a JSON file and returns it as a dictionary."""
    with open(file_path, 'r') as f:
        data = json.load(f)
    return data


def ask_for_help(question: str) -> str:
    """Asks the user for help with a specific question."""
    return input(question)


class FormAgent(BrowserAgent):
    def __init__(
        self,
        browser_computer: Computer,
        query: str,
        model_name: str,
        verbose: bool = True,
        can_ask_for_help: bool = False,
    ):
        super().__init__(browser_computer, query, model_name, verbose)
        self.can_ask_for_help = can_ask_for_help

        # Add your own custom functions here.
        custom_functions = [
            types.FunctionDeclaration.from_callable(
                client=self._client, callable=read_data_from_json
            )
        ]
        if self.can_ask_for_help:
            custom_functions.append(
                types.FunctionDeclaration.from_callable(
                    client=self._client, callable=ask_for_help
                )
            )

        self._generate_content_config = GenerateContentConfig(
            temperature=1,
            top_p=0.95,
            top_k=40,
            max_output_tokens=8192,
            tools=[
                types.Tool(
                    computer_use=types.ComputerUse(
                        environment=types.Environment.ENVIRONMENT_BROWSER,
                    ),
                ),
                types.Tool(function_declarations=custom_functions),
            ],
        )

    def handle_action(self, action: types.FunctionCall) -> FunctionResponseT:
        """Handles the action and returns the environment state."""
        if action.name == read_data_from_json.__name__:
            return read_data_from_json(action.args["file_path"])
        elif action.name == ask_for_help.__name__ and self.can_ask_for_help:
            return {"response": ask_for_help(action.args["question"])}
        else:
            return super().handle_action(action)
