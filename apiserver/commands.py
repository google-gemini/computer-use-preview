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
from pydantic import BaseModel, Field, RootModel
from typing import Annotated, Literal, Optional, Union


class EmptyJson(BaseModel):
    pass


class NavigateArgs(BaseModel):
    url: str


class ClickAtArgs(BaseModel):
    y: int
    x: int


class HoverAtArgs(BaseModel):
    y: int
    x: int


class TypeTextAtArgs(BaseModel):
    y: int
    x: int
    text: str


class ScrollDocumentArgs(BaseModel):
    direction: Literal["up"] | Literal["down"]


class KeyCombinationArgs(BaseModel):
    keys: str


class OpenWebBrowser(BaseModel):
    name: Literal["open_web_browser"]
    args: Optional[EmptyJson] = Field(None)


class ClickAt(BaseModel):
    name: Literal["click_at"]
    args: ClickAtArgs


class HoverAt(BaseModel):
    name: Literal["hover_at"]
    args: HoverAtArgs


class TypeTextAt(BaseModel):
    name: Literal["type_text_at"]
    args: TypeTextAtArgs


class ScrollDocument(BaseModel):
    name: Literal["scroll_document"]
    args: ScrollDocumentArgs


class Wait5Seconds(BaseModel):
    name: Literal["wait_5_seconds"]
    args: Optional[EmptyJson] = Field(None)


class GoBack(BaseModel):
    name: Literal["go_back"]
    args: Optional[EmptyJson] = Field(None)


class GoForward(BaseModel):
    name: Literal["go_forward"]
    args: Optional[EmptyJson] = Field(None)


class Search(BaseModel):
    name: Literal["search"]
    args: Optional[EmptyJson] = Field(None)


class Navigate(BaseModel):
    name: Literal["navigate"]
    args: NavigateArgs


class KeyCombination(BaseModel):
    name: Literal["key_combination"]
    args: KeyCombinationArgs


class Screenshot(BaseModel):
    name: Literal["screenshot"]
    args: Optional[EmptyJson] = Field(None)


class Shutdown(BaseModel):
    name: Literal["shutdown"]
    args: Optional[EmptyJson] = Field(None)


Command = Annotated[
    Union[
        OpenWebBrowser,
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
        Shutdown,
    ],
    Field(discriminator="name"),
]


class CommandModel(RootModel):
    root: Command
