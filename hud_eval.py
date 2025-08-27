#!/usr/bin/env python3
"""
HUD evaluation runner using MCPComputer with existing BrowserAgent.
"""
import argparse
import os
import sys
from typing import Optional, List
from concurrent.futures import ThreadPoolExecutor

# Add parent directory to path to import local modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from computers import HudComputer
from agent import BrowserAgent

# Import HUD SDK
import hud
from hud.datasets import Task
from hud.agents.base import find_reward, find_content
from datasets import load_dataset as hf_load_dataset

from rich.console import Console

console = Console()

# Optional: Instrument BrowserAgent methods if HUD_INSTRUMENT env var is set
if os.getenv("HUD_INSTRUMENT", "true").lower() in ("true", "1", "yes"):
    try:
        # Instrument the get_model_response method for LLM telemetry
        BrowserAgent.get_model_response = hud.instrument(
            span_type="agent",
            name="BrowserAgent.get_model_response",
            record_args=False,
            record_result=True,
        )(BrowserAgent.get_model_response)
        
        console.print("✓ [green]HUD instrumentation enabled for BrowserAgent[/green]")
    except Exception as e:
        console.print(f"[yellow]Warning: Could not enable instrumentation: {e}[/yellow]")

def run_single_task(
    task: Task,
    model: str = "computer-use-exp-07-16",
    verbose: bool = False,
    job_id: Optional[str] = None,
) -> dict:
    """
    Run a single task using MCPComputer and BrowserAgent.
    
    Args:
        task: HUD Task object with mcp_config
        model: Model name to use
        verbose: Enable verbose output
            
    Returns:
        Dict with reward and info
    """
    result = {"reward": 0.0, "info": {}}
    
    # Build full prompt
    prompt = task.system_prompt + "\n\n" + task.prompt

    trace_id = None
    try:
        # Create HudComputer with task's MCP config
        with hud.trace(name=task.prompt, job_id=job_id) as trace_id, HudComputer(
            mcp_config=task.mcp_config,
            screen_size=(1448, 944),
            task_prompt=prompt,
        ) as computer:
            console.print(f"See trace at: https://app.hud.so/trace/{trace_id}")
            
            try:
                # Run agent
                agent = BrowserAgent(
                    browser_computer=computer,
                    query=prompt,
                    model_name=model,
                    verbose=verbose
                )

                # Setup task
                try:
                    computer._loop.run_until_complete(
                        computer._client.call_tool(task.setup_tool)
                    )
                except Exception as e:
                    console.error(f"Could not setup task: {e}")

                # Get initial state
                computer.get_initial_state()

                # Run agent loop
                agent.agent_loop()
                    
                # Check final reasoning
                response = agent.final_reasoning
                if agent.final_reasoning:
                    try:
                        computer._loop.run_until_complete(
                            computer._client.call_tool(name="response", arguments={"response": response})
                        )
                    except Exception as e:
                        console.error(f"Could not submit response: {e}")

            except Exception as e:
                console.error(f"Error running task: {e}")
            except KeyboardInterrupt:
                console.error("Keyboard interrupt")
            finally:
                # Evaluate while computer context is still active
                try:
                    results = computer._loop.run_until_complete(
                        computer._client.call_tool(task.evaluate_tool)
                    )
                    reward = find_reward(results[0])
                    eval_content = find_content(results[0])

                    result["reward"] = reward
                    result["info"]["eval_content"] = eval_content
                    computer._loop.run_until_complete(
                        computer._client.shutdown()
                    )
                except Exception as e:
                    console.error(f"Could not get reward: {e}")
    
                if trace_id:
                    console.print(f"See trace at: https://app.hud.so/trace/{trace_id}")
                    
    except Exception as e:
        if verbose:
            console.error(f"Error running task: {e}")

    return result


def evaluate_dataset(
    dataset_name: str,
    model: str = "computer-use-exp-07-16",
    job_id: Optional[str] = None,
    max_concurrent: int = 5,
    verbose: bool = False,
    limit: Optional[int] = None,
) -> List[dict]:
    """
    Run evaluation on a HUD dataset.
    
    Args:
        dataset_name: HuggingFace dataset ID (e.g. "hud-evals/sheetbench-50")
        model: Model name to use
        job_id: ID for the evaluation job
        max_concurrent: Maximum parallel tasks
        verbose: Enable verbose output
        limit: Limit number of tasks to run
        
    Returns:
        List of result dicts
    """
    # Configure telemetry once before parallel execution to avoid race conditions
    try:
        from hud.otel import configure_telemetry, is_telemetry_configured
        if not is_telemetry_configured():
            configure_telemetry()
    except ImportError:
        pass  # HUD not available
    
    # Load dataset
    console.print(f"Loading dataset: {dataset_name}")
    dataset = hf_load_dataset(dataset_name, split="train")
    
    # Get tasks - convert dataset items to Task objects
    tasks = []
    for item in dataset:
        # HUD datasets store tasks as dicts
        if isinstance(item, dict):
            task = Task(**item)
            tasks.append(task)
        elif isinstance(item, Task):
            tasks.append(item)
    if limit:
        tasks = tasks[:limit]
    
    console.print(f"Running {len(tasks)} tasks...")
    
    # Run tasks in parallel using ThreadPoolExecutor to avoid event loop conflicts
    with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
        # Submit all tasks to the executor
        futures = [
            executor.submit(run_single_task, task, model, verbose, job_id)
            for task in tasks
        ]
        
        # Collect results as they complete
        results = []
        for future in futures:
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                results.append({
                    "reward": 0.0,
                    "info": {"error": str(e), "status": "exception"}
                })
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Run HUD evaluation using MCPComputer with BrowserAgent."
    )
    parser.add_argument(
        "--dataset",
        type=str,
        required=True,
        help="HuggingFace dataset ID (e.g., 'hud-evals/sheetbench-50')",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="computer-use-exp-07-16",
        help="Model name to use",
    )
    parser.add_argument(
        "--name",
        type=str,
        help="Name for the evaluation job",
    )
    parser.add_argument(
        "--max-concurrent",
        type=int,
        default=5,
        help="Maximum concurrent tasks",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )
    parser.add_argument(
        "--system-prompt",
        type=str,
        help="Override system prompt",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of tasks to run",
    )
    
    args = parser.parse_args()
    
    # Default job name
    job_name = args.name or f"{args.model} on {args.dataset.split('/')[-1]}"
    
    # Run evaluation with HUD trace
    with hud.job(name=job_name, dataset_link=args.dataset) as job_obj:
        results = evaluate_dataset(
            dataset_name=args.dataset,
            model=args.model,
            job_id=job_obj.id,
            max_concurrent=args.max_concurrent,
            verbose=args.verbose,
            limit=args.limit,
        )
    
    # Print summary
    rewards = [r["reward"] for r in results]
    errors = sum(1 for r in results if r["info"].get("status") == "error")
    
    console.print(f"\nEvaluation complete!")
    console.print(f"Tasks: {len(results)}")
    console.print(f"Average reward: {sum(rewards)/len(rewards) if rewards else 0:.2f}")
    console.print(f"Success rate: {sum(1 for r in rewards if r >= 1.0)/len(rewards)*100 if rewards else 0:.1f}%")
    if errors:
        console.print(f"Errors: {errors}")
    
    # Print link to view results
    console.print(f"\nView results at: https://app.hud.so/jobs/{job_obj.id}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())