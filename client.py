# 클라이언트 App을 모방하기 위한 코드입니다
# server.py와 client.py를 각각 다른 콘솔에서 실행시키고, 
# client.py 콘솔에서 채팅을 하듯이 입력하면 됩니다.
# - "사용자 쿼리 입력" 이라고 나오는 경우 채팅 텍스트 입력
# - "스크린샷 파일명 입력"이라고 나오면 초기 스크린샷 파일명 입력 (screenshots 폴더에 해당 스크린샷 파일이 있어야 합니다.)
# - "액션 수행 후 스크린샷 파일명 입력" 라고 나오면 '서버 응답에 따라 화면 조작을 실행 한 뒤'의 스크린샷 파일명 입력

import requests
import os
import json

# --- 설정 ---
SERVER_URL = "http://localhost:8000"
QUERY_ENDPOINT = f"{SERVER_URL}/chat/query"
STEP_ENDPOINT = f"{SERVER_URL}/chat/step"
SCREENSHOT_DIR = "screenshots"
# ------------

def main():
    """
    서버와 통신하는 메인 클라이언트 루프입니다.
    1. /chat/query로 텍스트 쿼리를 전송합니다.
    2. 서버가 "REQUIRE_SCREENSHOT"을 반환하면 /chat/step으로 스크린샷을 전송합니다.
    3. 서버가 "ACTION"을 반환하면, (액션 수행 시뮬레이션 후) 다음 스크린샷을 /chat/step으로 전송합니다.
    4. 서버가 "RESPONSE" 또는 "ERROR"를 반환하면 루프를 종료하고 새 쿼리를 기다립니다.
    """
    
    # 세션을 사용하여 연결을 유지합니다 (선택 사항이지만 권장).
    session = requests.Session()

    while True:
        try:
            # --- 1. 초기 쿼리 전송 (/chat/query) ---
            query = input("\n사용자 쿼리 입력 (종료: 'q' 또는 'quit'): ")
            if query.lower() in ('q', 'quit', 'exit'):
                print("클라이언트를 종료합니다.")
                break
            if not query.strip():
                continue

            print(f"[클라이언트] -> /chat/query (쿼리: {query})")
            response = session.post(QUERY_ENDPOINT, data={'query': query})
            response.raise_for_status() # HTTP 오류 발생 시 예외 처리
            server_data = response.json()
            print(f"[서버] <- {server_data}")

            # --- 2. 다중 턴 작업 처리 (ACTION 또는 스크린샷 요청 시) ---
            while server_data.get("type") in ("REQUIRE_SCREENSHOT", "ACTION"):
                
                # 서버가 스크린샷을 요구하거나(REQUIRE_SCREENSHOT) 
                # 다음 액션을 위한 스크린샷이 필요한 경우(ACTION)
                
                if server_data.get("type") == "REQUIRE_SCREENSHOT":
                    print(f"[서버] {server_data.get('message')}")
                    screenshot_filename = input("스크린샷 파일명 입력 (예: screen1.png): ")
                
                elif server_data.get("type") == "ACTION":
                    action = server_data.get('action')
                    args = server_data.get('args')
                    print(f"[서버 액션] {action}({args})")
                    print("--- (클라이언트가 액션을 수행합니다...) ---")
                    screenshot_filename = input("액션 수행 후 스크린샷 파일명 입력: ")

                # --- /chat/step으로 스크린샷 전송 ---
                filepath = os.path.join(SCREENSHOT_DIR, screenshot_filename.strip())
                
                if not os.path.exists(filepath):
                    print(f"[오류] {filepath} 에서 파일을 찾을 수 없습니다. 작업을 중단합니다.")
                    # 작업을 중단하고 새 쿼리 대기
                    break 

                try:
                    with open(filepath, 'rb') as f:
                        files = {
                            'screenshot': (screenshot_filename, f, 'image/png')
                        }
                        data = {
                            # 실제 앱에서는 현재 Activity 이름을 전송합니다.
                            'activity': 'simulated.activity.name' 
                        }
                        
                        print(f"[클라이언트] -> /chat/step (파일: {screenshot_filename})")
                        response = session.post(STEP_ENDPOINT, files=files, data=data)
                        response.raise_for_status()
                        server_data = response.json()
                        print(f"[서버] <- {server_data}")

                except IOError as e:
                    print(f"[오류] 파일 읽기 실패: {e}")
                    break # 내부 루프 중단

            # --- 3. 최종 응답 또는 오류 처리 ---
            if server_data.get("type") == "RESPONSE":
                print(f"[서버 최종 응답] {server_data.get('message')}")
            elif server_data.get("type") == "ERROR":
                print(f"[서버 오류] {server_data.get('message')}")

        except requests.exceptions.ConnectionError:
            print("\n[오류] 서버에 연결할 수 없습니다. (server.py가 실행 중인지 확인하세요)")
            break # 서버가 다운되면 클라이언트 종료
        except requests.exceptions.RequestException as e:
            print(f"\n[HTTP 오류] {e}")
        except Exception as e:
            print(f"\n[알 수 없는 오류] {e}")

if __name__ == "__main__":
    # 스크린샷 폴더가 없으면 생성
    if not os.path.exists(SCREENSHOT_DIR):
        os.makedirs(SCREENSHOT_DIR)
        print(f"'{SCREENSHOT_DIR}' 폴더를 생성했습니다. 스크린샷 이미지 파일을 이 폴더에 넣어주세요.")
        print(f"테스트용 Mock 스크린샷이 필요하면 'mock.py'의 Base64 데이터를 이미지 파일로 변환하여 사용하세요.")
    
    main()