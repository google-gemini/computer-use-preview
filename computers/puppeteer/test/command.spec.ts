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
import { parseCommand } from '../command';
import { strict as assert } from 'node:assert';

describe('#parseCommand() with JSON commands', function () {
  it('parses navigate(url: str)', () => {
    const command = parseCommand({ "name": "navigate", "args": { "url": "http://foo.bar/com" } });
    assert.equal(command.name, 'navigate');
    assert.equal(command.args.url, 'http://foo.bar/com');
  });

  it('parses click_at(x: int, y: int)', () => {
    const command = parseCommand({ "name": "click_at", "args": { "x": 1, "y": 2 } });
    assert.equal(command.name, 'click_at');
    assert.equal(command.args.x, 1);
    assert.equal(command.args.y, 2);
  });

  it('parses hover_at(x: int, y: int)', () => {
    const command = parseCommand({ "name": "hover_at", "args": { "x": 4, "y": 3 } });
    assert.equal(command.name, 'hover_at');
    assert.equal(command.args.x, 4);
    assert.equal(command.args.y, 3);
  });

  it('parses type_text_at(y: int, x: int, text: str, clear_existing_text: bool)', () => {
    const command = parseCommand({ "name": "type_text_at", "args": { "x": 4, "y": 3, "text": "banana fofana", "clear_existing_text": true } });
    assert.equal(command.name, 'type_text_at');
    assert.equal(command.args.x, 4);
    assert.equal(command.args.y, 3);
  });

  it('parses scroll_document(direction: str)', () => {
    const command = parseCommand({ "name": "scroll_document", "args": { "direction": "left" } });
    assert.equal(command.name, 'scroll_document');
    assert.equal(command.args.direction, 'left');
  });

  it('parses go_back()', () => {
    const command = parseCommand({ "name": "go_back" });
    assert.equal(command.name, 'go_back');
  });

  it('parses go_forward()', () => {
    const command = parseCommand({ "name": "go_forward" });
    assert.equal(command.name, 'go_forward');
  });

  it('parses search()', () => {
    const command = parseCommand({ "name": "search" });
    assert.equal(command.name, 'search');
  });

  it('parses wait_5_seconds()', () => {
    const command = parseCommand({ "name": "wait_5_seconds" });
    assert.equal(command.name, 'wait_5_seconds');
  });

  it('parses key_combination(keys: str)', () => {
    const command = parseCommand({ "name": "key_combination", "args": { "keys": "Control+Shift+c" } });
    assert.equal(command.name, 'key_combination');
    assert.deepEqual(command.args.keys, 'Control+Shift+c');
  });

  it('parses key_combination(keys: Space)', () => {
    const command = parseCommand({ "name": "key_combination", "args": { "keys": "Space" } });
    assert.equal(command.name, 'key_combination');
    assert.deepEqual(command.args.keys, 'Space');
  });

  it('parses screenshot()', () => {
    const command = parseCommand({ "name": "screenshot" });
    assert.equal(command.name, 'screenshot');
  });

  it('parses JSON string', () => {
    const command = parseCommand('{ "name": "key_combination", "args": { "keys": "Space" } }');
    assert.equal(command.name, 'key_combination');
    assert.deepEqual(command.args.keys, 'Space');
  });
});