import asyncio
import base64
from typing import Literal, Optional, Any, Dict
import termcolor

from ..computer import Computer, EnvState
from hud.job import Job
from hud.task import Task

class HudComputer(Computer):
    """HUD SDK Computer implementation that uses HUD environments for browser control."""

    def __init__(
        self,
        screen_size: tuple[int, int],
        initial_url: str = "https://www.google.com",
        search_engine_url: str = "https://www.google.com",
        task_prompt: Optional[str] = None,
        task: Optional[Task] = None,  # Optional Task object from HUD SDK
        job: Optional[Job] = None,
    ):
        self._screen_size = screen_size
        self._initial_url = initial_url
        self._search_engine_url = search_engine_url
        self._task_prompt = task_prompt or "Browse the web"
        self._task = task
        self._job = job
        self._env = None
        self._obs = None
        self._done = False
        self._loop = None
        self._current_url = None

    def __enter__(self):
        print("Creating HUD session...")
        
        # Create and run the async setup in a new event loop
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        
        # Import HUD SDK here to avoid circular imports
        try:
            from hud import gym
            from hud.task import Task
        except ImportError:
            raise ImportError("HUD SDK not installed. Please install with: pip install hud-python")
        
        # Use provided task or create a default one
        if self._task:
            task = self._task
        else:
            # Create a default task for the browser environment
            task = Task(
                prompt=self._task_prompt,
                gym="hud-browser",
                setup=("goto", self._initial_url),
                evaluate=("page_contains", "dummy")
            )
        
        # Create the environment
        self._env = self._loop.run_until_complete(gym.make(task, job=self._job))
        
        # Reset the environment to get initial observation
        self._obs, _ = self._loop.run_until_complete(self._env.reset())
        
        termcolor.cprint(
            f"HUD browser session started.",
            color="green",
            attrs=["bold"],
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._env:
            self._loop.run_until_complete(self._env.close())
        if self._loop:
            self._loop.close()

    def _get_screenshot_from_obs(self) -> bytes:
        """Extract screenshot from HUD observation."""
        if self._obs is None:
            return b""
        
        if hasattr(self._obs, 'screenshot'):
            screenshot_b64 = self._obs.screenshot
            screenshot_bytes = base64.b64decode(screenshot_b64)
            return screenshot_bytes
        
        # HUD SDK returns observations with a 'screenshot' key containing base64 encoded image
        if isinstance(self._obs, dict) and 'screenshot' in self._obs:
            screenshot_b64 = self._obs['screenshot']
            # Decode base64 to bytes
            screenshot_bytes = base64.b64decode(screenshot_b64)
            return screenshot_bytes
        
        return b""

    def _get_url_from_obs(self) -> str:
        """Extract URL from HUD observation."""
        if self._current_url is None:
            return self._initial_url
        return self._current_url

    def _create_cla_action(self, action_type: str, **kwargs) -> Dict[str, Any]:
        """Create a CLA action in the HUD SDK format."""
        from hud.adapters.common.types import (
            ClickAction,
            DragAction,
            MoveAction,
            Point,
            PressAction,
            ScrollAction,
            TypeAction,
            WaitAction,
            CustomAction,
        )
        # Map our action types to HUD SDK CLA action types
        if action_type == "click":
            return ClickAction(
                point=Point(x=kwargs.get("x"), y=kwargs.get("y")),
                button=kwargs.get("button", "left")
            )
        elif action_type == "move":
            return MoveAction(
                point=Point(x=kwargs.get("x"), y=kwargs.get("y"))
            )
        elif action_type == "type":
            return TypeAction(
                text=kwargs.get("text", ""),
                enter_after=kwargs.get("enter_after", False)
            )
        elif action_type == "scroll":
            # Map direction to scroll amounts
            direction = kwargs.get("direction", "down")
            dx, dy = 0, 0
            magnitude = kwargs.get("magnitude", 100)
            if direction == "down":
                dy = magnitude
            elif direction == "up":
                dy = -magnitude
            elif direction == "right":
                dx = magnitude
            elif direction == "left":
                dx = -magnitude
            
            action = ScrollAction(
                scroll=Point(x=dx, y=dy)
            )
            if "x" in kwargs and "y" in kwargs:
                action.point = Point(x=kwargs["x"], y=kwargs["y"])
            return action
        elif action_type == "press":
            return PressAction(
                keys=kwargs.get("keys", [])
            )
        elif action_type == "wait":
            # Convert seconds to milliseconds
            return WaitAction(
                time=kwargs.get("seconds", 5) * 1000
            )
        elif action_type == "drag":
            return DragAction(
                path=[
                    Point(x=kwargs.get("start_x"), y=kwargs.get("start_y")),
                    Point(x=kwargs.get("end_x"), y=kwargs.get("end_y"))
                ]
            )
        elif action_type == "navigate":
            # Use a CustomAction for navigation
            return CustomAction(
                action="navigate",
                args={"url": kwargs.get("url", "")}
            )
        elif action_type == "go_back":
            return CustomAction(
                action="go_back"
            )
        elif action_type == "go_forward":
            return CustomAction(
                action="go_forward"
            )
        else:
            # Fallback to CustomAction for any unrecognized action
            return CustomAction(
                action=action_type,
                args=kwargs
            )

    def _execute_action(self, action_type: str, **kwargs) -> EnvState:
        """Execute an action in the HUD environment."""
        if self._done:
            return self.current_state()
        
        # Create CLA action for HUD SDK
        action = self._create_cla_action(action_type, **kwargs)
        
        # Execute action in HUD environment
        # HUD SDK expects a list of actions
        self._obs, reward, self._done, info = self._loop.run_until_complete(
            self._env.step([action])
        )

        if "current_url" in info:
            self._current_url = info["current_url"]
        
        return self.current_state()

    def screen_size(self) -> tuple[int, int]:
        return self._screen_size

    def open_web_browser(self) -> EnvState:
        return self.current_state()

    def click_at(self, x: int, y: int) -> EnvState:
        return self._execute_action("click", x=x, y=y)

    def hover_at(self, x: int, y: int) -> EnvState:
        return self._execute_action("move", x=x, y=y)

    def type_text_at(
        self,
        x: int,
        y: int,
        text: str,
        press_enter: bool,
        clear_before_typing: bool,
    ) -> EnvState:
        # First click at the position
        self._execute_action("click", x=x, y=y)
        
        # Clear existing text if requested
        if clear_before_typing:
            # Select all and delete
            self._execute_action("press", keys=["ctrl", "a"])
            self._execute_action("press", keys=["delete"])
        
        # Type the text with optional enter
        self._execute_action("type", text=text, enter_after=press_enter)
        
        return self.current_state()

    def scroll_document(
        self, direction: Literal["up", "down", "left", "right"]
    ) -> EnvState:
        return self._execute_action("scroll", direction=direction)

    def scroll_at(
        self,
        x: int,
        y: int,
        direction: Literal["up", "down", "left", "right"],
        magnitude: int,
    ) -> EnvState:
        return self._execute_action(
            "scroll", x=x, y=y, direction=direction, magnitude=magnitude
        )

    def wait_5_seconds(self) -> EnvState:
        return self._execute_action("wait", seconds=5)

    def go_back(self) -> EnvState:
        return self._execute_action("go_back")

    def go_forward(self) -> EnvState:
        return self._execute_action("go_forward")

    def search(self) -> EnvState:
        return self.navigate(self._search_engine_url)

    def navigate(self, url: str) -> EnvState:
        return self._execute_action("navigate", url=url)

    def key_combination(self, keys: list[str]) -> EnvState:
        # Map key names to HUD SDK format (lowercase)
        mapped_keys = [key.lower() for key in keys]
        return self._execute_action("press", keys=mapped_keys)

    def drag_and_drop(
        self, x: int, y: int, destination_x: int, destination_y: int
    ) -> EnvState:
        return self._execute_action(
            "drag", 
            start_x=x, 
            start_y=y, 
            end_x=destination_x, 
            end_y=destination_y
        )

    def current_state(self) -> EnvState:
        screenshot = self._get_screenshot_from_obs()
        url = self._get_url_from_obs()
        return EnvState(screenshot=screenshot, url=url) 

    def evaluate(self) -> dict:
        return self._loop.run_until_complete(
            self._env.evaluate()
        )