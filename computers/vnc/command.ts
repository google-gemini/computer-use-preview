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

// type_text(text: str)
export interface TypeText {
  name: "type_text";
  args: {
    text: string;
  }
}

// press_enter(text: str)
export interface PressEnter {
  name: "press_enter";
  args?: {}
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
  | TypeText
  | PressEnter
  | ScrollDocument
  | Wait5Seconds
  | GoBack
  | GoForward
  | Search
  | Navigate
  | KeyCombination
  | Screenshot
  | ShutDown;

export const parseCommand = (input: string | Record<string, any>): Command => {
  if (typeof input !== "string") {
    return input as Command;
  }
  const params = extractParams(input);
  const name = extractName(input);

  if (name === 'open_web_browser') {
    return { name: 'open_web_browser' };
  }
  if (name === 'click_at') {
    let { x, y } = extractCoords(params);
    return { name: 'click_at', args: { x, y } };
  }
  if (name === 'hover_at') {
    const { x, y } = extractCoords(params);
    return { name: 'hover_at', args: { x, y } };
  }
  if (name === 'type_text_at') {
    const { x, y } = extractCoords(params);
    return { name: 'type_text_at', args: { x, y, text: assertParam(params, "text") } };
  }
  if (name === 'type_text') {
    return { name: 'type_text', args: { text: assertParam(params, "text") } };
  }
  if (name === 'press_enter') {
    return { name: 'press_enter' };
  }
  if (name === 'scroll_document') {
    return { name: 'scroll_document', args: { direction: assertParam(params, "direction") } };
  }
  if (name === 'wait_5_seconds') {
    return { name: 'wait_5_seconds' };
  }
  if (name === 'go_back') {
    return { name: 'go_back' };
  }
  if (name === 'go_forward') {
    return { name: 'go_forward' };
  }
  if (name === 'search') {
    return { name: 'search' };
  }
  if (name === 'navigate') {
    return { name: 'navigate', args: { url: assertParam(params, 'url') as string } };
  }
  if (name === 'key_combination') {
    return { name: 'key_combination', args: { keys: assertParam(params, "keys") } };
  }
  if (name === 'screenshot') {
    return { name: 'screenshot' };
  }
  if (name === 'shut_down') {
    return { name: 'shut_down' };
  }
  throw "Unexpected command: " + input;
};

const extractName = (text: string): string => {
  const match = text.trim().match(/^[^(]+/);
  if (match !== null) {
    return match[0];
  }
  return "";
};

const extractParams = (text: string): Map<string, string> => {
  const params = new Map<string, string>();
  const match = text.trim().match(/\(([^)]+)/);
  if (match === null || match.length != 2) {
    return params;
  }
  match[1].split(", ").forEach(param => {
    const [key, ...value] = param.split(":");
    params.set(key.trim(), value.join(":").trim());
  });
  return params;
}

const extractCoords = (params: Map<string, string>): { x: number, y: number } => {
  const x = parseInt(assertParam(params, 'x'), 10);
  const y = parseInt(assertParam(params, 'y'), 10);
  return { x, y };
};

const assertParam = (params: Map<string, string>, key: string): string => {
  const val = params.get(key);
  if (!val) {
    throw "Missing param: " + key;
  }
  return val;
};