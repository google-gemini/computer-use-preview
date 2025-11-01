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

from agent import BrowserAgent
from computers import BrowserbaseComputer, PlaywrightComputer, AgentCoreComputer


PLAYWRIGHT_SCREEN_SIZE = (1440, 900)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the browser agent with a query.")
    parser.add_argument(
        "--query",
        type=str,
        required=True,
        help="The query for the browser agent to execute.",
    )

    parser.add_argument(
        "--env",
        type=str,
        choices=("playwright", "browserbase", "agentcore"),
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
        "--recording_bucket",
        type=str,
        default=None,
        help="S3 bucket for AgentCore session recording (agentcore only).",
    )
    parser.add_argument(
        "--recording_prefix",
        type=str,
        default="recordings",
        help="S3 prefix for AgentCore session recording (agentcore only).",
    )
    parser.add_argument(
        "--execution_role_arn",
        type=str,
        default=None,
        help="IAM execution role ARN for AgentCore browser (required when using recording).",
    )
    parser.add_argument(
        "--create_execution_role",
        action="store_true",
        default=False,
        help="Auto-create IAM execution role if it doesn't exist (agentcore only).",
    )
    parser.add_argument(
        "--browser_identifier",
        type=str,
        default=None,
        help="Browser identifier for AgentCore (agentcore only). Defaults to AGENTCORE_BROWSER_IDENTIFIER env var or 'aws.browser.v1'.",
    )
    parser.add_argument(
        "--model",
        default='gemini-2.5-computer-use-preview-10-2025',
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
    elif args.env == "agentcore":
        env = AgentCoreComputer(
            screen_size=PLAYWRIGHT_SCREEN_SIZE,
            initial_url=args.initial_url,
            recording_bucket=args.recording_bucket,
            recording_prefix=args.recording_prefix,
            execution_role_arn=args.execution_role_arn,
            create_execution_role=args.create_execution_role,
            browser_identifier=args.browser_identifier,
        )
    else:
        raise ValueError("Unknown environment: ", args.env)

    with env as browser_computer:
        agent = BrowserAgent(
            browser_computer=browser_computer,
            query=args.query,
            model_name=args.model,
        )
        agent.agent_loop()
    return 0


if __name__ == "__main__":
    main()
