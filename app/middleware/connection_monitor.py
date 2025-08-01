from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import time
import logging

logger = logging.getLogger(__name__)

class ConnectionMonitorMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.request_count = 0
        self.last_request_time = time.time()

    async def dispatch(self, request: Request, call_next):
        # 요청 시작 시간 기록
        start_time = time.time()
        
        # 요청 카운터 증가
        self.request_count += 1
        self.last_request_time = time.time()
        
        try:
            # 요청 처리
            response = await call_next(request)
            
            # 응답 시간 계산
            process_time = time.time() - start_time
            
            # 로깅
            logger.info(
                f"Request: {request.method} {request.url.path} - "
                f"Status: {response.status_code} - "
                f"Time: {process_time:.3f}s"
            )
            
            # 응답 헤더에 처리 시간 추가
            response.headers["X-Process-Time"] = str(process_time)
            response.headers["X-Request-Count"] = str(self.request_count)
            
            return response
            
        except Exception as e:
            # 오류 로깅
            logger.error(
                f"Request error: {request.method} {request.url.path} - "
                f"Error: {str(e)}"
            )
            
            # 오류 응답
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "message": "서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
                    "timestamp": time.time()
                }
            )

    def get_stats(self):
        """연결 통계 반환"""
        return {
            "request_count": self.request_count,
            "last_request_time": self.last_request_time,
            "uptime": time.time() - self.last_request_time
        } 