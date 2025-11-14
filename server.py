# server.py
import uvicorn
from fastapi import FastAPI, File, UploadFile, Form
from typing import Optional, Dict, Any

from chat_agent import ChatAgent
from cu_agent import CUAgent

app = FastAPI()

# 전역 에이전트 인스턴스 생성
cu_agent = CUAgent(
    model_name='gemini-2.5-computer-use-preview-10-2025',
    verbose=True
)
chat_agent = ChatAgent(
    cu_agent=cu_agent,
    model_name='gemini-2.5-flash',
    verbose=True
)

@app.post("/chat/query")
async def chat_query(
    query: str = Form(...)
) -> Dict[str, Any]:
    """
    클라이언트의 모든 '초기 텍스트 쿼리'를 처리합니다.
    - 일상 채팅: 텍스트 응답 반환
    - 작업 요청: 스크린샷 요청 반환
    """
    print(f"\n[Server] /chat/query: Query='{query}'")
    
    # ChatAgent에 쿼리 처리 요청
    response_data = chat_agent.process_query(query)

    print(f"[Server] Response: {response_data}")
    return response_data

@app.post("/chat/step")
async def chat_step(
    screenshot: UploadFile = File(...),
    activity: Optional[str] = Form(None)
) -> Dict[str, Any]:
    """
    클라이언트가 서버의 요청에 따라 '스크린샷'을 전송하면,
    ChatAgent/CUAgent가 다음 액션 또는 최종 응답을 반환합니다.
    """
    print(f"\n[Server] /chat/step: New screenshot received.")

    screenshot_bytes = await screenshot.read()

    # ChatAgent에 작업 계속/시작 요청
    response_data = chat_agent.process_step(screenshot_bytes, activity or "unknown_activity")

    print(f"[Server] Response: {response_data}")
    return response_data

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)