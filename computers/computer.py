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
from typing import TypeAlias
import pydantic


# The screenshot in PNG format.
Screenshot: TypeAlias = bytes


class EnvState(pydantic.BaseModel):
    screenshot: Screenshot
    url: str


class Computer(abc.ABC):
    """Defines an interface for environments."""

    @abc.abstractmethod
    def screen_size() -> tuple[int, int]:
        """Returns the screen size of the environment."""

    @abc.abstractmethod
    def open_web_browser() -> EnvState:
        """Opens the web browser."""

    @abc.abstractmethod
    def click_at(y: int, x: int) -> EnvState:
        """Clicks at a specific y (0-999), x (0-999) coordinate on the webpage.

        The 'x' and 'y' values are scaled to the height and width of the screen.
        """

    @abc.abstractmethod
    def hover_at(y: int, x: int) -> EnvState:
        """Hovers at a specific y (0-999), x (0-999) coordinate on the webpage.

        May be used to explore sub-menus that appear on hover.
        The 'x' and 'y' values are scaled to the height and width of the screen.
        """

    @abc.abstractmethod
    def type_text_at(y: int, x: int, text: str) -> EnvState:
        """Types text at a specific y (0-999), x (0-999) coordinate.

        The system automatically presses ENTER after typing.
        The 'x' and 'y' values are scaled to the height and width of the screen.
        """

    @abc.abstractmethod
    def scroll_document(direction: str) -> EnvState:
        """Scrolls the entire webpage "up" or "down" based on direction."""

    @abc.abstractmethod
    def wait_5_seconds() -> EnvState:
        """Waits for 5 seconds to allow unfinished webpage processes to complete."""

    @abc.abstractmethod
    def go_back() -> EnvState:
        """Navigates back to the previous webpage in the browser history."""

    @abc.abstractmethod
    def go_forward() -> EnvState:
        """Navigates forward to the next webpage in the browser history."""

    @abc.abstractmethod
    def search() -> EnvState:
        """Directly jumps to a search engine home page.

        Used when you need to start with a search. For example, this is used when
        the current website doesn't have the information needed or because a new
        task is being started.
        """

    @abc.abstractmethod
    def navigate(url: str) -> EnvState:
        """Navigates directly to a specified URL."""

    @abc.abstractmethod
    def key_combination(keys: list[str]) -> EnvState:
        """Presses keyboard keys and combinations, such as "control+c" or "enter"."""

    @abc.abstractmethod
    def current_state() -> EnvState:
        """Returns the current state of the current webpage."""
