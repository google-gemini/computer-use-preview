import asyncio
import json
import uuid
from unittest.mock import MagicMock, AsyncMock, call, ANY

import pytest
from google.api_core import exceptions as google_exceptions

from models import Message
from cloud_pubsub import CloudPubSubManager


@pytest.fixture
def mock_publisher(mocker):
    """Mocks the PubSub PublisherClient."""
    mock_pub = MagicMock()

    mock_future = MagicMock()
    mock_future.result.return_value = "mock-message-id"
    mock_pub.publish.return_value = mock_future

    mock_pub.get_topic.side_effect = google_exceptions.NotFound("mocked")
    mock_pub.create_topic.return_value = MagicMock()
    mock_pub.delete_topic.return_value = None

    mocker.patch("google.cloud.pubsub_v1.PublisherClient", return_value=mock_pub)
    return mock_pub


@pytest.fixture
def mock_subscriber(mocker):
    """Mocks the PubSub SubscriberClient."""

    mock_instance = MagicMock()

    mocker.patch(
        "google.cloud.pubsub_v1.SubscriberClient",
        return_value=mock_instance,
        autospec=True,
    )

    mock_instance.get_subscription.side_effect = google_exceptions.NotFound("mocked")
    mock_instance.subscribe.return_value = MagicMock(spec=["cancel"]) 
    mock_instance.close.return_value = None
    mock_instance.create_subscription.return_value = MagicMock()
    mock_instance.delete_subscription.return_value = None

    return mock_instance


@pytest.fixture
def manager(mock_publisher):
    """Provides a CloudPubSubManager instance with mocked clients."""
    mgr = CloudPubSubManager(project_id="test-project")
    mgr.publisher = mock_publisher
    yield mgr
    mgr.shut_down()


@pytest.fixture
def mock_pubsub_message():
    """Factory for creating a mock Pub/Sub Message"""

    def _create_mock_message(id, screenshot, url):
        mock_msg = MagicMock()
        mock_msg.ack = MagicMock()
        payload = {"id": id, "screenshot": screenshot, "url": url}
        mock_msg.data = json.dumps(payload).encode("utf-8")
        return mock_msg

    return _create_mock_message


@pytest.mark.asyncio
async def test_init(manager, mock_publisher):
    assert manager.project_id == "test-project"
    assert manager.publisher == mock_publisher
    assert manager.subscribers == {}
    assert manager.pending_messages == {}


@pytest.mark.asyncio
async def test_start_session_new(manager, mock_publisher, mock_subscriber):
    """Tests that start_session creates topics and subscription when they dont exist."""
    session_id = "session-123"

    manager.start_session(session_id)

    cmd_topic_path = manager.command_topic_path(session_id)
    ss_topic_path = manager.screenshot_topic_path(session_id)

    mock_publisher.get_topic.assert_any_call(request={"topic": cmd_topic_path})
    mock_publisher.create_topic.assert_any_call(request={"name": cmd_topic_path})

    mock_publisher.get_topic.assert_any_call(request={"topic": ss_topic_path})
    mock_publisher.create_topic.assert_any_call(request={"name": ss_topic_path})

    assert session_id in manager.subscribers
    mock_sub_instance = manager.subscribers[session_id]

    mock_sub_instance.get_subscription.assert_called_once()
    mock_sub_instance.create_subscription.assert_called_once_with(
        name=ANY, topic=ss_topic_path
    )

    mock_sub_instance.subscribe.assert_called_once_with(
        ANY, callback=manager._screenshot_handler
    )


@pytest.mark.asyncio
async def test_start_session_existing(mocker, manager, mock_publisher, mock_subscriber):
    """Tests that start_session does NOT re-create topics/subs if they exist."""
    session_id = "session-abc"

    mock_publisher.get_topic.side_effect = None
    mock_publisher.get_topic.return_value = MagicMock(name="mock_topic")

    mock_subscriber.get_subscription.side_effect = None
    mock_subscriber.get_subscription.return_value = MagicMock(name="mock_sub")

    manager.start_session(session_id)

    mock_publisher.create_topic.assert_not_called()

    assert session_id in manager.subscribers
    mock_sub_instance = manager.subscribers[session_id]

    mock_sub_instance.create_subscription.assert_not_called()
    mock_sub_instance.subscribe.assert_called_once()


@pytest.mark.asyncio
async def test_end_session(manager, mock_publisher, mock_subscriber):
    session_id = "session-to-end"
    manager.start_session(session_id)

    assert session_id in manager.subscribers
    mock_sub_instance = manager.subscribers[session_id]

    manager.end_session(session_id)

    mock_sub_instance.close.assert_called_once()
    assert session_id not in manager.subscribers

    mock_publisher.delete_topic.assert_has_calls(
        [
            call(request={"topic": manager.command_topic_path(session_id)}),
            call(request={"topic": manager.screenshot_topic_path(session_id)}),
        ],
        any_order=True,
    )


