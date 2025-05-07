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
    GoBack,
    GoForward,
    Search,
    Wait5Seconds,
    KeyCombination,
    Screenshot,
)


class TestCommands(unittest.TestCase):

    def test_navigate(self):
        command = CommandModel.model_validate(
            {"name": "navigate", "args": {"url": "foo"}}
        )
        self.assertIsInstance(command.root, Navigate)
        self.assertEqual(command.to_string(), "navigate(url: foo)")

    def test_click_at(self):
        command = CommandModel.model_validate(
            {"name": "click_at", "args": {"y": 1, "x": 2}}
        )
        self.assertIsInstance(command.root, ClickAt)
        self.assertEqual(command.to_string(), "click_at(y: 1, x: 2)")

    def test_hover_at(self):
        command = CommandModel.model_validate(
            {"name": "hover_at", "args": {"y": 1, "x": 2}}
        )
        self.assertIsInstance(command.root, HoverAt)
        self.assertEqual(command.to_string(), "hover_at(y: 1, x: 2)")

    def test_type_text_at(self):
        command = CommandModel.model_validate(
            {
                "name": "type_text_at",
                "args": {"y": 1, "x": 2, "text": "one"},
            }
        )
        self.assertIsInstance(command.root, TypeTextAt)
        self.assertEqual(
            command.to_string(),
            "type_text_at(y: 1, x: 2, text: one)",
        )

    def test_scroll_document(self):
        command = CommandModel.model_validate(
            {"name": "scroll_document", "args": {"direction": "up"}}
        )
        self.assertIsInstance(command.root, ScrollDocument)
        self.assertEqual(command.to_string(), "scroll_document(direction: up)")

    def test_go_back(self):
        command = CommandModel.model_validate({"name": "go_back", "args": {}})
        self.assertIsInstance(command.root, GoBack)
        self.assertEqual(command.to_string(), "go_back()")

    def test_go_back_no_args(self):
        command = CommandModel.model_validate({"name": "go_back"})
        self.assertIsInstance(command.root, GoBack)
        self.assertEqual(command.to_string(), "go_back()")

    def test_go_forward(self):
        command = CommandModel.model_validate({"name": "go_forward", "args": {}})
        self.assertIsInstance(command.root, GoForward)
        self.assertEqual(command.to_string(), "go_forward()")

    def test_go_forward(self):
        command = CommandModel.model_validate({"name": "go_forward"})
        self.assertIsInstance(command.root, GoForward)
        self.assertEqual(command.to_string(), "go_forward()")

    def test_search(self):
        command = CommandModel.model_validate({"name": "search", "args": {}})
        self.assertIsInstance(command.root, Search)
        self.assertEqual(command.to_string(), "search()")

    def test_wait5_seconds(self):
        command = CommandModel.model_validate({"name": "wait_5_seconds", "args": {}})
        self.assertIsInstance(command.root, Wait5Seconds)
        self.assertEqual(command.to_string(), "wait_5_seconds()")

    def test_key_combination(self):
        command = CommandModel.model_validate(
            {"name": "key_combination", "args": {"keys": "control+c"}}
        )
        self.assertIsInstance(command.root, KeyCombination)
        self.assertEqual(command.to_string(), "key_combination(keys: control+c)")

    def test_screenshot(self):
        command = CommandModel.model_validate({"name": "screenshot", "args": {}})
        self.assertIsInstance(command.root, Screenshot)
        self.assertEqual(command.to_string(), "screenshot()")

    def test_screenshot_without_args(self):
        command = CommandModel.model_validate({"name": "screenshot"})
        self.assertIsInstance(command.root, Screenshot)
        self.assertEqual(command.to_string(), "screenshot()")


if __name__ == "__main__":
    unittest.main()
