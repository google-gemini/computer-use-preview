import * as http from 'http';
import { WebSocketServer, WebSocket } from 'ws';

// Define the interval duration for sending the instance ID (5 seconds)
const INSTANCE_ID_SEND_INTERVAL_MS = 5000;
// Delay in milliseconds before attempting reconnect (e.g., 5 seconds)
const RECONNECT_DELAY_MS = 1000;
// Define the interval duration for running time logging (e.g., 5 seconds)
const RUNNING_TIME_LOG_INTERVAL_MS = 5000;

export class Keepaliver {
  private httpService: http.Server;
  private instanceId: string;
  private wsServer?: WebSocketServer;

  // Keepalive WebSocket Client State
  private keepaliveConnection?: WebSocket | null = null;
  private reconnectTimerId?: NodeJS.Timeout | null = null; // Timer ID for scheduled reconnect

  // For logging running time.
  private startTime: Date;
  private runningTimeTimerId?: NodeJS.Timeout | null = null;
  private instanceIdSentInterval = 1000;  // Interval of sending the instance ID through the stream

  constructor(httpServer: http.Server, instanceId: string) {
    this.httpService = httpServer;
    this.startTime = new Date();
    this.instanceId = instanceId;
    console.log(`Keepaliver: Instance ID: ${this.instanceId}`);
    console.log(`Keepaliver: Instance started at: ${this.startTime.toISOString()}`);

    this.setupWebSocketServer();
  }

  private getRunningTime(): string {
    const now = new Date();
    const runningTimeMs = now.getTime() - this.startTime.getTime();

    const totalSeconds = Math.floor(runningTimeMs / 1000);
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = totalSeconds % 60;

    return `${hours}h ${minutes}m ${seconds}s`;
  }

  private startRunningTimeLogging(): void {
    if (this.runningTimeTimerId !== null) {
      return;
    }

    console.log(`Keepaliver: Starting runnting time logging every ${RUNNING_TIME_LOG_INTERVAL_MS}ms.`);
    this.runningTimeTimerId = setInterval(() => {
      const runningTime = this.getRunningTime()
      console.log(`Keepaliver: Total running time: ${runningTime}`);
    }, RUNNING_TIME_LOG_INTERVAL_MS);
  }


