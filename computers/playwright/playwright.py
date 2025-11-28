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
import logging
import termcolor
import time
import os
import sys
from ..computer import (
    Computer,
    EnvState,
)
import playwright.sync_api
from playwright.sync_api import sync_playwright
from typing import Literal

# Define a mapping from the user-friendly key names to Playwright's expected key names.
# Playwright is generally good with case-insensitivity for these, but it's best to be canonical.
# See: https://playwright.dev/docs/api/class-keyboard#keyboard-press
# Keys like 'a', 'b', '1', '$' are passed directly.
PLAYWRIGHT_KEY_MAP = {
    "backspace": "Backspace",
    "tab": "Tab",
    "return": "Enter",  # Playwright uses 'Enter'
    "enter": "Enter",
    "shift": "Shift",
    "control": "ControlOrMeta",
    "alt": "Alt",
    "escape": "Escape",
    "space": "Space",  # Can also just be " "
    "pageup": "PageUp",
    "pagedown": "PageDown",
    "end": "End",
    "home": "Home",
    "left": "ArrowLeft",
    "up": "ArrowUp",
    "right": "ArrowRight",
    "down": "ArrowDown",
    "insert": "Insert",
    "delete": "Delete",
    "semicolon": ";",  # For actual character ';'
    "equals": "=",  # For actual character '='
    "multiply": "Multiply",  # NumpadMultiply
    "add": "Add",  # NumpadAdd
    "separator": "Separator",  # Numpad specific
    "subtract": "Subtract",  # NumpadSubtract, or just '-' for character
    "decimal": "Decimal",  # NumpadDecimal, or just '.' for character
    "divide": "Divide",  # NumpadDivide, or just '/' for character
    "f1": "F1",
    "f2": "F2",
    "f3": "F3",
    "f4": "F4",
    "f5": "F5",
    "f6": "F6",
    "f7": "F7",
    "f8": "F8",
    "f9": "F9",
    "f10": "F10",
    "f11": "F11",
    "f12": "F12",
    "command": "Meta",  # 'Meta' is Command on macOS, Windows key on Windows
}


