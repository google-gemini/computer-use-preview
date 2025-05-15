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
import { CommandMessage, HttpChannel, PubSubChannel } from '../signalling';
import { strict as assert } from 'node:assert';
import Sinon, { spy, stub, createStubInstance } from 'sinon'
import http from 'node:http'
import { Subscription, Topic } from '@google-cloud/pubsub';

describe("HttpChannel", function () {
    let channel: HttpChannel

    beforeEach("init", () => {
        channel = new HttpChannel(9999)
    });

    this.afterEach(async () => {
        await channel.disconnect()
    })

    describe('#disconnect()', async function () {
        it('closes the server', async () => {
            const closeStub = stub()
            channel.server = createStubInstance(http.Server, {
                close: closeStub()
            });
            channel.disconnect()
            Sinon.assert.calledOnce(closeStub);
        });
    });

    describe('#subscribe()', async function () {

        it("returns the concatenated body", async () => {
            let message: null | CommandMessage = null
            const handler = async (m: CommandMessage) => {
                message = m
                m.publishScreenshot("screen", "session", "url")
            };
            await channel.subscribe(handler);
            const response = await fetch('http://localhost:9999', {
                method: 'POST',
                body: '{"command":{"click": "x"}}'
            });


            assert.ok(typeof message!.command === "object")
            assert.equal("x", message!.command["click"])
        })
    });
});

describe("PubSubChannel", function () {
    describe('#disconnect()', async function () {
        it('closes the server', async () => {
            const channel = new PubSubChannel({
                projectId: "test",
                commandsTopic: "test",
                screenshotsTopic: "test",
                subscriptionName: "test"
            })
            const closeStub = stub()
            channel.subscription = createStubInstance(Subscription, {
                close: closeStub()
            });
            channel.disconnect()
            Sinon.assert.calledOnce(closeStub);
        });
    });

    describe('#subscribe()', async function () {

        let channel: PubSubChannel

        beforeEach("init", () => {
            channel = new PubSubChannel({
                projectId: "test",
                commandsTopic: "cmd-topic",
                screenshotsTopic: "screen-topic",
                subscriptionName: "sub"
            })
        });

        this.afterEach(async () => {
            await channel.disconnect()
        })

        it("returns the command", async () => {
            let message: null | CommandMessage = null
            const handler = async (m: CommandMessage) => {
                message = m
            };

            const sub = new Subscription(channel.pubsub, "sub")
            const msg = {
                ack: spy(),
                data: Buffer.from(JSON.stringify({ command: { "click": "x" } }))
            }
            // Stub the 'on' method on the subscription instance
            const eventHandler = stub(sub, "on").withArgs("message", Sinon.match.func);
            const topic = createStubInstance(Topic, {});
            stub(channel.pubsub, "topic").withArgs("cmd-topic").returns(topic);

            // Use a Promise to control when the subscription creation callback is invoked.
            let subscriptionCreatedPromiseResolve: (value?: unknown) => void;
            const subscriptionCreatedPromise = new Promise(resolve => {
                subscriptionCreatedPromiseResolve = resolve;
            });

            (topic.createSubscription as Sinon.SinonStub)
                .withArgs("sub", Sinon.match.any) // Match name and any options/callback
                .callsFake(async (name: string, optionsOrCallback?: any, callback?: any) => {
                    let actualCallback: Function;
                    // Determine which argument is the callback
                    if (typeof optionsOrCallback === 'function') {
                        actualCallback = optionsOrCallback;
                    } else if (typeof callback === 'function') {
                        actualCallback = callback;
                    } else {
                        throw new Error('Callback not found in createSubscription arguments');
                    }

                    // Simulate the asynchronous nature, then call the actual callback
                    await Promise.resolve(); // Ensure callback is invoked in a microtask
                    actualCallback(null, sub); // Call the PubSub library's callback
                    subscriptionCreatedPromiseResolve(); // Signal that the subscription is "ready"
                    return [sub]; // Return value for the promise if used
                });

            channel.subscribe(handler);

            // Wait for the subscription to be "created" and its 'on' handler to be set up.
            await subscriptionCreatedPromise;

            // Now that the 'on' handler is theoretically set up,
            // we can call the argument of the stubbed 'on' method.
            eventHandler.callArgWith(1, msg);


            assert.ok(typeof message!.command === "object")
            assert.equal("x", message!.command["click"])
        })
    });
});
