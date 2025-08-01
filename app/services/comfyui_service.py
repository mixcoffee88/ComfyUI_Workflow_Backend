import requests
import websocket
import threading
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from app.core.config import settings

class ComfyUIService:
    """ComfyUI API 서비스 클래스 (workflow_api_sample.py 참조)"""
    
    def __init__(self):
        self.api_url = settings.COMFYUI_API_URL
        self.ws_url = settings.COMFYUI_WS_URL
        self.today = datetime.today().strftime("%Y/%m/%d")

    async def execute_workflow(self, execution_id: int, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """워크플로우를 실행하고 prompt_id를 반환"""
        client_id = str(uuid.uuid4())
        print(f"workflow_data : {workflow_data}")
        
        # 딕셔너리를 JSON 문자열로 변환 후 UUID 교체
        workflow_json_str = json.dumps(workflow_data, ensure_ascii=False)
        workflow_json_str = workflow_json_str.replace("[uuid]", client_id)
        workflow_json_str = workflow_json_str.replace("[execution_id]", str(execution_id))
        print(f"workflow_json_str : {workflow_json_str}")
        workflow_data = json.loads(workflow_json_str)
        
        # ComfyUI API에 프롬프트 전송
        try:
            response = requests.post(self.api_url, json={
                "prompt": workflow_data,
                "client_id": client_id
            })
            response.raise_for_status()
            prompt_id = response.json()["prompt_id"]
            print(f"✅ 워크플로우 전송 완료 : {response.json()}")
            print(f"✅ 워크플로우 전송 완료 - prompt_id: {prompt_id}")
            
            # prompt_id만 포함한 결과 반환
            result = {
                "status": "pending",
                "prompt_id": prompt_id,
                "execution_id": execution_id,
                "message": "워크플로우 실행 요청하였습니다."
            }
            return result
        except Exception as e:
            print(f"❌ 워크플로우 전송 실패: {e}")
            raise Exception(f"ComfyUI API 호출 실패: {e}")

    async def _monitor_execution(self, client_id: str, prompt_id: str) -> Dict[str, Any]:
        """WebSocket을 통해 워크플로우 실행을 모니터링"""
        result = {}
        execution_finished_event = threading.Event()
        
        def on_message(ws, message):
            try:
                msg = json.loads(message)
            except Exception as e:
                print(f"❌ JSON 파싱 오류: {e}, 원본: {message}")
                return

            is_executed = msg.get("type") == "executed"
            is_prompt_id = msg.get("data", {}).get("prompt_id") == prompt_id
            
            # 실행 완료 메시지 확인
            if is_executed and is_prompt_id:
                print(f"🟢 워크플로우 실행 완료: {msg}")
                output = msg.get("data", {}).get("output", {})
                
                # 결과 처리
                if "images" in output:
                    # 이미지 결과
                    result["images"] = output["images"]
                    result["type"] = "image"
                elif "text" in output:
                    # 텍스트 결과
                    result["text"] = output["text"]
                    result["type"] = "text"
                else:
                    # 기타 결과
                    result["output"] = output
                    result["type"] = "other"
                
                result["status"] = "completed"
                result["prompt_id"] = prompt_id
                execution_finished_event.set()
                ws.close()
                print(f"🟢 결과 수신 완료")

        def on_error(ws, error):
            print(f"❌ WebSocket 오류: {error}")
            result["status"] = "failed"
            result["error"] = str(error)
            execution_finished_event.set()

        def on_close(ws, code, msg):
            print(f"WebSocket 종료: {code} / {msg}")

        # WebSocket 연결
        ws_url = f"{self.ws_url}?clientId={client_id}"
        ws = websocket.WebSocketApp(
            ws_url,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
        )

        # WebSocket을 별도 스레드에서 실행
        thread = threading.Thread(target=ws.run_forever)
        thread.start()

        # 결과 대기 (최대 300초)
        if not execution_finished_event.wait(timeout=300):
            ws.close()
            result["status"] = "timeout"
            result["error"] = "WebSocket에서 응답을 받지 못했습니다."
            print("❌ 타임아웃: WebSocket에서 응답을 받지 못했습니다.")

        thread.join(timeout=5)
        return result

    async def get_queue_status(self) -> Dict[str, Any]:
        """ComfyUI 큐 상태 조회"""
        try:
            queue_url = f"{self.api_url.replace('/prompt', '')}/queue"
            response = requests.get(queue_url)
            response.raise_for_status()
            
            queue_data = response.json()
            
            # 큐 상태 파싱
            running_count = len(queue_data.get("queue_running", []))
            pending_count = len(queue_data.get("queue_pending", []))
            
            result = {
                "running": running_count,
                "pending": pending_count,
                "total": running_count + pending_count,
                "queue_data": queue_data
            }
            
            print(f"✅ 큐 상태 조회 완료: 실행중={running_count}, 대기중={pending_count}")
            return result
            
        except Exception as e:
            print(f"❌ 큐 상태 조회 실패: {e}")
            # 오류 시 기본값 반환
            return {
                "running": 0,
                "pending": 0,
                "total": 0,
                "error": str(e)
            }

    def replace_placeholders(self, workflow_data: Dict[str, Any], replacements: Dict[str, str]) -> Dict[str, Any]:
        """워크플로우 데이터의 플레이스홀더를 실제 값으로 교체"""
        workflow_json_str = json.dumps(workflow_data, ensure_ascii=False)
        
        for placeholder, value in replacements.items():
            workflow_json_str = workflow_json_str.replace(placeholder, str(value))
        
        try:
            return json.loads(workflow_json_str)
        except json.JSONDecodeError as e:
            raise Exception(f"워크플로우 데이터 처리 실패: {str(e)}") 