# server.py
import uvicorn
from fastapi import FastAPI, File, UploadFile, Form
from typing import Optional, Dict, Any

from chat_agent import ChatAgent
from cu_agent import CUAgent

app = FastAPI()

# 세션 ID를 기반으로 ChatAgent 인스턴스를 저장할 딕셔너리
# 프로덕션에서는 Redis나 DB 사용
# 서버 재시작 시 초기화되는 임시 메모리 저장소
SESSION_STORE: Dict[str, ChatAgent] = {}

def get_or_create_agent(session_id: str) -> ChatAgent:
    """세션 ID에 해당하는 에이전트를 반환하거나 새로 생성합니다."""
    if session_id not in SESSION_STORE:
        print(f"\n[Server] New session created: {session_id}")
        # 세션별로 독립적인 CUAgent와 ChatAgent를 생성
        cu_agent = CUAgent(
            model_name='gemini-2.5-computer-use-preview-10-2025',
            verbose=True
        )
        chat_agent = ChatAgent(
            cu_agent=cu_agent,
            model_name='gemini-2.5-flash',
            verbose=True
        )
        SESSION_STORE[session_id] = chat_agent
    
    return SESSION_STORE[session_id]

@app.post("/chat/query")
async def chat_query(
    query: str = Form(...),
    session_id: str = Form(...)
) -> Dict[str, Any]:
    """
    클라이언트의 모든 '초기 텍스트 쿼리'를 처리합니다.
    - 일상 채팅: 텍스트 응답 반환
    - 작업 요청: 스크린샷 요청 반환
    """
    print(f"\n[Server] /chat/query (Session: {session_id}): Query='{query}'")

    # 세션 ID에 맞는 에이전트를 가져오거나 생성
    chat_agent = get_or_create_agent(session_id)
    
    # ChatAgent에 쿼리 처리 요청
    response_data = chat_agent.process_query(query)

    print(f"[Server] Response: {response_data}")
    return response_data

@app.post("/chat/step")
async def chat_step(
    screenshot: UploadFile = File(...),
    activity: Optional[str] = Form(None),
    session_id: str = Form(...)
) -> Dict[str, Any]:
    """
    클라이언트가 서버의 요청에 따라 '스크린샷'을 전송하면,
    ChatAgent/CUAgent가 다음 액션 또는 최종 응답을 반환합니다.
    """
    print(f"\n[Server] /chat/step (Session: {session_id}): New screenshot received.")

    # 세션 ID로 해당 에이전트를 찾음
    chat_agent = SESSION_STORE.get(session_id)
    
    if not chat_agent:
        print(f"[Server] Error: No session found for ID {session_id}")
        return {
            "type": "ERROR", 
            "message": f"세션을 찾을 수 없습니다 (ID: {session_id}). /chat/query를 먼저 호출해주세요."
        }

    screenshot_bytes = await screenshot.read()

    # ChatAgent에 작업 계속/시작 요청
    response_data = chat_agent.process_step(screenshot_bytes, activity or "unknown_activity")

    print(f"[Server] Response: {response_data}")
    return response_data

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)