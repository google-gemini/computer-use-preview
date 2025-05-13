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
"""Computer user API server.

Provides the REST API for integrating with the Computer Use API.
"""
import asyncio
from fastapi.security import APIKeyHeader
from fastapi import FastAPI, HTTPException, status, Path, Security, Depends, Request
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from typing import Annotated
from contextlib import asynccontextmanager
from pubsub import DevManager
from cloud_pubsub import CloudPubSubManager
from sessions import SessionManager
from models import CreateSessionRequest, CreateSessionResponse
from models import CreateCommandRequest, CreateCommandResponse
from models import DeleteSessionResponse
from models import Message
from models import SignalingStrategy
import uuid
import os
import uvicorn
import secrets
from config import Config


config = Config()
session_manager = SessionManager(config=config)
if config.use_pubsub:
    print(f"using PubSub signalling in {config.project_id}")
    pubsub_manager = CloudPubSubManager(project_id=config.project_id)
    signaling_strategy = SignalingStrategy.PUBSUB
else:
    pubsub_manager = DevManager()
    signaling_strategy = SignalingStrategy.HTTP


@asynccontextmanager
async def lifespan(app: FastAPI):
    await pubsub_manager.start()
    yield
    await pubsub_manager.shut_down()


description = """
A REST API for operating a containerized computer running as Cloud Run Job. 🚀

[working demo](https://apiserver-997665560667.us-east1.run.app/)
"""

API_KEY_HEADER_NAME = "X-API-Key"
# TODO: this is insecure by default
api_key_header = APIKeyHeader(name=API_KEY_HEADER_NAME, auto_error=False)


async def check_api_key(api_key: str | None = Security(api_key_header)):
    if config.api_key is None:
        return

    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid API Key, Missing {API_KEY_HEADER_NAME} header",
        )

    if secrets.compare_digest(api_key, config.api_key):
        return

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=f"Invalid API Key, Check the {API_KEY_HEADER_NAME} header",
    )


app = FastAPI(
    title="Cloud Run Computer Use Tool",
    description=description,
    version="0.0.1",
    lifespan=lifespan,
    dependencies=[Depends(check_api_key)],
)


@app.post("/sessions")
async def create_session(session: CreateSessionRequest) -> CreateSessionResponse:
    session_id = str(uuid.uuid4())
    try:
        pubsub_manager.start_session(session_id=session_id)
        await session_manager.start_worker(
            session_id=session_id,
            session_type=session.type,
            signaling_strategy=signaling_strategy,
            screen_resolution=session.screen_resolution,
            job_timeout_seconds=session.timeout_seconds,
            idle_timeout_seconds=session.idle_timeout_seconds,
        )
        return CreateSessionResponse(id=session_id)
    except Exception as e:
        print(f'Error in session creation: {e} {repr(e)}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e))


@app.get("/sessions/{session_id}/screenshots")
def get_screenshot(
    session_id: Annotated[str, Path(description="The UUID of the session.")],
    request: Request,
):
    return StreamingResponse(
        pubsub_manager.stream_screenshots(session_id, request),
        media_type="text/event-stream",
    )


@app.post("/sessions/{session_id}/commands")
async def create_command(
    session_id: Annotated[str, Path(description="The UUID of the session.")],
    command: CreateCommandRequest,
) -> CreateCommandResponse:
    command_data_dict = command.model_dump()
    print(f"command data: {command_data_dict}")
    message = Message(type="command", data=command_data_dict)
    await pubsub_manager.publish_message(session_id=session_id, message=message)
    try:
        screenshot = await message.get_screenshot(timeout=config.cmd_timeout)
        url = await message.get_url()
    except asyncio.TimeoutError as err:
        print(err)
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail="command timed out, the worker may not be responsive",
        ) from err

    if screenshot is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="command failed"
        )

    return CreateCommandResponse(id=message.id, screenshot=screenshot, url=url)


@app.delete("/sessions/{session_id}")
async def delete_session(
    session_id: Annotated[str, Path(description="The UUID of the session.")],
) -> DeleteSessionResponse:
    await pubsub_manager.publish_message(
        session_id=session_id, message=Message(type="command", data="shut_down")
    )
    pubsub_manager.end_session(session_id=session_id)
    return DeleteSessionResponse(id=session_id)


# Static HTML5 to test the API.
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("app:app", host='0.0.0.0', port=port, log_level="info")