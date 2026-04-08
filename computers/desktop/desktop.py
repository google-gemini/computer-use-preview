import io
import sys
import time
import webbrowser
from typing import Literal

import pyautogui

from ..computer import Computer, EnvState


class DesktopComputer(Computer):
    """Controls the local desktop using OS-level input automation."""

    def __init__(
        self,
        screen_size: tuple[int, int],
        initial_url: str = "https://www.google.com",
        search_engine_url: str = "https://www.google.com",
    ):
        self._initial_url = initial_url
        self._search_engine_url = search_engine_url
        size = pyautogui.size()
        self._screen_size = (size.width, size.height)
        self._current_url = ""
        self._spotlight_pending = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return None

    def screen_size(self) -> tuple[int, int]:
        return self._screen_size

    def open_web_browser(self) -> EnvState:
        webbrowser.open(self._initial_url)
        self._current_url = self._initial_url
        time.sleep(1)
        return self.current_state()

    def click_at(self, x: int, y: int) -> EnvState:
        pyautogui.click(x, y)
        return self.current_state()

    def hover_at(self, x: int, y: int) -> EnvState:
        pyautogui.moveTo(x, y)
        return self.current_state()

    def type_text_at(
        self,
        x: int,
        y: int,
        text: str,
        press_enter: bool = False,
        clear_before_typing: bool = True,
    ) -> EnvState:
        if self._spotlight_pending:
            self._spotlight_pending = False
        else:
            pyautogui.click(x, y)
        if clear_before_typing:
            if sys.platform == "darwin":
                pyautogui.hotkey("command", "a")
            else:
                pyautogui.hotkey("ctrl", "a")
            pyautogui.press("backspace")
        pyautogui.write(text)
        if press_enter:
            pyautogui.press("enter")
        return self.current_state()

    def scroll_document(
        self, direction: Literal["up", "down", "left", "right"]
    ) -> EnvState:
        scroll_amount = self._screen_size[1] // 2
        if direction == "up":
            pyautogui.scroll(scroll_amount)
        elif direction == "down":
            pyautogui.scroll(-scroll_amount)
        elif direction == "left":
            pyautogui.hscroll(-scroll_amount)
        elif direction == "right":
            pyautogui.hscroll(scroll_amount)
        else:
            raise ValueError("Unsupported direction: ", direction)
        return self.current_state()

    def scroll_at(
        self,
        x: int,
        y: int,
        direction: Literal["up", "down", "left", "right"],
        magnitude: int = 800,
    ) -> EnvState:
        pyautogui.moveTo(x, y)
        if direction == "up":
            pyautogui.scroll(magnitude)
        elif direction == "down":
            pyautogui.scroll(-magnitude)
        elif direction == "left":
            pyautogui.hscroll(-magnitude)
        elif direction == "right":
            pyautogui.hscroll(magnitude)
        else:
            raise ValueError("Unsupported direction: ", direction)
        return self.current_state()

    def wait_5_seconds(self) -> EnvState:
        time.sleep(5)
        return self.current_state()

    def go_back(self) -> EnvState:
        if sys.platform == "darwin":
            pyautogui.hotkey("command", "[")
        else:
            pyautogui.hotkey("alt", "left")
        return self.current_state()

    def go_forward(self) -> EnvState:
        if sys.platform == "darwin":
            pyautogui.hotkey("command", "]")
        else:
            pyautogui.hotkey("alt", "right")
        return self.current_state()

    def search(self) -> EnvState:
        return self.navigate(self._search_engine_url)

    def navigate(self, url: str) -> EnvState:
        normalized_url = url
        if not normalized_url.startswith(("http://", "https://")):
            normalized_url = "https://" + normalized_url
        if sys.platform == "darwin":
            pyautogui.hotkey("command", "l")
        else:
            pyautogui.hotkey("ctrl", "l")
        pyautogui.write(normalized_url)
        pyautogui.press("enter")
        self._current_url = normalized_url
        time.sleep(1)
        return self.current_state()

    def key_combination(self, keys: list[str]) -> EnvState:
        normalized_keys = [self._normalize_key(key) for key in keys]
        if len(normalized_keys) == 1:
            pyautogui.press(normalized_keys[0])
        else:
            pyautogui.hotkey(*normalized_keys)
        if sys.platform == "darwin" and normalized_keys == ["command", "space"]:
            self._spotlight_pending = True
            time.sleep(0.2)
        return self.current_state()

    def drag_and_drop(
        self, x: int, y: int, destination_x: int, destination_y: int
    ) -> EnvState:
        pyautogui.moveTo(x, y)
        pyautogui.dragTo(destination_x, destination_y, button="left")
        return self.current_state()

    def current_state(self) -> EnvState:
        screenshot = pyautogui.screenshot()
        buffer = io.BytesIO()
        screenshot.save(buffer, format="PNG")
        return EnvState(screenshot=buffer.getvalue(), url=self._current_url)

    def _normalize_key(self, key: str) -> str:
        k = key.strip().lower()
        if k in ("controlormeta", "meta", "command"):
            return "command" if sys.platform == "darwin" else "ctrl"
        if k in ("control", "ctrl"):
            return "ctrl"
        if k in ("alt", "option"):
            return "alt"
        if k in ("return", "enter"):
            return "enter"
        if k in ("escape", "esc"):
            return "esc"
        if k in ("space", "spacebar"):
            return "space"
        if k in ("pageup", "page_up"):
            return "pageup"
        if k in ("pagedown", "page_down"):
            return "pagedown"
        if k in ("arrowleft", "left"):
            return "left"
        if k in ("arrowright", "right"):
            return "right"
        if k in ("arrowup", "up"):
            return "up"
        if k in ("arrowdown", "down"):
            return "down"
        if k == "delete":
            return "delete"
        if k == "backspace":
            return "backspace"
        return k
