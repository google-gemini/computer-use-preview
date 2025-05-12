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
import http from 'http';
import { PubSub, Message, Subscription } from '@google-cloud/pubsub';

export interface MessagingChannel {
  subscribe(handler: (message: CommandMessage) => Promise<void>): void;
  disconnect(): Promise<void>;
}

export interface CommandMessage {
  id: string;
  command: string | Record<string, any>;
  publishScreenshot(screenshot: string, sessionID: string, url: string): Promise<void>;
  publishError(error: string): Promise<void>;
}

class HttpMessage implements CommandMessage {
  id: string;
  command: string | Record<string, any>;
  private res: http.ServerResponse<http.IncomingMessage>;

  constructor(command: string, res: http.ServerResponse<http.IncomingMessage>) {
    this.id = "";
    this.command = command;
    this.res = res;
  }
  async publishScreenshot(screenshot: string, sessionID: string, url: string): Promise<void> {
    this.res.writeHead(200, { 'Content-Type': 'application/json' });
    this.res.end(JSON.stringify({ id: this.id, session_id: sessionID, screenshot, url }));
  }

  async publishError(error: string): Promise<void> {
    this.res.writeHead(500, { 'Content-Type': 'application/json' });
    this.res.end(JSON.stringify({ error }));
  }
}

export class HttpChannel implements MessagingChannel {
  port: number;
  server?: http.Server;
  instanceId: string;  // Unique ID for this instance

  constructor(port: number) {
    this.port = port;
    this.instanceId = crypto.randomUUID();
    console.log(`Instance ID: ${this.instanceId}`);
  }

  subscribe(handler: (message: CommandMessage) => Promise<void>) {
    this.server = http.createServer(async (req, res) => {
      try {
        const body = await this.getBody(req);
        console.log("HTTP Body:", body);
        const json = JSON.parse(body);
        // Adjust based on your CommandMessage structure
        const command = "command" in json ? json.command : json;
        await handler(new HttpMessage(command, res));
      } catch (error) {
        console.error("Error handling HTTP request:", error);
        if (!res.headersSent) {
          res.writeHead(500, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ error: 'Internal Server Error' }));
        }
      }
    });

    // Start the HTTP server listening
    this.server.listen(this.port, () => {
      console.log(`HTTP server listening on port ${this.port}`);
    });
  }

  async disconnect() {
    if (this.server) {
      this.server.close();
    }
  }

  private async getBody(request: http.IncomingMessage): Promise<string> {
    return new Promise((resolve) => {
      const bodyParts: Buffer[] = [];
      let body;
      request.on('data', (chunk: Buffer) => {
        bodyParts.push(chunk);
      }).on('end', () => {
        body = Buffer.concat(bodyParts).toString();
        resolve(body);
      });
    });
  }
}

class PubSubMessage implements CommandMessage {
  id: string;
  command: string | Record<string, any>;
  pubsub: PubSub;
  screenshotsTopic: string;

  constructor(command: string, id: string, pubsub: PubSub, screenshotsTopic: string) {
    this.id = id;
    this.command = command;
    this.pubsub = pubsub;
    this.screenshotsTopic = screenshotsTopic;
  }
  async publishScreenshot(screenshot: string, sessionID: string, url: string): Promise<void> {
    console.log("publishing screenshot for", this.id, "to topic", this.screenshotsTopic);
    const json = { id: this.id, session_id: sessionID, screenshot, url };
    await this.pubsub.topic(this.screenshotsTopic).publishMessage({ json });
  }

  async publishError(error: string): Promise<void> {
    console.log("publishing error for: ", this.id);
    const json = { id: this.id, error };
    await this.pubsub.topic(this.screenshotsTopic).publishMessage({ json });
  }
}

export class PubSubChannel implements MessagingChannel {
  commandsTopic: string;
  screenshotsTopic: string;
  pubsub: PubSub;
  subscriptionName: string;
  subscription: Subscription | null;
  interval: NodeJS.Timeout | null;

  constructor(config: { projectId: string, commandsTopic: string, screenshotsTopic: string, subscriptionName: string }) {
    this.commandsTopic = config.commandsTopic;
    this.screenshotsTopic = config.screenshotsTopic;
    this.pubsub = new PubSub({ projectId: config.projectId });
    this.subscriptionName = config.subscriptionName;
    this.subscription = null
    this.interval = null
  }

  subscribe(handler: (message: CommandMessage) => void) {
    const topic = this.pubsub.topic(this.commandsTopic);
    console.log(`Creating Subscription ${this.subscriptionName} to topic: ${this.commandsTopic}`);
    topic.createSubscription(this.subscriptionName, (error, subscription) => {
      if (error || !subscription) {
        throw "Failed to create subscription";
      }
      this.subscription = subscription;
      console.log(`Subscription ${subscription.name} created`);

      subscription.on('message', (msg: Message) => {
        msg.ack();
        const data = JSON.parse(msg.data.toString());
        const c = new PubSubMessage(data.command, data.id, this.pubsub, this.screenshotsTopic);
        handler(c);
      });
    });
    //hack to keep the process running
    this.interval = setInterval(() => { }, 1 << 30);
  }

  async disconnect() {
    if (this.subscription) {
      await this.subscription.close();
    }
    if (this.interval) {
      clearInterval(this.interval);
    }
  }
}
