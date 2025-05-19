# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# cloud_pubsub.py (New or replacing existing pubsub.py)
import json
import time
import logging
from google.cloud import pubsub_v1
from google.cloud.pubsub_v1.publisher.futures import Future
from pubsub import BaseManager
from google.api_core import exceptions as google_exceptions
from models import Message
import uuid
from fastapi import Request
from typing import Callable, Any
import asyncio


class CloudPubSubManager(BaseManager):
    """
    Manages Google Cloud Pub/Sub interactions for sending commands
    and receiving screenshot results.
    """

    def __init__(
        self,
        project_id: str,
    ):
        super().__init__()
        self.project_id = project_id
        self.pending_messages = dict()
        self.publisher = pubsub_v1.PublisherClient()
        self.subscribers = dict()

    def _create_topic(self, topic_path: str) -> None:
        try:
            self.publisher.get_topic(request={"topic": topic_path})
            logging.warning(f"Topic '{topic_path}' already exists.")
        except google_exceptions.NotFound:
            topic = self.publisher.create_topic(request={"name": topic_path})
            logging.info(f"Created topic: {topic.name}")

    def _delete_topic(self, topic_path: str) -> None:
        try:
            self.publisher.delete_topic(request={"topic": topic_path})
            logging.info(f"Deleted topic: {topic_path}")
        except google_exceptions.NotFound:
            logging.warning(f"Topic not found: {topic_path}")

    def _create_subscription(
        self,
        subscriber: pubsub_v1.SubscriberClient,
        subscription_path: str,
        topic_path: str,
    ) -> None:
        try:
            subscriber.get_subscription(subscription=subscription_path)
            logging.info(f"Successfully subscribed to {subscription_path}")
        except google_exceptions.NotFound:
            logging.info(f"Subscription not found: {subscription_path}. Creating...")
            subscriber.create_subscription(name=subscription_path, topic=topic_path)
            logging.info(f"Created subscription: {subscription_path}")

    def _delete_subscription(
        self, subscriber: pubsub_v1.SubscriberClient, subscription_path: str
    ) -> None:
        try:
            subscriber.delete_subscription(subscription=subscription_path)
            logging.info(f"Successfully deleted subscription {subscription_path}")
        except google_exceptions.NotFound:
            logging.warning(f"Subscription not found: {subscription_path}")

    def command_topic_path(self, session_id: str) -> str:
        return f"projects/{self.project_id}/topics/commands-{session_id}"

    def screenshot_topic_path(self, session_id: str) -> str:
        return f"projects/{self.project_id}/topics/screenshots-{session_id}"

    def subscription_path(self, subscription_id: str) -> str:
        return f"projects/{self.project_id}/subscriptions/screenshots-{subscription_id}"

    def start_session(self, session_id: str) -> None:
        logging.info("Starting the Pub/Sub session")
        self._create_topic(topic_path=self.command_topic_path(session_id=session_id))

        screenshots_topic_path = self.screenshot_topic_path(session_id=session_id)
        self._create_topic(topic_path=screenshots_topic_path)
        self.start_subscriber(session_id=session_id, handler=self._screenshot_handler)

    def start_subscriber(
        self,
        session_id: str,
        handler: Callable[[Any, pubsub_v1.subscriber.message.Message], None],
    ) -> pubsub_v1.SubscriberClient:
        topic_path = self.screenshot_topic_path(session_id=session_id)
        logging.info("Starting a new subscriber")
        self.subscribers[session_id] = pubsub_v1.SubscriberClient()

        subscription_id = str(uuid.uuid4())
        subscription_path = self.subscription_path(subscription_id=subscription_id)

        logging.info(
            f"Creating subscripion path: {subscription_path} on topic path: {topic_path}"
        )
        self._create_subscription(
            subscriber=self.subscribers[session_id],
            subscription_path=subscription_path,
            topic_path=topic_path,
        )

        logging.info(f"Subscripion path: {subscription_path} created")
        self.subscribers[session_id].subscribe(subscription_path, callback=handler)
        return self.subscribers[session_id]

    def end_session(self, session_id: str) -> None:
        if session_id in self.subscribers:
            subcriber = self.subscribers[session_id]
            subcriber.close()
            logging.info("Ended subscription")
            del self.subscribers[session_id]
        self._delete_topic(topic_path=self.command_topic_path(session_id=session_id))
        self._delete_topic(topic_path=self.screenshot_topic_path(session_id=session_id))

    def shutdown(self) -> None:
        for subscriber in self.subscribers.values():
            subscriber.close()
        self.subscribers.clear()

    def _screenshot_handler(
        self, message: pubsub_v1.subscriber.message.Message
    ) -> None:
        logging.info("Screenshot event")
        try:
            data_str = message.data.decode("utf-8")
            parsed_data = json.loads(data_str)
            id = parsed_data["id"]

            if id in self.pending_messages:
                if "error" in parsed_data:
                    logging.error(f"Error: {parsed_data['error']}")
                    self.pending_messages[id].set_screenshot(None)
                else:
                    self.pending_messages[id].set_screenshot(
                        parsed_data["screenshot"], url=parsed_data["url"]
                    )
                del self.pending_messages[id]

            else:
                logging.warning(
                    f"Received screenshot for unknown or already processed ID: {id}"
                )
        except Exception as e:
            logging.error(f"Error processing screenshot message: {e}")
        finally:
            message.ack()

    async def publish_message(
        self, session_id: str, message: Message, timeout: int
    ) -> None:
        # This is to reconnect in case the subscriber is not listening on this instance
        if session_id not in self.subscribers:
            logging.info("No active subscribers on this host, starting a new one")
            self.start_session(session_id=session_id)

        topic_path = self.command_topic_path(session_id=session_id)

        data_bytes = message.json().encode("utf-8")
        attributes = {"message_id": message.id}

        try:
            self.pending_messages[message.id] = message

            logging.info(f"Publishing message {message.id} to {topic_path}")
            start_time = time.time()
            publish_future: Future = self.publisher.publish(
                topic_path, data=data_bytes, **attributes
            )
            publish_future.result(timeout=timeout)
            logging.info(
                f"Published message {message.id} to {topic_path} in {time.time() - start_time:.2f} seconds"
            )
        except Exception as e:
            logging.error(
                f"Failed to publish message {message.id} to {topic_path}: {e}"
            )
            self.pending_messages.pop(message.id, None)
            raise

    async def stream_screenshots(self, session_id: str, request: Request):
        messages = []

        def process_message(message: pubsub_v1.subscriber.message.Message) -> None:
            message.ack()
            data_str = message.data.decode("utf-8")
            screenshot = json.loads(data_str)["screenshot"]
            messages.append(f"event: screenshot\ndata: {screenshot}\n\n")

        subscriber = self.start_subscriber(
            session_id=session_id,
            handler=lambda message: process_message(message=message),
        )

        while True:
            if await request.is_disconnected():
                logging.info(
                    "Disconnecting streaming subscriber since the request is not disconnected"
                )
                subscriber.close()
                break
            while len(messages) > 0:
                message = messages.pop(0)
                yield message
            await asyncio.sleep(0.1)
