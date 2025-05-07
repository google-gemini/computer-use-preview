import http from 'http';
import {PubSub, Message, Subscription} from '@google-cloud/pubsub';
import { createClient } from 'redis';
import {Keepaliver} from './keepaliver';

const crypto = require("crypto");
type RedisClient = ReturnType<typeof createClient>;

export interface MessagingChannel {
  subscribe(handler: (message: CommandMessage) => Promise<void>): Promise<void>;
  disconnect(): Promise<void>;
}

export interface CommandMessage {
  id: string;
  command: string|Record<string, any>;
  publishScreenshot(screenshot: string, sessionID: string): Promise<void>;
  publishError(error: string): Promise<void>;
}

class HttpMessage implements CommandMessage {
  id: string;
  command: string|Record<string, any>;
  private res: http.ServerResponse<http.IncomingMessage>;

  constructor(command: string, res: http.ServerResponse<http.IncomingMessage>) {
    this.id = "";
    this.command = command;
    this.res = res;
  }
  async publishScreenshot(screenshot: string, sessionID: string): Promise<void> {
    this.res.writeHead(200, { 'Content-Type': 'application/json' });
    this.res.end(JSON.stringify({ id: this.id, session_id: sessionID, screenshot }));
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

  private keepaliver?: Keepaliver;  // For keeping this instance alive.

  constructor(port: number) {
    this.port = port;
    this.instanceId = crypto.randomUUID();
    console.log(`Instance ID: ${this.instanceId}`);
  }

  async subscribe(handler: (message: CommandMessage) => Promise<void>) {
    this.server = http.createServer(async (req, res) => {
      console.log(`Received HTTP request: ${req.method} ${req.url}`);
       if (req.url === '/instance_id') {
	 await this.keepaliver?.handleInstanceIdRequest(req, res);
       }
       else if (req.url === '/keepalive') {
         await this.keepaliver?.handleKeepaliveRequest(req, res);
       }

       else {
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

       }
    })

    // Create the keepaliver
    this.keepaliver = new Keepaliver(this.server, this.instanceId); // Updated class and property name

    // Start the HTTP server listening
    this.server.listen(this.port, () => {
      console.log(`HTTP server listening on port ${this.port}`);
    });
  }

  async disconnect() {
    if (this.keepaliver) {
      await this.keepaliver.close();
    }
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
  command: string|Record<string, any>;
  pubsub: PubSub;
  screenshotsTopic: string;

  constructor(command: string, id: string, pubsub: PubSub, screenshotsTopic: string) {
    this.id = id;
    this.command = command;
    this.pubsub = pubsub;
    this.screenshotsTopic = screenshotsTopic;
  }
  async publishScreenshot(screenshot: string, sessionID: string): Promise<void> {
    console.log("publishing screenshot for", this.id, "to topic", this.screenshotsTopic);
    const json = {id: this.id, session_id: sessionID, screenshot};
    await this.pubsub.topic(this.screenshotsTopic).publishMessage({json});
  }

  async publishError(error: string): Promise<void> {
    console.log("publishing error for: ", this.id);
    const json = {id: this.id, error};
    await this.pubsub.topic(this.screenshotsTopic).publishMessage({json});
  }
}

export class PubSubChannel implements MessagingChannel {
  commandsTopic: string;
  screenshotsTopic: string;
  pubsub: PubSub;
  subscriptionName: string;
  subscription: Subscription | null;
  interval: NodeJS.Timeout | null;

  constructor(config: {projectId: string, commandsTopic: string, screenshotsTopic: string, subscriptionName: string}){
    this.commandsTopic = config.commandsTopic;
    this.screenshotsTopic = config.screenshotsTopic;
    this.pubsub = new PubSub({projectId: config.projectId});
    this.subscriptionName = config.subscriptionName;
    this.subscription = null
    this.interval = null
  }

  async subscribe(handler: (message: CommandMessage) => Promise<void>) {
    const topic = this.pubsub.topic(this.commandsTopic);
    console.log(`Creating Subscription ${this.subscriptionName} to topic: ${this.commandsTopic}`);
    const [subscription] = await topic.createSubscription(this.subscriptionName);
    this.subscription = subscription
    console.log(`Subscription ${subscription.name} created`);

    subscription.on('message', (msg: Message) => {
        msg.ack();
        const data = JSON.parse(msg.data.toString());
        const c = new PubSubMessage(data.command, data.id, this.pubsub, this.screenshotsTopic);
        handler(c);
    });

    //hack to keep the process running
    this.interval = setInterval(() => {}, 1 << 30);
  }

  async disconnect() {
    if(this.subscription){
        await this.subscription.close();
    }
    if(this.interval){
        clearInterval(this.interval);
    }
  }
}

class RedisMessage implements CommandMessage {
  id: string;
  command: string|Record<string, any>;
  client: RedisClient;

  constructor(command: string, id: string, client: RedisClient) {
    this.id = id;
    this.command = command;
    this.client = client;
  }
  async publishScreenshot(screenshot: string, sessionID: string): Promise<void> {
    console.log("sending screenshot for", this.id)
    await this.client.publish("screenshots", JSON.stringify({ id: this.id, session_id: sessionID, screenshot }));
    console.log("screenshot submitted for", this.id)
  }

  async publishError(error: string): Promise<void> {
    console.log("publishing error for: ", this.id);
    const data = {id: this.id, error};
    await this.client.publish("screenshots", JSON.stringify(data));
    console.log("error submitted for", this.id);
  }
}

export class RedisChannel implements MessagingChannel {
  private client?: RedisClient;
  private subscriber?: RedisClient;

  constructor(
    private redisHost: string,
    private redisPort: string,
    private sessionID: string,
  ){}

  async subscribe(handler: (message: CommandMessage) => Promise<void>) {
    this.client = await createClient({
      url: `redis://${this.redisHost}:${this.redisPort}`,
    })
      .on('error', err => console.log('Redis Client Error', err))
      .connect();

    this.subscriber = this.client.duplicate();
    this.subscriber.on('error', err => console.error(err));

    await this.subscriber.connect();
    await this.subscriber.subscribe(`session:${this.sessionID}`, async(data: string) => {
      const eventData = JSON.parse(data);
      const message = new RedisMessage(eventData.command, eventData.id, this.client as RedisClient);
      await handler(message);
    });
  }

  async disconnect() {
    if (this.subscriber) {
      await this.subscriber.disconnect();
    }
    if (this.client) {
      await this.client.disconnect();
    }
  }
}
