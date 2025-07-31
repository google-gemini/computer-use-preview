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
import termcolor
import time
import sys
from ..computer import (
    Computer,
    EnvState,
)
from typing import Literal
from screeninfo import get_monitors
import pyautogui
from io import BytesIO


class MyComputer(Computer):

    def __init__(
        self,
    ):
        monitors = get_monitors()
        print(f'Detected {len(monitors)} monitors.')
        for id, m in enumerate(monitors):
            print(f"ID: {id} Monitor: {m.name if m.name else 'Unnamed'}, Primary: {m.is_primary}, "
                f"Resolution: {m.width}x{m.height}, Position: ({m.x}, {m.y})")
            print()

        selection = int(input('Make your selection: '))
        m = monitors[selection]
        self._size = (m.width, m.height)
        self._offset = (m.x, 0) # hack for y

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def _correct_xy(self, x, y):
        if x<0 or x>=self._size[0] or y<0 or y>=self._size[1]:
            raise ValueError(f'Invalid xy: {x} {y}')
        return (x+self._offset[0], y+self._offset[1])

    def open_web_browser(self) -> EnvState:
        return self.current_state()

    def click_at(self, x: int, y: int):
        x, y = self._correct_xy(x, y)
        pyautogui.click(x=x, y=y)
        return self.current_state()

    def hover_at(self, x: int, y: int):
        raise NotImplementedError()

    def type_text_at(
        self,
        x: int,
        y: int,
        text: str,
        press_enter: bool = False,
        clear_before_typing: bool = True,
    ) -> EnvState:
        self.click_at(x, y)
        pyautogui.write(text)
        if press_enter:
            pyautogui.press('enter')
        return self.current_state()

    def scroll_document(
        self, direction: Literal["up", "down", "left", "right"]
    ) -> EnvState:
        for _ in range(5):
            pyautogui.press(direction)
        return self.current_state()

    def scroll_at(
        self,
        x: int,
        y: int,
        direction: Literal["up", "down", "left", "right"],
        magnitude: int,
    ) -> EnvState:
        raise NotImplementedError()

    def wait_5_seconds(self) -> EnvState:
        time.sleep(5)
        return self.current_state()

    def go_back(self) -> EnvState:
        raise NotImplementedError()

    def go_forward(self) -> EnvState:
        raise NotImplementedError()

    def search(self) -> EnvState:
        raise NotImplementedError()

    def navigate(self, url: str) -> EnvState:
        raise NotImplementedError()

    def key_combination(self, keys: list[str]) -> EnvState:
        raise NotImplementedError()

    def drag_and_drop(
        self, x: int, y: int, destination_x: int, destination_y: int
    ) -> EnvState:
        raise NotImplementedError()

    def current_state(self) -> EnvState:
        time.sleep(3)
        im = pyautogui.screenshot(region=(self._offset[0], self._offset[1], self._size[0], self._size[1]))
        image_bytes_io = BytesIO()

        # Save the image to the BytesIO object in PNG format
        im.save(image_bytes_io, format='PNG')
        png_bytes = image_bytes_io.getvalue()

        return EnvState(screenshot=png_bytes, url='about:local')

    def screen_size(self) -> tuple[int, int]:
        return self._size

    def highlight_mouse(self, x: int, y: int):
        raise NotImplementedError()
