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
from computers import BrowserbaseComputer, PlaywrightComputer


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
        default='gemini-2.5-computer-use-preview-10-2025',
        help="Set which main model to use.",
    )
    parser.add_argument(
        "--chrome_profile",
        type=str,
        default=None,
        help="Path to Chrome user data directory (profile) to use. You can use your regular Chrome profile. "
             "Common locations: macOS: ~/Library/Application Support/Google/Chrome/User Data/Profile 1, "
             "Linux: ~/.config/google-chrome/Default, Windows: %%LOCALAPPDATA%%\\Google\\Chrome\\User Data\\Default. "
             "Find your exact path in Chrome by visiting chrome://version/ and looking for 'Profile Path'. "
             "If not specified, a temporary profile will be used.",
    )
    parser.add_argument(
        "--use_system_chrome",
        action="store_true",
        default=False,
        help="Use system Chrome executable instead of Playwright's bundled Chromium. "
             "This can work better with existing Chrome profiles and managed profiles.",
    )
    args = parser.parse_args()

    # Expand user profile path if provided
    user_data_dir = None
    if args.chrome_profile:
        # Expand ~ to home directory
        user_data_dir = os.path.expanduser(args.chrome_profile)
        # Convert to absolute path
        user_data_dir = os.path.abspath(user_data_dir)
        
        # Validate that the directory exists
        if not os.path.isdir(user_data_dir):
            print(f"Error: Chrome profile directory does not exist: {user_data_dir}")
            print(f"Please check the path and ensure Chrome is closed before using the profile.")
            return 1
        
        print(f"Using Chrome profile: {user_data_dir}")

    if args.env == "playwright":
        env = PlaywrightComputer(
            screen_size=PLAYWRIGHT_SCREEN_SIZE,
            initial_url=args.initial_url,
            highlight_mouse=args.highlight_mouse,
            user_data_dir=user_data_dir,
            use_system_chrome=args.use_system_chrome,
        )
    elif args.env == "browserbase":
        env = BrowserbaseComputer(
            screen_size=PLAYWRIGHT_SCREEN_SIZE,
            initial_url=args.initial_url
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
