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
import unittest
from commands import (
    CommandModel,
    Navigate,
    ClickAt,
    HoverAt,
    TypeTextAt,
    ScrollDocument,
    ScrollAt,
    DragAndDrop,
    GoBack,
    GoForward,
    Search,
    Wait5Seconds,
    KeyCombination,
    Screenshot,
    Shutdown,
)


class TestCommands(unittest.TestCase):

    def test_navigate(self):
        function_call = {"name": "navigate", "args": {"url": "foo"}}
        command = CommandModel.model_validate(function_call)
        self.assertIsInstance(command.root, Navigate)
        self.assertEqual(command.model_dump(), function_call)

    def test_click_at(self):
        function_call = {"name": "click_at", "args": {"x": 2, "y": 1}}
        command = CommandModel.model_validate(function_call)
        self.assertIsInstance(command.root, ClickAt)
        self.assertEqual(command.model_dump(), function_call)

    def test_hover_at(self):
        function_call = {"name": "hover_at", "args": {"x": 2, "y": 1}}
        command = CommandModel.model_validate(function_call)
        self.assertIsInstance(command.root, HoverAt)
        self.assertEqual(command.model_dump(), function_call)

    def test_type_text_at(self):
        function_call = {
            "name": "type_text_at",
            "args": {
                "x": 2,
                "y": 1,
                "text": "one",
                "press_enter": True,
                "clear_before_typing": False,
            },
        }
        command = CommandModel.model_validate(
            function_call,
        )
        self.assertIsInstance(command.root, TypeTextAt)
        self.assertEqual(
            command.model_dump(),
            {
                "name": "type_text_at",
                "args": {
                    "x": 2,
                    "y": 1,
                    "text": "one",
                    "press_enter": True,
                    "clear_before_typing": False,
                },
            },
        )

    def test_scroll_document(self):
        function_call = {
            "name": "scroll_document",
            "args": {"direction": "up"},
        }
        command = CommandModel.model_validate(
            function_call,
        )
        self.assertIsInstance(command.root, ScrollDocument)
        self.assertEqual(command.model_dump(), function_call)

        function_call = {
            "name": "scroll_document",
            "args": {"direction": "down"},
        }
        command = CommandModel.model_validate(
            function_call,
        )
        self.assertIsInstance(command.root, ScrollDocument)
        self.assertEqual(command.model_dump(), function_call)

        function_call = {
            "name": "scroll_document",
            "args": {"direction": "left"},
        }
        command = CommandModel.model_validate(
            function_call,
        )
        self.assertIsInstance(command.root, ScrollDocument)
        self.assertEqual(command.model_dump(), function_call)

        function_call = {
            "name": "scroll_document",
            "args": {"direction": "right"},
        }
        command = CommandModel.model_validate(
            function_call,
        )
        self.assertIsInstance(command.root, ScrollDocument)
        self.assertEqual(command.model_dump(), function_call)

    def test_scroll_at(self):
        function_call = {
            "name": "scroll_at",
            "args": {"x": 1, "y": 2, "direction": "up", "magnitude": 10},
        }
        command = CommandModel.model_validate(
            function_call,
        )
        self.assertIsInstance(command.root, ScrollAt)
        self.assertEqual(command.model_dump(), function_call)

    def test_drag_and_drop(self):
        function_call = {
            "name": "drag_and_drop",
            "args": {"x": 1, "y": 2, "destination_x": 3, "destination_y": 4},
        }
        command = CommandModel.model_validate(
            function_call,
        )
        self.assertIsInstance(command.root, DragAndDrop)
        self.assertEqual(command.model_dump(), function_call)

    def test_go_back(self):
        function_call = {"name": "go_back", "args": {}}
        command = CommandModel.model_validate(function_call)
        self.assertIsInstance(command.root, GoBack)
        self.assertEqual(command.model_dump(), function_call)

    def test_go_back_no_args(self):
        function_call = {"name": "go_back"}
        command = CommandModel.model_validate(function_call)
        self.assertIsInstance(command.root, GoBack)
        self.assertEqual(command.model_dump(), {"name": "go_back", "args": None})

    def test_go_forward(self):
        function_call = {"name": "go_forward", "args": {}}
        command = CommandModel.model_validate(function_call)
        self.assertIsInstance(command.root, GoForward)
        self.assertEqual(command.model_dump(), function_call)

    def test_go_forward_no_args(self):
        function_call = {"name": "go_forward"}
        command = CommandModel.model_validate(function_call)
        self.assertIsInstance(command.root, GoForward)
        self.assertEqual(command.model_dump(), {"name": "go_forward", "args": None})

    def test_search(self):
        function_call = {"name": "search", "args": {}}
        command = CommandModel.model_validate(function_call)
        self.assertIsInstance(command.root, Search)
        self.assertEqual(command.model_dump(), function_call)

    def test_wait5_seconds(self):
        function_call = {"name": "wait_5_seconds", "args": {}}
        command = CommandModel.model_validate(function_call)
        self.assertIsInstance(command.root, Wait5Seconds)
        self.assertEqual(command.model_dump(), function_call)

    def test_key_combination(self):
        function_call = {"name": "key_combination", "args": {"keys": "control+c"}}
        command = CommandModel.model_validate(function_call)
        self.assertIsInstance(command.root, KeyCombination)
        self.assertEqual(command.model_dump(), function_call)

    def test_screenshot(self):
        function_call = {"name": "screenshot", "args": {}}
        command = CommandModel.model_validate(function_call)
        self.assertIsInstance(command.root, Screenshot)
        self.assertEqual(command.model_dump(), function_call)

    def test_screenshot_without_args(self):
        function_call = {"name": "screenshot"}
        command = CommandModel.model_validate(function_call)
        self.assertIsInstance(command.root, Screenshot)
        self.assertEqual(command.model_dump(), {"name": "screenshot", "args": None})

    def test_shutdown(self):
        function_call = {"name": "shutdown", "args": {}}
        command = CommandModel.model_validate(function_call)
        self.assertIsInstance(command.root, Shutdown)
        self.assertEqual(command.model_dump(), function_call)

    def test_shutdown_without_args(self):
        function_call = {"name": "shutdown"}
        command = CommandModel.model_validate(function_call)
        self.assertIsInstance(command.root, Shutdown)
        self.assertEqual(command.model_dump(), {"name": "shutdown", "args": None})


if __name__ == "__main__":
    unittest.main()
