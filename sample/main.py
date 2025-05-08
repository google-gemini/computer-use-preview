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

from cloud_run_env import CloudRunComputer
from playwright_env import PlaywrightComputer
from agent import BrowserAgent
from browserbase_env import BrowserbaseComputer


SCREEN_SIZE = (1000, 1000)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the browser agent with a query.")
    parser.add_argument(
        "--query",
        type=str,
        required=True,
        help="The query for the browser agent to execute.",
    )
    parser.add_argument(
        "--api_server",
        type=str,
        help="The URL of the API Server for the cloud run environment.",
    )
    parser.add_argument(
        "--env",
        type=str,
        choices=("cloud-run", "playwright", "browserbase"),
        default="cloud-run",
        help="The computer use environment to use.",
    )
    parser.add_argument(
        "--initial_url",
        type=str,
        default="https://www.google.com",
        help="The inital URL loaded for the computer (currently only works for local playwright).",
    )
    args = parser.parse_args()

    match args.env:
        case "cloud-run":
            assert args.api_server, "--api_server is required for cloud run."
            env = CloudRunComputer(api_server=args.api_server, screen_size=SCREEN_SIZE)
        case "playwright":
            env = PlaywrightComputer(screen_size=SCREEN_SIZE, initial_url=args.initial_url)
        case "browserbase":
            env = BrowserbaseComputer(screen_size=SCREEN_SIZE)

    with env as browser_computer:
        agent = BrowserAgent(
            browser_computer=browser_computer,
            query=args.query,
        )
        agent.agent_loop()
    return 0


if __name__ == "__main__":
    main()
