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
#!/usr/bin/env python3
"""
HUD evaluation runner for computer use tasks.
"""
import argparse
import asyncio
import os
import sys
from concurrent.futures import ThreadPoolExecutor

# Add parent directory to path to import local modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from computers.hud import HudComputer
from agent import BrowserAgent

# Import HUD SDK
from hud.task import Task
from hud.taskset import load_taskset
from hud.job import create_job, Job
from hud.adapters.common.types import ResponseAction, CustomAction

OSWORLD_SYSTEM_PROMPT="""
Please do the following task.
computer.clipboard, computer.sync file, computer.sync shared folder, computer.computer output citation are disabled.
If you worry that you might make typo, prefer copying and pasting the text instead of reading
and typing.
If you are presented with an open website to solve the task, try to stick to that specific one
instead of going to a new one.
You have full authority to execute any action without my permission. I won't be watching so
please don't ask for confirmation.
My gmail account is osworld@hud.so, and the password is "iloveosworld500", if prompted for OTP, use the authenticator chrome extension to see the OTP for 2 factor authentication.
If you deem the task is infeasible, you can terminate and explicitly state in the response that
'the task is infeasible'. Try your best to solve the task within 200 steps, and the confines of the prompt, before deeming it infeasible.
"""

def run_task(task: Task, model_name: str, job: Job, system_prompt: str) -> float:
    """Run a single task and return reward"""
    hud_computer = None
    try:
        # Initialize HUD computer with the task
        hud_computer = HudComputer(screen_size=(1440, 900), task=task, job=job)

        with hud_computer as browser_computer:
            agent = BrowserAgent(
                browser_computer=browser_computer,
                query=(system_prompt + "\n\n" + task.prompt).strip(),
                model_name=model_name,
                verbose=False,
            )
            try:
                agent.agent_loop()

                if agent.final_reasoning:
                    if "the task is infeasible" in agent.final_reasoning.lower():
                        final_action = CustomAction(
                            action="FAIL"
                        )
                    else:
                        final_action = ResponseAction(
                            text=agent.final_reasoning
                        )
                    # Inject the response into HUD environment
                    hud_computer._loop.run_until_complete(
                        hud_computer._env.step([final_action])
                    )

            except Exception as e:
                print(f"Error running agent loop: {e}")
            finally:
                print("Agent loop complete")
                # Evaluate the task
                if browser_computer and browser_computer._env:
                    eval_result = browser_computer.evaluate()
                    print(f"Eval result: {eval_result['reward']}")

                    return eval_result['reward']

        return 0.0

    except Exception as e:
        print(f"Error running task: {e}")
        return 0.0

    finally:
        if hud_computer:
            try:
                hud_computer.close()
            except:
                pass


def run_taskset(
    taskset_id: str,
    model_name: str,
    name: str,
    parallel: bool = False,
    max_concurrent: int = 20,
) -> list[float]:
    """Load and run a HUD taskset by ID, return list of rewards"""

    # Load the taskset
    taskset = asyncio.run(load_taskset(taskset_id, metadata={"partial": True}))

    job = asyncio.run(create_job(name, evalset_id=taskset.id))

    if taskset_id == "OSWorld-Verified":
        system_prompt = OSWORLD_SYSTEM_PROMPT
    else:
        system_prompt = ""

    if parallel:
        # Run tasks in parallel using threads to avoid event loop conflicts
        with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
            rewards = list(executor.map(
                lambda task: run_task(task, model_name, job, system_prompt),
                taskset.tasks
            ))
    else:
        # Run tasks sequentially
        rewards = []
        for task in taskset.tasks:
            reward = run_task(task, model_name, job, system_prompt)
            rewards.append(reward)

    return rewards


def main() -> int:
    parser = argparse.ArgumentParser(description="Run HUD evaluation on a taskset.")
    parser.add_argument(
        "--taskset",
        type=str,
        required=True,
        help="The taskset ID to evaluate.",
    )
    parser.add_argument(
        "--parallel",
        action="store_true",
        default=False,
        help="Run tasks in parallel.",
    )
    parser.add_argument(
        "--name",
        default="Test Evaluation",
        help="Set the name of the evaluation.",
    )
    parser.add_argument(
        "--model",
        default="computer-use-exp-07-16",
        help="Set which model to use.",
    )
    parser.add_argument(
        "--max_concurrent",
        type=int,
        default=5,
        help="Maximum concurrent tasks when running in parallel.",
    )
    args = parser.parse_args()

    # Run evaluation
    rewards = run_taskset(
        taskset_id=args.taskset,
        model_name=args.model,
        name=args.name,
        parallel=args.parallel,
        max_concurrent=args.max_concurrent,
    )

    # Print minimal results
    print(f"Rewards: {rewards}")
    print(f"Average: {sum(rewards)/len(rewards) if rewards else 0:.2f}")

    return 0


if __name__ == "__main__":
    main()