class PlaywrightComputer(Computer):
    """Connects to a local Playwright instance."""

    def __init__(
        self,
        screen_size: tuple[int, int],
        initial_url: str = "https://www.google.com",
        search_engine_url: str = "https://www.google.com",
        highlight_mouse: bool = False,
        user_data_dir: str | None = None,
        use_system_chrome: bool = False,
    ):
        self._initial_url = initial_url
        self._screen_size = screen_size
        self._search_engine_url = search_engine_url
        self._highlight_mouse = highlight_mouse
        self._user_data_dir = user_data_dir
        self._use_system_chrome = use_system_chrome

    def _handle_new_page(self, new_page: playwright.sync_api.Page):
        """The Computer Use model only supports a single tab at the moment.

        Some websites, however, try to open links in a new tab.
        For those situations, we intercept the page-opening behavior, and instead overwrite the current page.
        """
        new_url = new_page.url
        new_page.close()
        self._page.goto(new_url)

    def __enter__(self):
        print("Creating session...")
        self._playwright = sync_playwright().start()
        
        if self._user_data_dir:
            # Handle Chrome profile path: .../Chrome/Profile 1 -> .../Chrome/User Data
            profile_dir = None
            user_data_dir = self._user_data_dir
            current_name = os.path.basename(user_data_dir)
            parent_dir = os.path.dirname(user_data_dir)
            
            # If provided path is a profile directory (Profile 1, Profile 2, etc.), 
            # find the "User Data" parent directory
            if current_name in ("Default", "Profile 1", "Profile 2", "Profile 3", "Profile 4", "Profile 5"):
                user_data_candidate = os.path.join(parent_dir, "User Data")
                if os.path.isdir(user_data_candidate):
                    profile_dir = current_name
                    user_data_dir = user_data_candidate
                    termcolor.cprint(
                        f"Detected profile: {profile_dir}, using User Data directory: {user_data_dir}",
                        color="cyan",
                    )
                elif os.path.basename(parent_dir) == "User Data":
                    # Already pointing to User Data/Profile X
                    profile_dir = current_name
                    user_data_dir = parent_dir
                    termcolor.cprint(
                        f"Detected profile: {profile_dir}, using User Data directory: {user_data_dir}",
                        color="cyan",
                    )
            
            # Check for Chrome lock file - indicates Chrome might still be running
            lock_file = os.path.join(user_data_dir, "SingletonLock")
            if os.path.exists(lock_file):
                termcolor.cprint(
                    f"Warning: Chrome lock file detected. Make sure Chrome is completely closed before using the profile.",
                    color="yellow",
                )
            
            # Use persistent context for Chrome profile support
            # For managed profiles with extensions and SSO, we need to:
            # - Enable extensions (remove --disable-extensions)
            # - Enable sync (remove --disable-sync) for device enrollment and SSO
            # - Enable file system access for profile data
            # - Keep other optimizations that don't interfere with enterprise features
            try:
                args = [
                    # Extensions, sync, and file system are enabled for managed profiles
                    # to support browsing protection, device identification, and SSO
                    "--disable-plugins",
                    "--disable-dev-shm-usage",
                    "--disable-background-networking",
                    "--disable-default-apps",
                    # No '--no-sandbox' arg means the sandbox is on.
                ]
                
                # If we detected a specific profile, use --profile-directory argument
                if profile_dir:
                    args.append(f"--profile-directory={profile_dir}")
                
                # Option to use system Chrome instead of Playwright's bundled Chromium
                # This can work better with existing Chrome profiles
                executable_path = None
                if self._use_system_chrome:
                    # Try to find system Chrome on macOS
                    chrome_paths = [
                        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                        "/Applications/Chromium.app/Contents/MacOS/Chromium",
                    ]
                    for path in chrome_paths:
                        if os.path.exists(path):
                            executable_path = path
                            termcolor.cprint(
                                f"Using system Chrome: {executable_path}",
                                color="cyan",
                            )
                            break
                    if not executable_path:
                        termcolor.cprint(
                            "Warning: System Chrome not found, using Playwright's Chromium",
                            color="yellow",
                        )
                
                self._context = self._playwright.chromium.launch_persistent_context(
                    user_data_dir=user_data_dir,
                    viewport={
                        "width": self._screen_size[0],
                        "height": self._screen_size[1],
                    },
                    args=args,
                    headless=bool(os.environ.get("PLAYWRIGHT_HEADLESS", False)),
                    executable_path=executable_path,
                )
                # With persistent context, pages are managed differently
                self._page = self._context.pages[0] if self._context.pages else self._context.new_page()
                self._browser = None  # Persistent context manages browser internally
            except Exception as e:
                termcolor.cprint(
                    f"Error launching Chromium with profile: {e}",
                    color="red",
                )
                termcolor.cprint(
                    f"Make sure Chrome is completely closed and the profile path is correct: {self._user_data_dir}",
                    color="yellow",
                )
                raise
        else:
            # Original behavior without profile - disable extensions and sync
            self._browser = self._playwright.chromium.launch(
                args=[
                    "--disable-extensions",
                    "--disable-file-system",
                    "--disable-plugins",
                    "--disable-dev-shm-usage",
                    "--disable-background-networking",
                    "--disable-default-apps",
                    "--disable-sync",
                    # No '--no-sandbox' arg means the sandbox is on.
                ],
                headless=bool(os.environ.get("PLAYWRIGHT_HEADLESS", False)),
            )
            self._context = self._browser.new_context(
                viewport={
                    "width": self._screen_size[0],
                    "height": self._screen_size[1],
                }
            )
            self._page = self._context.new_page()
        
        self._page.goto(self._initial_url)
        self._context.on("page", self._handle_new_page)

        termcolor.cprint(
            f"Started local playwright.",
            color="green",
            attrs=["bold"],
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._context:
            self._context.close()
        if self._browser:
            try:
                self._browser.close()
            except Exception as e:
                # Browser was already shut down because of SIGINT or such.
                if "Browser.close: Connection closed while reading from the driver" in str(
                    e
                ):
                    pass
                else:
                    raise

        self._playwright.stop()

    def open_web_browser(self) -> EnvState:
        return self.current_state()

    def click_at(self, x: int, y: int):
        self.highlight_mouse(x, y)
        self._page.mouse.click(x, y)
        self._page.wait_for_load_state()
        return self.current_state()

    def hover_at(self, x: int, y: int):
        self.highlight_mouse(x, y)
        self._page.mouse.move(x, y)
        self._page.wait_for_load_state()
        return self.current_state()

    def type_text_at(
        self,
        x: int,
        y: int,
        text: str,
        press_enter: bool = False,
        clear_before_typing: bool = True,
    ) -> EnvState:
        self.highlight_mouse(x, y)
        self._page.mouse.click(x, y)
        self._page.wait_for_load_state()

        if clear_before_typing:
            if sys.platform == "darwin":
                self.key_combination(["Command", "A"])
            else:
                self.key_combination(["Control", "A"])
            self.key_combination(["Delete"])

        self._page.keyboard.type(text)
        self._page.wait_for_load_state()

        if press_enter:
            self.key_combination(["Enter"])
        self._page.wait_for_load_state()
        return self.current_state()

    def _horizontal_document_scroll(
        self, direction: Literal["left", "right"]
    ) -> EnvState:
        # Scroll by 50% of the viewport size.
        horizontal_scroll_amount = self.screen_size()[0] // 2
        if direction == "left":
            sign = "-"
        else:
            sign = ""
        scroll_argument = f"{sign}{horizontal_scroll_amount}"
        # Scroll using JS.
        self._page.evaluate(f"window.scrollBy({scroll_argument}, 0); ")
        self._page.wait_for_load_state()
        return self.current_state()

    def scroll_document(
        self, direction: Literal["up", "down", "left", "right"]
    ) -> EnvState:
        if direction == "down":
            return self.key_combination(["PageDown"])
        elif direction == "up":
            return self.key_combination(["PageUp"])
        elif direction in ("left", "right"):
            return self._horizontal_document_scroll(direction)
        else:
            raise ValueError("Unsupported direction: ", direction)

    def scroll_at(
        self,
        x: int,
        y: int,
        direction: Literal["up", "down", "left", "right"],
        magnitude: int = 800,
    ) -> EnvState:
        self.highlight_mouse(x, y)

        self._page.mouse.move(x, y)
        self._page.wait_for_load_state()

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
        else:
            raise ValueError("Unsupported direction: ", direction)

        self._page.mouse.wheel(dx, dy)
        self._page.wait_for_load_state()
        return self.current_state()

    def wait_5_seconds(self) -> EnvState:
        time.sleep(5)
        return self.current_state()

    def go_back(self) -> EnvState:
        self._page.go_back()
        self._page.wait_for_load_state()
        return self.current_state()

    def go_forward(self) -> EnvState:
        self._page.go_forward()
        self._page.wait_for_load_state()
        return self.current_state()

    def search(self) -> EnvState:
        return self.navigate(self._search_engine_url)

    def navigate(self, url: str) -> EnvState:
        normalized_url = url
        if not normalized_url.startswith(("http://", "https://")):
            normalized_url = "https://" + normalized_url
        self._page.goto(normalized_url)
        self._page.wait_for_load_state()
        return self.current_state()

    def key_combination(self, keys: list[str]) -> EnvState:
        # Normalize all keys to the Playwright compatible version.
        keys = [PLAYWRIGHT_KEY_MAP.get(k.lower(), k) for k in keys]

        for key in keys[:-1]:
            self._page.keyboard.down(key)

        self._page.keyboard.press(keys[-1])

        for key in reversed(keys[:-1]):
            self._page.keyboard.up(key)

        return self.current_state()

    def drag_and_drop(
        self, x: int, y: int, destination_x: int, destination_y: int
    ) -> EnvState:
        self.highlight_mouse(x, y)
        self._page.mouse.move(x, y)
        self._page.wait_for_load_state()
        self._page.mouse.down()
        self._page.wait_for_load_state()

        self.highlight_mouse(destination_x, destination_y)
        self._page.mouse.move(destination_x, destination_y)
        self._page.wait_for_load_state()
        self._page.mouse.up()
        return self.current_state()

    def current_state(self) -> EnvState:
        self._page.wait_for_load_state()
        # Even if Playwright reports the page as loaded, it may not be so.
        # Add a manual sleep to make sure the page has finished rendering.
        time.sleep(0.5)
        screenshot_bytes = self._page.screenshot(type="png", full_page=False)
        return EnvState(screenshot=screenshot_bytes, url=self._page.url)

    def screen_size(self) -> tuple[int, int]:
        viewport_size = self._page.viewport_size
        # If available, try to take the local playwright viewport size.
        if viewport_size:
            return viewport_size["width"], viewport_size["height"]
        # If unavailable, fall back to the original provided size.
        return self._screen_size

    def highlight_mouse(self, x: int, y: int):
        if not self._highlight_mouse:
            return
        self._page.evaluate(
            f"""
        () => {{
            const element_id = "playwright-feedback-circle";
            const div = document.createElement('div');
            div.id = element_id;
            div.style.pointerEvents = 'none';
            div.style.border = '4px solid red';
            div.style.borderRadius = '50%';
            div.style.width = '20px';
            div.style.height = '20px';
            div.style.position = 'fixed';
            div.style.zIndex = '9999';
            document.body.appendChild(div);

            div.hidden = false;
            div.style.left = {x} - 10 + 'px';
            div.style.top = {y} - 10 + 'px';

            setTimeout(() => {{
                div.hidden = true;
            }}, 2000);
        }}
    """
        )
        # Wait a bit for the user to see the cursor.
        time.sleep(1)
