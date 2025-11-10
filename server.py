# server.py
import uvicorn
from fastapi import FastAPI, File, UploadFile, Form
from pydantic import BaseModel
from typing import Optional
import base64
import io

from chat_agent import ChatAgent
from cu_agent import CUAgent
# from mock import MockComputer # 초기화용 (실제론 사용 안 함)

app = FastAPI()

# 전역 에이전트 인스턴스 생성 (서버 실행 시 1회 초기화)
# mock_computer = MockComputer() # CUAgent 초기화에 필요하지만 실제로는 요청 데이터 사용
cu_agent = CUAgent(
    # browser_computer=mock_computer,
    model_name='gemini-2.5-computer-use-preview-10-2025',
    verbose=True
)
chat_agent = ChatAgent(
    cu_agent=cu_agent,
    model_name='gemini-2.5-flash',
    verbose=True
)

@app.post("/chat")
async def chat_endpoint(
    query: str = Form(...),
    screenshot: UploadFile = File(...),
    activity: str = Form("unknown_activity")
):
    """
    앱으로부터 쿼리와 스크린샷을 받아 에이전트를 실행하고 결과를 반환합니다.
    """
    print(f"\n[Server] Request Received: Query='{query}', Screenshot={screenshot.filename}")

    # 1. 수신한 스크린샷 이미지 파일 읽기
    screenshot_bytes = await screenshot.read()

    # 2. ChatAgent에게 작업 위임 (Mock 데이터 대신 실제 수신 데이터 전달)
    response_data = chat_agent.execute_task(
        query=query,
        screenshot_bytes=screenshot_bytes,
        activity=activity
    )

    print(f"[Server] Response sending: {response_data}")
    return response_data

if __name__ == "__main__":
    # 서버 실행: 0.0.0.0:8000
    uvicorn.run(app, host="0.0.0.0", port=8000)