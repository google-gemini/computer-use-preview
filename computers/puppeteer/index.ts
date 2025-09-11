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
import * as http from 'http'; // Import the http module
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
const READINESS_CHECK_PORT = parseInt(process.env.HEALTH_CHECK_PORT ?? '8000', 10);
const PORT = parseInt(process.env.PORT ?? '8080', 10);
const IDLE_TIMEOUT = timestring(process.env.IDLE_TIMEOUT || "1h", 'ms');
const HEADFULCHROME = (process.env.HEADFULCHROME ?? '').toLowerCase() === 'true';
const FULLOS = (process.env.FULLOS ?? '').toLowerCase() === 'true';
const SCREEN_RESOLUTION = parseResolution();
const LANG = process.env.LANG ?? 'en-US,en';

let isReady = false;

const server = http.createServer(async (req, res) => {
  if (req.url === '/ready') {
    if (isReady) {
      res.writeHead(204);
      res.end();
    } else {
      res.writeHead(503);
      res.end();
    }
    return;
  }
  else if (req.url === '/start_session' && req.method == 'POST') {
    try {
      // 1. Asynchronously read the full request body
      const body = await new Promise<string>((resolve, reject) => {
        let data = '';
        req.on('data', chunk => {
          data += chunk.toString();
        });
        req.on('end', () => resolve(data));
        req.on('error', err => reject(err));
      });

      // 2. Parse the body as JSON and extract session_id
      const { session_id } = JSON.parse(body);

      // 3. Validate that session_id is a string
      console.log(`Session ID received: ${session_id}`);

      res.writeHead(200, { 'Content-Type': 'text/plain' });
      res.write('1');

      await launchSession(session_id);

      isReady = true;
      res.write('2');

      await new Promise(resolve => setTimeout(resolve, 1000 * 60 * 55));

      res.end('done, exiting');

      process.exit(0);

    } catch (error) {
      // This catches errors from JSON.parse() or our validation
      res.writeHead(400, { 'Content-Type': 'text/plain' });
      res.end('Bad Request: Invalid JSON or missing/invalid session_id.');
    }

    return; // Stop further execution
  }

  res.writeHead(404, { 'Content-Type': 'text/plain' });
  res.end('Not Found');
});

let portToUse = SESSION_ID == '1234' ? PORT : READINESS_CHECK_PORT;

server.listen(portToUse, () => {
  console.log(`HTTP server listening on port ${portToUse}...`);
});

const getSignallingChannel = (session_id: string): MessagingChannel => {
  if (process.env.USE_PUBSUB === "true") {
    console.log('using PubSub signalling strategy');
    return new PubSubChannel({
      projectId: PUBSUB_PROJECT_ID,
      commandsTopic: `projects/${PUBSUB_PROJECT_ID}/topics/commands-${session_id}`,
      screenshotsTopic: `projects/${PUBSUB_PROJECT_ID}/topics/screenshots-${session_id}`,
      subscriptionName: `projects/${PUBSUB_PROJECT_ID}/subscriptions/commands-${session_id}`,
    })
  }
  console.log('using HTTP signalling strategy');
  return new HttpChannel(PORT);
};

const launchSession = async (session_id: string) => {
  const channel = getSignallingChannel(session_id);

  let idleTimer: NodeJS.Timeout;

  const resetIdleTimer = () => {
    if (idleTimer) {
      clearTimeout(idleTimer);
    }
    idleTimer = setTimeout(async () => {
      console.log(`No commands received for ${process.env.IDLE_TIMEOUT || "1h"}. Shutting down.`);
      await channel.disconnect();
      server.close(() => {
        process.exit(0);
      });
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
    server.close(() => {
      process.exit(0);
    });
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
    if (command.name === 'shutdown') {
      console.log("received shutdown command");
      isReady = false;
      if (idleTimer) {
        clearTimeout(idleTimer);
      }
      await channel.disconnect();
      server.close(() => {
        process.exit(0);
      });
    }

    try {
      await browserShell!.runCommand(command);
      const url = browserShell!.currentUrl();
      const screenshot = await browserShell!.screenshot();
      message.publishScreenshot(screenshot, session_id, url);
    } catch (e: Error | any) {
      console.error(e);
      if (e instanceof Error) {
        message.publishError(e.message);
      } else {
        message.publishError(e);
      }
    }
  });
  browserShell = FULLOS ? await OsShell.init() : await BrowserShell.init(!HEADFULCHROME, SCREEN_RESOLUTION, LANG);
};

(async () => {
  if (SESSION_ID == '1234') {
    console.log("Started in service mode.")
    return;
  }

  console.log("creating puppeteer worker");

  await launchSession(SESSION_ID);

  isReady = true;
  console.log('Worker is ready.');
})();