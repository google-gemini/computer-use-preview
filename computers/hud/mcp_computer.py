#!/usr/bin/env python3
"""
MCP Computer implementation that connects to any MCP server exposing computer tools.
This allows the existing BrowserAgent to work with HUD's new MCP-based environments.
"""
import asyncio
import base64
import json
from typing import Literal, Optional, Tuple, Dict, Any, List
import termcolor

from computers.computer import Computer, EnvState


class MCPComputer(Computer):
    """Computer implementation that uses MCP protocol to connect to remote browser environments."""
    
    def __init__(
        self,
        mcp_config: Dict[str, Any],
        screen_size: Tuple[int, int] = (1280, 720),
        initial_url: str | None = None,
        search_engine_url: str = "https://www.google.com",
        task_prompt: Optional[str] = None,
    ):
        """
        Initialize MCP Computer.
        
        Args:
            mcp_config: MCP configuration dict (e.g., {"hud": {"url": ..., "headers": ...}})
                       This comes from Task.mcp_config in HUD
            screen_size: Screen size tuple (width, height)
            initial_url: Initial URL to navigate to
            search_engine_url: Search engine URL for search() method
            task_prompt: Optional task prompt (for compatibility with HudComputer)
        """
        self._mcp_config = mcp_config
        self._screen_size = screen_size
        self._initial_url = initial_url
        self._search_engine_url = search_engine_url
        self._task_prompt = task_prompt
        
        # MCP client and async loop
        self._client = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        
        # State tracking
        self._current_url = initial_url or "about:blank"
        self._last_screenshot = b""
        
        # Tool discovery
        self._available_tools: List[str] = []
        self._has_computer_tool = False
        self._has_playwright_tool = False
        
    def __enter__(self):
        """Enter context manager - initialize MCP client connection."""
        print("Creating MCP session...")
        
        # Import and create MCP client
        try:
            from hud.clients import MCPClient
        except ImportError:
            raise ImportError("HUD SDK not installed. Please install with: pip install hud-python[agents]")
        
        # Always create our own event loop to avoid conflicts
        # This matches the behavior of the working HudComputer implementation
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._owns_loop = True
        
        # Create MCP client with the provided config
        self._client = MCPClient(mcp_config=self._mcp_config)
        
        # Connect to MCP server
        self._loop.run_until_complete(self._client.initialize())
        
        # Discover available tools
        self._discover_tools()

        if self._initial_url:
            try:
                if self._has_playwright_tool:
                    env_state = self._call_playwright_tool("navigate", url=self._initial_url)
                else:
                    env_state = self.navigate(self._initial_url)
                self._last_screenshot = env_state.screenshot
                self._current_url = env_state.url or self._initial_url
            except Exception as e:
                print(f"Error getting initial screenshot: {e}")
                # If navigation fails, just try to get a screenshot
                try:
                    env_state = self._call_computer_tool("screenshot")
                    self._last_screenshot = env_state.screenshot
                    self._current_url = env_state.url or self._initial_url
                except Exception as e:
                    print(f"Error getting initial screenshot: {e}")
                    raise e
        
        
        termcolor.cprint(
            f"MCP browser session started. Available tools: {', '.join(self._available_tools)}",
            color="green",
            attrs=["bold"],
        )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager - cleanup MCP client connection."""
        if self._client and self._loop:
            self._loop.run_until_complete(self._client.shutdown())
        if self._loop:
            self._loop.close()
    
    def _discover_tools(self):
        """Discover what tools are available from the MCP server."""
        if not self._client or not self._loop:
            return
            
        try:
            # Try to list tools
            tools = self._loop.run_until_complete(self._client.list_tools())
            if tools:
                self._available_tools = [tool.name for tool in tools]
                self._has_computer_tool = "computer" in self._available_tools
                self._has_playwright_tool = "playwright" in self._available_tools
                print(f"Discovered {len(self._available_tools)} tools: {', '.join(self._available_tools)}")
        except Exception as e:
            print(f"Could not discover tools: {e}")
            # Assume standard tools are available
            self._has_computer_tool = True
            self._has_playwright_tool = True

    def get_initial_state(self) -> EnvState:
        """Get initial state of the computer."""
        try:
            env_state = self._call_computer_tool("screenshot")
            self._last_screenshot = env_state.screenshot
            self._current_url = env_state.url
        except Exception as e:
            print(f"Error getting initial screenshot: {e}")
            raise e
        
        return env_state
    
    def _call_computer_tool(self, action: str, **kwargs) -> EnvState:
        """
        Call the computer tool with the specified action.
        
        Args:
            action: The action to perform (click, type, screenshot, etc.)
            **kwargs: Additional arguments for the action
            
        Returns:
            EnvState with screenshot and URL
        """
        # Build arguments with action
        arguments = {"action": action}
        arguments.update(kwargs)
        
        return self._call_tool("computer", arguments)
    
    def _call_playwright_tool(self, action: str, **kwargs) -> EnvState:
        """
        Call the playwright tool with the specified action.
        
        Args:
            action: The action to perform (navigate, click, type, screenshot, etc.)
            **kwargs: Additional arguments for the action
            
        Returns:
            EnvState with screenshot and URL
        """
        # Build arguments with action
        arguments = {"action": action}
        arguments.update(kwargs)
        
        return self._call_tool("playwright", arguments)
    
    def _call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> EnvState:
        """
        Call an MCP tool and parse the response into EnvState.
        
        Args:
            tool_name: Name of the MCP tool to call
            arguments: Arguments for the tool
            
        Returns:
            EnvState with screenshot and URL
        """
        if not self._client or not self._loop:
            raise RuntimeError("MCPComputer not initialized. Use with context manager.")
        
        # Import MCP types
        from hud.types import MCPToolCall
        
        # Create tool call
        tool_call = MCPToolCall(
            name=tool_name,
            arguments=arguments,
            id=f"{tool_name}_call"
        )
        
        # Execute tool call
        result = self._loop.run_until_complete(
            self._client.call_tool(tool_call)
        )
        
        # Parse result to extract screenshot and URL
        screenshot_data = self._last_screenshot  # Default to last screenshot
        url = self._current_url  # Default to current URL
        
        if result and result.content:
            for block in result.content:
                if block.type == "image" and hasattr(block, "data"):
                    # Decode base64 screenshot
                    screenshot_data = base64.b64decode(block.data)
                    self._last_screenshot = screenshot_data
                elif block.type == "text":
                    # Look for URL in text
                    text = block.text
                    if "url:" in text.lower():
                        # Try to extract URL
                        try:
                            parts = text.split("url:", 1)
                            if len(parts) > 1:
                                url = parts[1].strip()
                                self._current_url = url
                        except:
                            pass
                    elif text.startswith("http"):
                        url = text.strip()
                        self._current_url = url
        
        return EnvState(screenshot=screenshot_data, url=url)
    
    def screen_size(self) -> Tuple[int, int]:
        """Return screen dimensions."""
        return self._screen_size
    
    def open_web_browser(self) -> EnvState:
        """Open web browser - most MCP environments start with browser open."""
        # Just get current state with screenshot
        return self._call_computer_tool("screenshot")
    
    def navigate(self, url: str) -> EnvState:
        """Navigate to URL."""
        # Try playwright tool first if available
        if self._has_playwright_tool:
            return self._call_playwright_tool("navigate", url=url)
        else:
            # Use computer tool to navigate (might need to click address bar and type)
            # First take screenshot to see current state
            self._call_computer_tool("screenshot")
            # Click on address bar (usually at top)
            self._call_computer_tool("click", x=self._screen_size[0] // 2, y=50)
            # Select all and clear
            self._call_computer_tool("press", keys=["ctrl", "a"])
            # Type new URL
            self._call_computer_tool("type", text=url)
            # Press enter
            return self._call_computer_tool("press", keys=["Return"])
    
    def click_at(self, x: int, y: int) -> EnvState:
        """Click at coordinates."""
        return self._call_computer_tool("click", x=x, y=y)
    
    def hover_at(self, x: int, y: int) -> EnvState:
        """Hover at coordinates."""
        # Use move action to hover
        return self._call_computer_tool("move", x=x, y=y)
    
    def type_text_at(
        self,
        x: int,
        y: int,
        text: str,
        press_enter: bool = False,
        clear_before_typing: bool = True,
    ) -> EnvState:
        """Type text at coordinates."""
        # First click to focus
        self._call_computer_tool("click", x=x, y=y)
        
        # Clear field if requested
        if clear_before_typing:
            # Select all and delete
            self._call_computer_tool("press", keys=["ctrl", "a"])
            self._call_computer_tool("press", keys=["Delete"])
        
        # Type text using computer tool with enter_after parameter
        return self._call_computer_tool("type", text=text, enter_after=press_enter)
    
    def key_combination(self, keys: list[str]) -> EnvState:
        """Press key combination."""
        # Use press action with keys list
        return self._call_computer_tool("press", keys=keys)
    
    def scroll_document(self, direction: Literal["up", "down", "left", "right"]) -> EnvState:
        """Scroll document in direction."""
        # Use playwright tool if available (more reliable for scrolling)
        if self._has_playwright_tool:
            if direction == "down":
                return self._call_playwright_tool("press", key="PageDown")
            elif direction == "up":
                return self._call_playwright_tool("press", key="PageUp")
            elif direction in ("left", "right"):
                # Use JavaScript scrollBy for horizontal scrolling like playwright implementation
                horizontal_scroll_amount = self._screen_size[0] // 2
                if direction == "left":
                    scroll_arg = f"-{horizontal_scroll_amount}"
                else:
                    scroll_arg = str(horizontal_scroll_amount)
                return self._call_playwright_tool("evaluate", expression=f"window.scrollBy({scroll_arg}, 0);")
            else:
                raise ValueError("Unsupported direction: ", direction)
        else:
            # Fallback to computer tool with error handling
            # Map direction to scroll_x and scroll_y
            scroll_x = 0
            scroll_y = 0
            if direction == "up":
                scroll_y = -500
            elif direction == "down":
                scroll_y = 500
            elif direction == "left":
                scroll_x = -500
            elif direction == "right":
                scroll_x = 500
                
            # Use computer tool scroll action
            return self._call_computer_tool(
                "scroll",
                x=self._screen_size[0] // 2,
                y=self._screen_size[1] // 2,
                scroll_x=scroll_x,
                scroll_y=scroll_y
            )
    
    def scroll_at(self, x: int, y: int, direction: str, magnitude: int) -> EnvState:
        """Scroll at specific location."""
        # Use playwright tool if available (more reliable for scrolling)
        if self._has_playwright_tool:
            # Move mouse to position first, then scroll like playwright implementation
            self._call_playwright_tool("move", x=x, y=y)
            
            # Map direction and magnitude for scroll
            dx = 0
            dy = 0
            if direction == "up":
                dy = -magnitude
            elif direction == "down":
                dy = magnitude
            elif direction == "left":
                dx = -magnitude
            elif direction == "right":
                dx = magnitude
            
            return self._call_playwright_tool("scroll", dx=dx, dy=dy)
        else:
            # Fallback to computer tool with error handling
            # Map direction and magnitude to scroll_x and scroll_y
            scroll_x = 0
            scroll_y = 0
            if direction == "up":
                scroll_y = -magnitude
            elif direction == "down":
                scroll_y = magnitude
            elif direction == "left":
                scroll_x = -magnitude
            elif direction == "right":
                scroll_x = magnitude
            
            # Scroll with computer tool
            return self._call_computer_tool(
                "scroll",
                x=x,
                y=y,
                scroll_x=scroll_x,
                scroll_y=scroll_y
            )
    
    def wait_5_seconds(self) -> EnvState:
        """Wait 5 seconds."""
        # Use wait action with time in milliseconds
        return self._call_computer_tool("wait", time=5000)
    
    def go_back(self) -> EnvState:
        """Go back in browser history."""
        # Use Alt+Left key combination
        return self._call_computer_tool("press", keys=["Alt", "Left"])
    
    def go_forward(self) -> EnvState:
        """Go forward in browser history."""
        # Use Alt+Right key combination
        return self._call_computer_tool("press", keys=["Alt", "Right"])
    
    def search(self) -> EnvState:
        """Navigate to search engine."""
        return self.navigate(self._search_engine_url)
    
    def drag_and_drop(
        self, x: int, y: int, destination_x: int, destination_y: int
    ) -> EnvState:
        """Drag from one location to another."""
        # Use computer tool drag action with path parameter
        path = [(x, y), (destination_x, destination_y)]
        return self._call_computer_tool("drag", path=path)
    
    def current_state(self) -> EnvState:
        """Get current state with screenshot."""
        return self._call_computer_tool("screenshot")