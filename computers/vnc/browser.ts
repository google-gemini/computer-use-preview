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
  currentUrl(): Promise<string>;
}

export interface ScreenResolution {
  width: number;
  height: number;
}

export class BrowserShell implements ComputerShell {
  browser: Browser;
  
  headfulShell?: OsShell;
  constructor(browser: Browser, headless: boolean = true) {
    this.browser = browser;
    if (!headless) {
      this.headfulShell = new OsShell();
    }
  }

  static async init(headless: boolean, resolution: ScreenResolution): Promise<BrowserShell> {
    console.log(`launching puppeteer with headless=${headless}`);
    const b = await puppeteer.launch({
      executablePath: '/usr/bin/google-chrome-stable',
      defaultViewport: null,
      args: [
        '--no-sandbox',
        '--disable-gpu',
        '--disable-blink-features=AutomationControlled',  
        '--no-default-browser-check',
        `--window-size=${resolution.width},${resolution.height}`,
        '--start-maximized'
      ],
      ignoreDefaultArgs: ['--enable-automation'],
      headless,
      protocolTimeout: 300000,
    });
    console.log('puppeteer ready');
    return new BrowserShell(b, headless);
  }

  async runCommand(c: Command): Promise<void> {
    if (this.headfulShell && HEADFUL_COMMANDS.has(c.name)) {
      return await this.headfulShell.runCommand(c);
    }
    const page = await this.page();
    switch (c.name) {
      case 'open_web_browser':
        await page.goto('https://www.google.com');
        break;
      case 'click_at':
          await page.mouse.click(c.args.x, c.args.y);
          // adding a little delay so the screenshot shows the result of the click
          await new Promise(resolve => setTimeout(resolve, 300));
          break;
      case 'hover_at':
        await page.mouse.move(c.args.x, c.args.y);
        break;
      case 'type_text_at':
        await page.mouse.click(c.args.x, c.args.y);
        // see https://github.com/puppeteer/puppeteer/issues/1648
        for (let i = 0; i < c.args.text.length; i++) {
          await page.keyboard.type(c.args.text[i]);
          await new Promise(resolve => setTimeout(resolve, 100));
        }
        await page.keyboard.press('Enter');
        break;
      case 'type_text':
        for (let i = 0; i < c.args.text.length; i++) {
          await page.keyboard.type(c.args.text[i]);
          await new Promise(resolve => setTimeout(resolve, 100));
        }
        break;
      case 'press_enter':
        await page.keyboard.press('Enter');
        break;
      case 'scroll_document':
        let deltaX = 0;
        let deltaY = 0;
        let offset = 400;
        if (c.args.direction === 'left') {
          deltaX = -offset;
        }
        if (c.args.direction === 'right') {
          deltaX = offset;
        }
        if (c.args.direction === 'up') {
          deltaY = -offset;
        }
        if (c.args.direction === 'down') {
          deltaY = offset;
        }
        await page.mouse.wheel({deltaY, deltaX});
        break;
      case 'wait_5_seconds':
        await new Promise(resolve => setTimeout(resolve, 5000));
        break;
      case 'go_back':
        await Promise.all([
          page.waitForNavigation({timeout: 5000}),
          page.goBack(),
        ]);
        break;
      case 'go_forward':
        await Promise.all([
          page.waitForNavigation({timeout: 5000}),
          page.goForward(),
        ]);
        break;
      case 'search':
        await page.goto('https://www.google.com');
        break;
      case 'navigate':
        await Promise.all([
          page.waitForNavigation({timeout: 5000}),
          page.goto(c.args.url),
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
          await page.keyboard.down(keyInput);
        }
        for (const keyInput of keyInputs) {
          console.log(`releasing key: ${keyInput}`);
          await page.keyboard.up(keyInput);
        }
        break;
    }
  }

  async currentUrl(): Promise<string> {
    const page = await this.page();
    return page.url();
  }

  async screenshot(): Promise<string> {
    if (this.headfulShell) {
      return await this.headfulShell.screenshot();
    }
    const page = await this.page();
    return await page.screenshot({
      encoding: 'base64',
      type: 'png',
      captureBeyondViewport: false,
    });
  }

  private async page(): Promise<Page> {
    const pages = await this.browser.pages();
    if (pages.length < 1) {
      console.log('no active pages. Creating one');
      return await this.browser.newPage();
    } 
    if (pages.length > 1) {
      console.log("Chrome has more than one tab open, picking the visible one");
      for (let page of pages) {
        const isHidden = await page.evaluate(() => document.hidden);
        if (!isHidden) {
          return page;
        }
      }
    }
    return pages[0];
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

  async currentUrl(): Promise<string> {
    return "";
  }

  async doubleClick(x: number, y: number): Promise<void> {
    const {stdout, stderr} = await execAsync(`xdotool mousemove ${x} ${y} click --repeat 2 1`);
    console.log(stdout);
    console.log(stderr);
  }

  async screenshot(): Promise<string> {
    const {stdout, stderr} = await execAsync("scrot --pointer - | base64 -w 0", {maxBuffer: 6 * 1024 * 1024});
    return stdout;
  }
}
