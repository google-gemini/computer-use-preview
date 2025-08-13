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


def run_task(task: Task, model_name: str, job: Job) -> float:
    """Run a single task and return reward"""
    hud_computer = None
    try:
        # Initialize HUD computer with the task
        hud_computer = HudComputer(screen_size=(1440, 900), task=task, job=job)
        
        with hud_computer as browser_computer:
            agent = BrowserAgent(
                browser_computer=browser_computer,
                query=task.prompt,
                model_name=model_name,
                verbose=False,
                max_screenshots=1,
            )
            agent.agent_loop()
        
            # Evaluate the task
            if browser_computer and browser_computer._env:
                eval_result = browser_computer.evaluate()
                print(f"Eval result: {eval_result}")

                return eval_result["reward"]
        
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
    parallel: bool = False,
    max_concurrent: int = 20,
    api_key: str = None
) -> list[float]:
    """Load and run a HUD taskset by ID, return list of rewards"""
    
    # Load the taskset
    taskset = asyncio.run(load_taskset(taskset_id, api_key=api_key))

    job = asyncio.run(create_job("SheetBench Evaluation", evalset_id=taskset.id))
    
    if parallel:
        # Run tasks in parallel using threads to avoid event loop conflicts
        with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
            rewards = list(executor.map(
                lambda task: run_task(task, model_name, job),
                taskset.tasks
            ))
    else:
        # Run tasks sequentially
        rewards = []
        for task in taskset.tasks:
            reward = run_task(task, model_name, job)
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
        "--model",
        default="computer-use-exp-07-16",
        help="Set which model to use.",
    )
    parser.add_argument(
        "--api_key",
        type=str,
        help="HUD API key (defaults to environment variable).",
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
        parallel=args.parallel,
        max_concurrent=args.max_concurrent,
        api_key=args.api_key or os.environ.get("HUD_API_KEY")
    )
    
    # Print minimal results
    print(f"Rewards: {rewards}")
    print(f"Average: {sum(rewards)/len(rewards) if rewards else 0:.2f}")
    
    return 0


if __name__ == "__main__":
    main()