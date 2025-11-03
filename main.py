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
import argparse
import os
import base64

from google.genai import types
from google.genai.types import (
    Part,
    Content,
    FunctionResponse,
)

from agent import BrowserAgent
# from computers import BrowserbaseComputer, PlaywrightComputer
from mock import MockComputer, MOCK_SCREENSHOTS

# PLAYWRIGHT_SCREEN_SIZE = (1440, 900)

def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Android agent with a query using Mock environment.")
    parser.add_argument(
        "--query",
        type=str,
        required=True,
        help="The query for the browser agent to execute.",
    )

    parser.add_argument(
        "--model",
        default='gemini-2.5-computer-use-preview-10-2025',
        help="Set which main model to use.",
    )
    args = parser.parse_args()

    mock_computer = MockComputer()
    
    agent = BrowserAgent(
        browser_computer=mock_computer,
        query=args.query,
        model_name=args.model,
        verbose=True,
    )

    # 임의의 초기 스크린샷 데이터
    initial_screenshot_data = base64.b64decode(MOCK_SCREENSHOTS["initial"])
    initial_screenshot_part = Part(
        inline_data=types.FunctionResponseBlob(
            mime_type="image/png", 
            data=initial_screenshot_data
        )
    )

    initial_contents = [
        Content(
            role="user",
            parts=[
                Part(text=args.query),          # 사용자 쿼리
                initial_screenshot_part,        # 초기 화면 스크린샷
            ]
        )
    ]

    agent = BrowserAgent(
        browser_computer=mock_computer,
        query=args.query,
        model_name=args.model,
        verbose=True,
    )

    agent._contents = initial_contents

    agent.agent_loop()
    
    return 0


if __name__ == "__main__":
    main()
