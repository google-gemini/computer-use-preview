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

from chat_agent import ChatAgent
from cu_agent import CUAgent

from mock import MockComputer, MOCK_SCREENSHOTS

def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Android agent with a query using Mock environment.")
    # parser.add_argument(
    #     "--query",
    #     type=str,
    #     required=True,
    #     help="The query for the browser agent to execute.",
    # )
    # parser.add_argument(
    #     "--model",
    #     default='gemini-2.5-flash',
    #     help="Set the model to use for the Chat Agent.",
    # )
    # args = parser.parse_args()

    mock_computer = MockComputer()

    cu_agent = CUAgent(
        browser_computer=mock_computer,
        model_name='gemini-2.5-computer-use-preview-10-2025', # GCU 전용 모델 하드코딩 유지
        verbose=True,
    )

    chat_agent = ChatAgent(
        cu_agent=cu_agent, # GCUAgent 주입
        model_name='gemini-2.5-flash',
        verbose=True,
    )

    chat_agent.start_chat_loop()

    return 0

if __name__ == "__main__":
    main()
