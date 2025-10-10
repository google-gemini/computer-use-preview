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
from config import get_config
from exceptions import ConfigurationError


def main() -> int:
    # 加载配置
    config = get_config()
    
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
        default=None,  # 将从配置获取默认值
        help="The initial URL loaded for the computer.",
    )
    parser.add_argument(
        "--highlight_mouse",
        action="store_true",
        default=None,  # 将从配置获取默认值
        help="If possible, highlight the location of the mouse.",
    )
    parser.add_argument(
        "--model",
        default=None,  # 将从配置获取默认值
        help="Set which main model to use.",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to custom configuration file.",
    )
    args = parser.parse_args()

    # 如果提供了自定义配置文件，重新加载配置
    if args.config:
        config = get_config(args.config)

    # 使用命令行参数覆盖配置，如果参数提供了值的话
    initial_url = args.initial_url or (
        config.playwright.initial_url if args.env == "playwright" 
        else config.browserbase.initial_url
    )
    
    highlight_mouse = args.highlight_mouse if args.highlight_mouse is not None else config.playwright.highlight_mouse
    model_name = args.model or config.model.name

    # 获取屏幕大小配置
    screen_size = config.browser.screen_size

    try:
        if args.env == "playwright":
            env = PlaywrightComputer(
                screen_size=screen_size,
                initial_url=initial_url,
                highlight_mouse=highlight_mouse,
            )
        elif args.env == "browserbase":
            env = BrowserbaseComputer(
                screen_size=screen_size,
                initial_url=initial_url
            )
        else:
            raise ConfigurationError(f"Unknown environment: {args.env}", "env", args.env)

        with env as browser_computer:
            agent = BrowserAgent(
                browser_computer=browser_computer,
                query=args.query,
                model_name=model_name,
            )
            agent.agent_loop()
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    main()
