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

from chat_agent import ChatAgent
from browser_agent import BrowserAgent
from computers import BrowserbaseComputer, PlaywrightComputer

PLAYWRIGHT_SCREEN_SIZE = (1440, 900)

def main() -> int:
    parser = argparse.ArgumentParser(description="Run the browser agent with a query.")
    parser.add_argument(
        "--env",
        type=str,
        choices=("playwright", "browserbase"),
        default="playwright",
        help="The computer use environment to use.",
    )
    parser.add_argument(
        "--initial_url",
        type=str,
        default="https://www.google.com",
        help="The inital URL loaded for the computer.",
    )
    parser.add_argument(
        "--highlight_mouse",
        action="store_true",
        default=False,
        help="If possible, highlight the location of the mouse.",
    )
    parser.add_argument(
        "--model",
        default='gemini-2.5-flash',
        help="Set which main model to use.",
    )
    args = parser.parse_args()

    if args.env == "playwright":
        env = PlaywrightComputer(
            screen_size=PLAYWRIGHT_SCREEN_SIZE,
            initial_url=args.initial_url,
            highlight_mouse=args.highlight_mouse,
        )
    elif args.env == "browserbase":
        env = BrowserbaseComputer(
            screen_size=PLAYWRIGHT_SCREEN_SIZE,
            initial_url=args.initial_url
        )
    else:
        raise ValueError("Unknown environment: ", args.env)

    with env as browser_computer:
        browser_agent = BrowserAgent(
            browser_computer=browser_computer,
            model_name="gemini-2.5-computer-use-preview-10-2025"
        )
        char_agent = ChatAgent(
            model_name=args.model,
            browser_agent=browser_agent
        )
        char_agent.agent_loop()
    return 0

if __name__ == "__main__":
    main()
