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
import abc
import pydantic
from typing import Literal


class EnvState(pydantic.BaseModel):
    # The screenshot in PNG format.
    screenshot: bytes
    url: str


class Computer(abc.ABC):
    """Defines an interface for environments."""

    @abc.abstractmethod
    def screen_size(self) -> tuple[int, int]:
        """Returns the screen size of the environment."""

    @abc.abstractmethod
    def open_web_browser(self) -> EnvState:
        """Opens the web browser."""

    @abc.abstractmethod
    def click_at(self, x: int, y: int) -> EnvState:
        """Clicks at a specific x, y  coordinate on the webpage.

        The 'x' and 'y' values are absolute values, scaled to the height and width of the screen.
        """

    @abc.abstractmethod
    def hover_at(self, x: int, y: int) -> EnvState:
        """Hovers at a specific x, y coordinate on the webpage.

        May be used to explore sub-menus that appear on hover.
        The 'x' and 'y' values are absolute values, scaled to the height and width of the screen.
        """

    @abc.abstractmethod
    def type_text_at(
        self,
        x: int,
        y: int,
        text: str,
        press_enter: bool,
        clear_before_typing: bool,
    ) -> EnvState:
        """Types text at a specific x, y coordinate.

        The system automatically presses ENTER after typing. To disable this, set `press_enter` to False.
        The system automatically clears any existing content before typing the specified `text`. To disable this, set `clear_before_typing` to False.
        The 'x' and 'y' values are absolute values, scaled to the height and width of the screen.
        """

    @abc.abstractmethod
    def scroll_document(
        self, direction: Literal["up", "down", "left", "right"]
    ) -> EnvState:
        """Scrolls the entire webpage "up", "down", "left" or "right" based on direction."""

    @abc.abstractmethod
    def scroll_at(
        self,
        x: int,
        y: int,
        direction: Literal["up", "down", "left", "right"],
        magnitude: int,
    ) -> EnvState:
        """Scrolls up, down, right, or left at a x, y coordinate by magnitude.

        The 'x' and 'y' values are absolute values, scaled to the height and width of the screen.
        """

    @abc.abstractmethod
    def wait_5_seconds(self) -> EnvState:
        """Waits for 5 seconds to allow unfinished webpage processes to complete."""

    @abc.abstractmethod
    def go_back(self) -> EnvState:
        """Navigates back to the previous webpage in the browser history."""

    @abc.abstractmethod
    def go_forward(self) -> EnvState:
        """Navigates forward to the next webpage in the browser history."""

    @abc.abstractmethod
    def search(self) -> EnvState:
        """Directly jumps to a search engine home page.

        Used when you need to start with a search. For example, this is used when
        the current website doesn't have the information needed or because a new
        task is being started.
        """

    @abc.abstractmethod
    def navigate(self, url: str) -> EnvState:
        """Navigates directly to a specified URL."""

    @abc.abstractmethod
    def key_combination(self, keys: list[str]) -> EnvState:
        """Presses keyboard keys and combinations, such as "control+c" or "enter"."""

    @abc.abstractmethod
    def drag_and_drop(
        self, x: int, y: int, destination_x: int, destination_y: int
    ) -> EnvState:
        """Drag and drop an element from a x, y coordinate to a destination destination_y, destination_x coordinate.
        The 'x', 'y', 'destination_y' and 'destination_x' values are absolute values, scaled to the height and width of the screen.
        """

    @abc.abstractmethod
    def current_state(self) -> EnvState:
        """Returns the current state of the current webpage."""
