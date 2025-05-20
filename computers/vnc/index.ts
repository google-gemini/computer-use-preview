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
import { parseCommand } from './command';
import { BrowserShell, OsShell, ComputerShell, ScreenResolution } from './browser';
import { MessagingChannel, PubSubChannel, HttpChannel, CommandMessage } from './signalling';
import timestring from 'timestring';

const parseResolution = (): ScreenResolution => {
  const parts = (process.env.SCREEN_RESOLUTION ?? '1920x1000x16').split('x');
  if (parts.length < 2) {
    throw `invalid SCREEN_RESOLUTION: ${process.env.SCREEN_RESOLUTION}`;
  }
  return {
    width: parseInt(parts[0], 10),
    height: parseInt(parts[1], 10),
  }
};

const SESSION_ID = process.env.SESSION_ID ?? '1234';
const PUBSUB_PROJECT_ID = process.env.PUBSUB_PROJECT_ID ?? '';
const PORT = 7777;
const IDLE_TIMEOUT = timestring(process.env.IDLE_TIMEOUT || "1h", 'ms');
const HEADFULCHROME = true;
const FULLOS = (process.env.FULLOS ?? '').toLowerCase() === 'true';
const SCREEN_RESOLUTION = parseResolution();

let isReady = false;

const getSignallingChannel = (): MessagingChannel => {
  if (process.env.USE_PUBSUB === "true") {
    console.log('using PubSub signalling strategy');
    return new PubSubChannel({
      projectId: PUBSUB_PROJECT_ID,
      commandsTopic: `projects/${PUBSUB_PROJECT_ID}/topics/commands-${SESSION_ID}`,
      screenshotsTopic: `projects/${PUBSUB_PROJECT_ID}/topics/screenshots-${SESSION_ID}`,
      subscriptionName: `projects/${PUBSUB_PROJECT_ID}/subscriptions/commands-${SESSION_ID}`,
    })
  }
  console.log('using HTTP signalling strategy');
  return new HttpChannel(PORT);
};

(async () => {
  console.log("creating puppeteer worker");
  
  const channel = getSignallingChannel();

  let idleTimer: NodeJS.Timeout;

  const resetIdleTimer = () => {
    if (idleTimer) {
      clearTimeout(idleTimer);
    }
    idleTimer = setTimeout(async () => {
      console.log(`No commands received for ${process.env.IDLE_TIMEOUT || "1h"}. Shutting down.`);
      await channel.disconnect();
    }, IDLE_TIMEOUT);
  };

  resetIdleTimer();

  process.on('SIGTERM', async () => {
    console.info('SIGTERM signal received.');
    isReady = false;
    if (idleTimer) {
      clearTimeout(idleTimer);
    }
    await channel.disconnect();
  });

  let browserShell: ComputerShell | undefined;
  console.log("starting to subscribe");
  channel.subscribe(async (message: CommandMessage) => {
    if (!isReady) {
      console.warn("Received command while not ready. Ignoring.");
      return;
    }

    resetIdleTimer();

    const command = parseCommand(message.command);
    console.log(command);
    if (command.name === 'shut_down') {
      console.log("received shutdown command");
      isReady = false;
      if (idleTimer) {
        clearTimeout(idleTimer);
      }
      await channel.disconnect();
    }

    try {
      await browserShell!.runCommand(command);
      const url = await browserShell!.currentUrl();
      const screenshot = await browserShell!.screenshot();
      message.publishScreenshot(screenshot, SESSION_ID, url);
    } catch (e: Error | any) {
      console.error(e);
      if (e instanceof Error) {
        message.publishError(e.message);
      } else {
        message.publishError(e);
      }
    }
  });
  browserShell = FULLOS ? await OsShell.init() : await BrowserShell.init(!HEADFULCHROME, SCREEN_RESOLUTION); 

  isReady = true;
  console.log('Worker is ready.');
})();