@pytest.mark.asyncio
async def test_publish_message_success(manager, mock_publisher, mock_subscriber):
    session_id = "session-pub"
    manager.start_session(session_id)

    msg = Message(type="CMD", data={"do": "this"})
    assert msg.id not in manager.pending_messages

    await manager.publish_message(session_id, msg)

    assert msg.id in manager.pending_messages

    expected_topic = manager.command_topic_path(session_id)
    expected_data = msg.json().encode("utf-8")
    expected_attrs = {"message_id": msg.id}

    mock_publisher.publish.assert_called_once_with(
        expected_topic, data=expected_data, **expected_attrs
    )
    mock_publisher.publish.return_value.result.assert_called_once_with(timeout=10)


@pytest.mark.asyncio
async def test_publish_starts_subscriber_if_needed(
    manager, mock_publisher, mock_subscriber
):
    """Tests that a publish on a node that isn't currently subscribed for the session
    will start a subscription on that node.
    """
    session_id = "session-pub-reconect"

    assert session_id not in manager.subscribers

    msg = Message(type="CMD", data={"do": "this"})

    await manager.publish_message(session_id, msg)

    assert session_id in manager.subscribers

    mock_subscriber.create_subscription.assert_called_once()
    mock_subscriber.subscribe.assert_called_once()

    mock_publisher.publish.assert_called_once()


@pytest.mark.asyncio
async def test_publish_message_failure(manager, mock_publisher, mock_subscriber):
    session_id = "session-fail"
    manager.start_session(session_id) 
    
    msg = Message(type="CMD", data={"do": "this"})
    
    pub_error = Exception("Pubsub unavailable")
    mock_publisher.publish.side_effect = pub_error
    
    with pytest.raises(Exception, match="Pubsub unavailable"):
        await manager.publish_message(session_id, msg)
        
    assert msg.id not in manager.pending_messages


@pytest.mark.asyncio
async def test_screenshot_handler_resolves_pending_message(
    manager, mock_pubsub_message
):
    """Tests that the handler finds a pending message and sets the result."""
    msg = Message(type="CMD", data={"do": "this"})
    manager.pending_messages[msg.id] = msg

    mock_ss = "base64string=="
    mock_url = "http://example.com"

    pubsub_msg = mock_pubsub_message(msg.id, mock_ss, mock_url)
    assert not msg._event.is_set()

    manager._screenshot_handler(pubsub_msg)

    pubsub_msg.ack.assert_called_once()
    assert msg.id not in manager.pending_messages

    screenshot = await msg.get_screenshot(timeout=0.1)
    url = await msg.get_url(timeout=0.1)

    assert screenshot == mock_ss
    assert url == mock_url
    assert msg._event.is_set()


@pytest.mark.asyncio
async def test_screenshot_handler_unknown_id(manager, mock_pubsub_message):
    unknown_id = "unknown-message-id"
    assert unknown_id not in manager.pending_messages

    pubsub_msg = mock_pubsub_message(unknown_id, "data", "url")

    manager._screenshot_handler(pubsub_msg)

    pubsub_msg.ack.assert_called_once()
    assert not manager.pending_messages


@pytest.mark.asyncio
async def test_screenshot_handler_bad_json(manager):
    msg = Message(type="CMD", data={"do": "this"})
    manager.pending_messages[msg.id] = msg

    mock_msg = MagicMock()
    mock_msg.ack = MagicMock()
    mock_msg.data = b"this is not json"

    manager._screenshot_handler(mock_msg)

    mock_msg.ack.assert_called_once()
    assert msg.id in manager.pending_messages
    assert not msg._event.is_set()


@pytest.mark.asyncio
async def test_stream_screenshots(manager, mock_subscriber):
    """
    Tests the async generator for streaming.
    Mocks the request and simulates messages arriving via the callback.
    """
    session_id = "stream-session"
    anext_task = None

    try:
        mock_request = AsyncMock()
        mock_request.is_disconnected.return_value = False

        loop = asyncio.get_running_loop()
        callback_captured = loop.create_future()
        handler_callback = None

        def capture_callback_wrapper(sub_path, callback):
            nonlocal handler_callback
            handler_callback = callback

            if not callback_captured.done():
                callback_captured.set_result(True)
            return MagicMock(spec=["cancel"]) 

        mock_subscriber.subscribe.side_effect = capture_callback_wrapper

        stream_generator = manager.stream_screenshots(session_id, mock_request)

        anext_task = asyncio.create_task(anext(stream_generator))

        await asyncio.wait_for(callback_captured, timeout=1.0)

        mock_subscriber.subscribe.assert_called_once()
        assert handler_callback is not None

        mock_msg = MagicMock()
        mock_msg.ack = MagicMock()
        ss_data = "iVBORw0KGgoAAA=="
        mock_msg.data = json.dumps({"screenshot": ss_data}).encode("utf-8")

        handler_callback(mock_msg)
        mock_msg.ack.assert_called_once()

        yielded_message = await asyncio.wait_for(anext_task, timeout=1.0)

        expected_sse = f"event: screenshot\ndata: {ss_data}\n\n"
        assert yielded_message == expected_sse

        mock_request.is_disconnected.return_value = True

        with pytest.raises(StopAsyncIteration):
            await asyncio.wait_for(anext(stream_generator), timeout=1.0)

        mock_subscriber.close.assert_called_once()

    finally:
        if anext_task and not anext_task.done():
            anext_task.cancel()
            try:
                await anext_task
            except asyncio.CancelledError:
                pass