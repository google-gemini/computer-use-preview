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
import puppeteer, { Browser, KeyInput, Page } from 'puppeteer';
import {Command} from './command';
import { spawn, exec } from 'node:child_process';
import {promisify} from 'util';

const execAsync = promisify(exec);

const XDO_KEY_MAP: {[key: string]: string} = {
  "Backspace": "BackSpace",
  "Enter": "Return",
  "Space": "space",
  "-": "minus",
  "/": "slash",
  ":": "colon",
  ".": "period",
};

const HEADFUL_COMMANDS = new Set<string>([
  'click_at',
  'hover_at',
  'type_text_at',
  'key_combination'
])


export interface ComputerShell {
  runCommand(c: Command): Promise<void>;
  screenshot(): Promise<string>;
  currentUrl(): string;
}

export interface ScreenResolution {
  width: number;
  height: number;
}

export class BrowserShell implements ComputerShell {
  browser: Browser;
  page: Page;
  headfulShell?: OsShell;
  constructor(browser: Browser, page: Page, headless: boolean = true) {
    this.browser = browser;
    this.page = page;
    if (!headless) {
      this.headfulShell = new OsShell();
    }
  }

  static async init(headless: boolean, resolution: ScreenResolution, lang: string): Promise<BrowserShell> {
    console.log(`launching puppeteer with headless=${headless}`);
    const b = await puppeteer.launch({
      executablePath: '/usr/bin/google-chrome-stable',
      args: [
        '--no-sandbox',
        '--disable-gpu',
        '--disable-blink-features=AutomationControlled',
        `--lang=${lang}`
      ],
      ignoreDefaultArgs: ['--enable-automation'],
      headless,
    });
    const p = await b.newPage();
    await p.setViewport(resolution);
    console.log('puppeteer ready');
    return new BrowserShell(b, p, headless);
  }

  async runCommand(c: Command): Promise<void> {
    if (this.headfulShell && HEADFUL_COMMANDS.has(c.name)) {
      return await this.headfulShell.runCommand(c);
    }
    switch (c.name) {
      case 'open_web_browser':
        await this.page.goto('https://www.google.com');
        break;
      case 'click_at':
          await this.page.mouse.click(c.args.x, c.args.y);
          // adding a little delay so the screenshot shows the result of the click
          await new Promise(resolve => setTimeout(resolve, 300));
          break;
      case 'hover_at':
        await this.page.mouse.move(c.args.x, c.args.y);
        break;
      case 'type_text_at':
        await this.page.mouse.click(c.args.x, c.args.y);
        // see https://github.com/puppeteer/puppeteer/issues/1648
        for (let i = 0; i < c.args.text.length; i++) {
          await this.page.keyboard.type(c.args.text[i]);
          await new Promise(resolve => setTimeout(resolve, 100));
        }
        await this.page.keyboard.press('Enter');
        break;
      case 'scroll_document':
        let deltaX = 0;
        let deltaY = 0;
        if (c.args.direction === 'left') {
          deltaX = -900;
        }
        if (c.args.direction === 'right') {
          deltaX = 900;
        }
        if (c.args.direction === 'up') {
          deltaY = -900;
        }
        if (c.args.direction === 'down') {
          deltaY = 900;
        }
        await this.page.mouse.wheel({deltaY, deltaX});
        break;
      case 'wait_5_seconds':
        await new Promise(resolve => setTimeout(resolve, 5000));
        break;
      case 'go_back':
        await Promise.all([
          this.page.waitForNavigation({timeout: 5000}),
          this.page.goBack(),
        ]);
        break;
      case 'go_forward':
        await Promise.all([
          this.page.waitForNavigation({timeout: 5000}),
          this.page.goForward(),
        ]);
        break;
      case 'search':
        await this.page.goto('https://www.google.com');
        break;
      case 'navigate':
        await Promise.all([
          this.page.waitForNavigation({timeout: 5000}),
          this.page.goto(c.args.url),
        ]);
        break;
      case 'key_combination':
        // Split on '+' and send each key separately
        console.log(`typing keys: ${c.args.keys}`);
        const keys = c.args.keys.split('+');
        console.log(`typing keys (split): ${keys}`);
        const keyInputs: KeyInput[] = [];
        for (const key of keys) {
          // If the key is >1 char, capitalize the first letter so that
          // we can cast to KeyInput.
          // TODO: Make this logic more robust.
          if (key.length > 1) {
            const formattedKey = key.charAt(0).toUpperCase() + key.slice(1).toLowerCase();
            keyInputs.push(formattedKey as KeyInput);
          } else {
            keyInputs.push(key as KeyInput);
          }
        }
        // Execute the key presses
        for (const keyInput of keyInputs) {
          console.log(`pressing key: ${keyInput}`);
          await this.page.keyboard.down(keyInput);
        }
        for (const keyInput of keyInputs) {
          console.log(`releasing key: ${keyInput}`);
          await this.page.keyboard.up(keyInput);
        }
        break;
    }
  }

  currentUrl(): string {
    return this.page.url();
  }

  async screenshot(): Promise<string> {
    if (this.headfulShell) {
      return await this.headfulShell.screenshot();
    }
    return await this.page.screenshot({
      encoding: 'base64',
      type: 'png',
      captureBeyondViewport: false,
    });
  }
}

export class OsShell implements ComputerShell {

  constructor() {}

  static async init(): Promise<OsShell> {
    return new OsShell();
  }

  async runCommand(c: Command): Promise<void> {
    switch (c.name) {
      case 'wait_5_seconds':
        await new Promise(resolve => setTimeout(resolve, 5000));
        break;
      case 'navigate':
        console.log("unimplemented command: ", c.name);
        break;
      case 'go_back':
        console.log("unimplemented command: ", c.name);
        break;
      case 'go_forward':
        console.log("unimplemented command: ", c.name);
        break;
      case 'click_at':
        await execAsync(`xdotool mousemove ${c.args.x} ${c.args.y} click 1`);
        // adding a little delay so the screenshot shows the result of the click
        await new Promise(resolve => setTimeout(resolve, 300));
        break;
      case 'hover_at':
        await execAsync(`xdotool mousemove ${c.args.x} ${c.args.y}`);
        break;
      case 'type_text_at':
        await execAsync(`xdotool mousemove ${c.args.x} ${c.args.y} click 1`);
        await new Promise(resolve => setTimeout(resolve, 200));
        await execAsync(`xdotool type -- '${c.args.text}'`);
        break;
      case 'key_combination':
        // const keys = c.args.keys.map((k) => k in XDO_KEY_MAP ? XDO_KEY_MAP[k] : k);
        // console.log(`typing keys: ${keys}`)
        // const {stdout, stderr} = await execAsync(`xdotool key ${keys.join("+")}`);
        // console.log(stdout);
        // console.log(stderr);
        // TODO: Update this to use string instead of list of strings.
        break;
      case 'scroll_document':
        let mouseButton = 4;
        if (c.args.direction === 'left') {
          mouseButton = 6;
        }
        if (c.args.direction === 'right') {
          mouseButton = 7;
        }
        if (c.args.direction === 'up') {
          mouseButton = 4;
        }
        if (c.args.direction === 'down') {
          mouseButton = 5;
        }
        await execAsync(`xdotool click ${mouseButton}`);
        break;
    }
  }

  currentUrl(): string {
    return "";
  }

  async screenshot(): Promise<string> {
    const {stdout, stderr} = await execAsync("scrot --pointer - | base64 -w 0");
    return stdout;
  }
}