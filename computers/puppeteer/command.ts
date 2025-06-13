// Copyright 2025 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

// open_web_browser()
export interface OpenWebBrowser {
  name: "open_web_browser";
  args?: {}
}

// click_at(x: int, y: int)
export interface ClickAt {
  name: "click_at";
  args: {
    x: number;
    y: number;
  }
}

// hover_at(x: int, y: int)
export interface HoverAt {
  name: "hover_at";
  args: {
    x: number;
    y: number;
  }
}

// type_text_at(x: int, y: int, text: str, press_enter: bool, clear_before_typing: bool)
export interface TypeTextAt {
  name: "type_text_at";
  args: {
    x: number;
    y: number;
    text: string;
    press_enter: boolean;
    clear_before_typing: boolean;
  }
}

// scroll_document(direction: "up" | "down" | "left" | "right")
export interface ScrollDocument {
  name: "scroll_document";
  args: {
    direction: "up" | "down" | "left" | "right";
  }
}

// scroll_at(x: int, y: int, direction: "up" | "down" | "left" | "right", magnitude: int)
export interface ScrollAt {
  name: "scroll_at";
  args: {
    x: number;
    y: number;
    direction: "up" | "down" | "left" | "right";
    magnitude: number;
  }
}

// drag_and_drop(x: int, y: int, destination_x: int, destination_y: int)
export interface DragAndDrop {
  name: "drag_and_drop";
  args: {
    x: number;
    y: number;
    destination_x: number;
    destination_y: number;
  }
}

// wait_5_seconds()
export interface Wait5Seconds {
  name: "wait_5_seconds";
  args?: {}
}

// go_back()
export interface GoBack {
  name: "go_back";
  args?: {}
}

// go_forward()
export interface GoForward {
  name: "go_forward";
  args?: {}
}

// search()
export interface Search {
  name: "search";
  args?: {}
}

// navigate(url: str)
export interface Navigate {
  name: "navigate";
  args: {
    url: string;
  }
}

// key_combination(keys: str)
export interface KeyCombination {
  name: "key_combination";
  args: {
    keys: string; // Changed from string[] to string
  },
}

// Worker specific command
export interface Screenshot {
  name: "screenshot";
  args?: {}
}

// Worker specific command
export interface Shutdown {
  name: "shutdown"
  args?: {}
}

export type Command = OpenWebBrowser
  | ClickAt
  | HoverAt
  | TypeTextAt
  | ScrollDocument
  | ScrollAt
  | DragAndDrop
  | Wait5Seconds
  | GoBack
  | GoForward
  | Search
  | Navigate
  | KeyCombination
  | Screenshot
  | Shutdown;

export const parseCommand = (input: string | Record<string, any>): Command => {
  try {
    if (typeof input === "string") {
      input = JSON.parse(input);
    }
    return input as Command;
  } catch (e) {
    throw new Error("Failed to parse command: " + e);
  }
};