  private setupWebSocketServer() {
    this.wsServer = new WebSocketServer({ server: this.httpService });

    this.wsServer.on('connection', (ws: WebSocket, request: http.IncomingMessage) => {
      console.log(`Keepaliver: WebSocket server connection received: ${request.url}`);

      if (request.url === '/instance_id') {
        console.log(`Keepaliver: Client connected to /instance_id. Sending instance ID: ${this.instanceId}`);
        ws.send(this.instanceId);

	// Start an interval to send the instance ID repeatedly
        const intervalId = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) { // Only send if the connection is still open
            ws.send(this.instanceId);
          } else {
            // Connection is not open, clear the interval
            console.log('Keepaliver: Client connection not open, clearing interval.');
            clearInterval(intervalId);
          }
        }, INSTANCE_ID_SEND_INTERVAL_MS);

        // Store the interval ID on the websocket object so we can clear it later
        // We use 'as any' to add a custom property to the WebSocket object
        (ws as any).instanceIdInterval = intervalId

        ws.on('message', (message: string) => {
          console.log(`Keepaliver: Server received message on /instance_id: ${message}`);
        });

        ws.on('error', (error) => {
          console.error(`Keepaliver: Server WebSocket error on /instance_id connection:`, error);
	  // Clear the interval on error
          if ((ws as any).instanceIdInterval) {
            clearInterval((ws as any).instanceIdInterval);
            console.log('Keepaliver: Cleared instance ID interval on error.');
          }
        });

        ws.on('close', (code, reason) => {
          console.log(`Keepaliver: Server WebSocket connection closed on /instance_id. Code: ${code}, Reason: ${reason.toString()}`);
	  // Clear the interval on close
          if ((ws as any).instanceIdInterval) {
            clearInterval((ws as any).instanceIdInterval);
            console.log('Keepaliver: Cleared instance ID interval on close.');
          }
        });

      } else {
        console.log(`Keepaliver: Unauthorized WebSocket connection attempt to ${request.url}. Closing.`);
        ws.close(1000, 'Unauthorized path');
      }
    });

    this.wsServer.on('error', (error) => {
      console.error('Keepaliver: WebSocket server error:', error);
    });

    this.wsServer.on('listening', () => {
      console.log('Keepaliver: WebSocket server is listening');
    });
  }

  async handleInstanceIdRequest(req: http.IncomingMessage, res: http.ServerResponse): Promise<void> {
    if (!req.headers['upgrade'] || req.headers['upgrade'].toLowerCase() !== 'websocket') {
      res.writeHead(405, { 'Allow': 'GET, POST, UPGRADE' });
      res.end('Method Not Allowed or Not a WebSocket Upgrade');
      return;
    }
  }

  // Handler for the /keepalive HTTP endpoint - Triggers the initial connection attempt
  async handleKeepaliveRequest(req: http.IncomingMessage, res: http.ServerResponse): Promise<void> {
    if (req.method !== 'POST' && req.method !== 'GET') {
      res.writeHead(405, { 'Allow': 'GET, POST' });
      res.end('Method Not Allowed');
      return;
    }

    console.log('Keepaliver: Received request for /keepalive');
    this.startRunningTimeLogging();

    // Check if a connection is already active, connecting, or scheduled to reconnect
    if ((this.keepaliveConnection &&
      (this.keepaliveConnection.readyState === WebSocket.OPEN ||
        this.keepaliveConnection.readyState === WebSocket.CONNECTING)) ||
      this.reconnectTimerId !== null)
      {
        console.log('Keepaliver: Keepalive connection is already active, connecting, or scheduled. Returning OK.');
        res.writeHead(200, { 'Content-Type': 'text/plain' });
        res.end('OK - connection already active');
        return;
      }

    // If no active connection, attempt to establish one
    console.log('Keepaliver: No active keepalive connection or scheduled reconnect. Initiating connection attempt.');
    try {
      this.establishConnection();
      res.writeHead(200, { 'Content-Type': 'text/plain' });
      res.end('OK - attempting to establish keepalive connection');
    } catch (error) {
      console.error(`Keepaliver: Failed to initiate connection attempt:`, error);
      res.writeHead(500, { 'Content-Type': 'text/plain' });
      res.end('Error initiating keepalive connection');
    }
  }

  // Method to establish the WebSocket client connection
  private establishConnection(): void {
    const targetUrl = this.getTargetURL();
    if (!targetUrl) {
      console.error('Keepaliver: KEEPALIVE_TARGET_URL environment variable is not set. Cannot establish keepalive connection.');
      // Do NOT schedule reconnect here, as it's a configuration error, not a transient network error.
      return;
    }

    const wsBaseUrl = this.replaceHTTPWithWS(targetUrl);
    const wsTargetUrl = `${wsBaseUrl}/instance_id`;

    console.log(`Keepaliver: Establishing WebSocket connection to ${wsTargetUrl}`);

    try {
      const newConnection = new WebSocket(wsTargetUrl);

      // Assign event handlers to the new connection instance
      newConnection.onopen = () => {
        console.log(`Keepaliver: Keepalive WebSocket connected to ${wsTargetUrl}`);
        // Clear any pending reconnect timer on successful connection
        if (this.reconnectTimerId !== null) {
          clearTimeout(this.reconnectTimerId);
          this.reconnectTimerId = null;
          console.log('Keepaliver: Cleared reconnect timer on successful connection.');
        }
      };

      newConnection.onmessage = (event) => {
        const receivedInstanceId = event.data.toString(); // Ensure data is a string

        if (receivedInstanceId === this.instanceId) {
          console.log(`Keepaliver: Received instance ID matches local instance ID (${this.instanceId}). Connection is OK.`);
          // No action needed, keep the connection open
        } else {
          console.warn(`Keepaliver: Received instance ID (${receivedInstanceId}) does NOT match local instance ID (${this.instanceId}). Closing connection and attempting reconnect.`);
          // Close the current connection
          newConnection.close(1000, 'Instance ID mismatch'); // 1000 is Normal Closure
          // The onclose handler will be triggered by this, which schedules the reconnect.
        }
      };

      newConnection.onerror = (event) => {
        console.error(`Keepaliver: Keepalive WebSocket error to ${wsTargetUrl}:`, event.error);
        // Error often precedes close, but schedule reconnect just in case
        this.scheduleReconnect();
      };

      newConnection.onclose = (event) => {
        console.log(`Keepaliver: Keepalive WebSocket connection closed to ${wsTargetUrl}. Code: ${event.code}, Reason: ${event.reason}`);
        // Clear the reference to the closed connection
        if (this.keepaliveConnection === newConnection) {
          this.keepaliveConnection = null;
        }
        // Schedule reconnect after connection closes
        this.scheduleReconnect();
      };

      // Store the new connection instance
      this.keepaliveConnection = newConnection;

    } catch (error) {
      console.error(`Keepaliver: Failed to create WebSocket client for ${wsTargetUrl}:`, error);
      // Schedule reconnect if client creation fails
      this.scheduleReconnect();
    }
  }

  // Method to schedule a reconnect attempt after a delay
  private scheduleReconnect(): void {
    // Only schedule if no reconnect is already scheduled
    if (this.reconnectTimerId !== null) {
      console.log(`Keepaliver: Reconnect already scheduled. Skipping.`);
      return;
    }

    console.log(`Keepaliver: Scheduling reconnect in ${RECONNECT_DELAY_MS}ms.`);
    this.reconnectTimerId = setTimeout(() => {
      console.log('Keepaliver: Attempting scheduled reconnect.');
      this.reconnectTimerId = null; // Clear timer ID before attempting to connect
      this.establishConnection(); // Attempt to establish a new connection
    }, RECONNECT_DELAY_MS);
  }


  async close() {
    console.log('Shutting down Keepaliver...');

    const runningTime = this.getRunningTime()
    console.log(`Keepaliver: Final total running time: ${runningTime}`);

    // Clear running time logging timer
    if (this.runningTimeTimerId !== null) {
      clearInterval(this.runningTimeTimerId);
      this.runningTimeTimerId = null;
      console.log('Keepaliver: Cleared running time logging timer.');
    }


    // Clear any pending reconnect timer
    if (this.reconnectTimerId !== null) {
      clearTimeout(this.reconnectTimerId);
      this.reconnectTimerId = null;
      console.log('Keepaliver: Cleared pending reconnect timer.');
    }

    // Close the keepalive client connection if it exists and is open
    if (this.keepaliveConnection && this.keepaliveConnection.readyState === WebSocket.OPEN) {
      this.keepaliveConnection.close(1000, 'Service shutting down');
    }
    this.keepaliveConnection = null; // Ensure reference is cleared

    // Close the WebSocket server
    if (this.wsServer) {
      // Clear intervals for all active server connections before closing the server
      this.wsServer.clients.forEach((client: WebSocket) => {
        // Check if the custom property exists
        if ((client as any).instanceIdInterval) {
          clearInterval((client as any).instanceIdInterval);
          console.log('Keepaliver: Cleared instance ID interval for server client during shutdown.');
        }
        // Optionally close the client connection gracefully
        if (client.readyState === WebSocket.OPEN) {
          client.close(1000, 'Server shutting down');
        }
      });
      await new Promise<void>((resolve, reject) => {
        this.wsServer!.close((err) => {
          if (err) {
            console.error('Keepaliver: Error closing WebSocket server:', err);
            reject(err);
          } else {
            console.log('Keepaliver: WebSocket server closed.');
            resolve();
          }
        });
      });
    } else {
      console.log('Keepaliver: WebSocket server instance not found.');
    }
  }

  private getTargetURL(): string | null {
    const targetUrl = process.env.KEEPALIVE_TARGET_URL;

    if (!targetUrl) {
      console.error('Keepaliver: KEEPALIVE_TARGET_URL environment variable is not set.');
      return null;
    }

    console.log(`Keepaliver: Using KEEPALIVE_TARGET_URL from environment: ${targetUrl}`);
    return targetUrl;
  }

  private replaceHTTPWithWS(urlStr: string): string {
    if (urlStr.startsWith('https')) {
      return 'wss' + urlStr.substring(5);
    }
    if (urlStr.startsWith('http')) {
      return 'ws' + urlStr.substring(4);
    }
    return urlStr;
  }
}
