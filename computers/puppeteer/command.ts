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

// click_at(y: int, x: int)
export interface ClickAt {
  name: "click_at";
  args: {
    x: number;
    y: number;
  }
}

// hover_at(y: int, x: int)
export interface HoverAt {
  name: "hover_at";
  args: {
    x: number;
    y: number;
  }
}

// type_text_at(y: int, x: int, text: str)
export interface TypeTextAt {
  name: "type_text_at";
  args: {
    x: number;
    y: number;
    text: string;
  }
}

// scroll_document(direction: str)
export interface ScrollDocument {
  name: "scroll_document";
  args: {
    direction: string;
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
export interface ShutDown {
  name: "shut_down"
  args?: {}
}

export type Command = OpenWebBrowser
  | ClickAt
  | HoverAt
  | TypeTextAt
  | ScrollDocument
  | Wait5Seconds
  | GoBack
  | GoForward
  | Search
  | Navigate
  | KeyCombination
  | Screenshot
  | ShutDown;

export const parseCommand = (input: Record<string, any>): Command => {
  try {
    return input as Command;
  } catch (e) {
    throw new Error("Failed to parse command: " + e);
  }
};
