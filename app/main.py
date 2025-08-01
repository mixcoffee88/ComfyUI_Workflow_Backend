from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from datetime import datetime
import os

from app.core.config import settings
from app.api import auth, workflows, executions, admin, callback
from app.db.database import init_db
from app.middleware.connection_monitor import ConnectionMonitorMiddleware

load_dotenv()

app = FastAPI(
    title="ComfyUI 워크플로우 관리 플랫폼",
    description="ComfyUI 워크플로우를 관리하고 실행할 수 있는 플랫폼",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 연결 모니터링 미들웨어 추가
app.add_middleware(ConnectionMonitorMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept", "Origin", "X-Requested-With"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["인증"])
app.include_router(workflows.router, prefix="/api/workflows", tags=["워크플로우"])
app.include_router(executions.router, prefix="/api/executions", tags=["실행"])
app.include_router(admin.router, prefix="/api/admin", tags=["관리자"])
app.include_router(callback.router, prefix="/api/callback", tags=["콜백"])

@app.on_event("startup")
async def startup_event():
    await init_db()
    print("ComfyUI 워크플로우 관리 플랫폼이 시작되었습니다.")

@app.get("/")
async def root():
    return {"message": "ComfyUI 워크플로우 관리 플랫폼에 오신 것을 환영합니다!"}

@app.get("/health")
async def health_check():
    """서버 상태 확인 엔드포인트"""
    try:
        # 데이터베이스 연결 확인
        from app.db.database import SessionLocal
        db = SessionLocal()
        try:
            db.execute("SELECT 1")
            db_status = "connected"
        except Exception as e:
            db_status = f"error: {str(e)}"
        finally:
            db.close()
        
        # 연결 통계 가져오기
        connection_stats = None
        for middleware in app.user_middleware:
            if hasattr(middleware.cls, 'get_stats'):
                connection_stats = middleware.cls(app).get_stats()
                break
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": db_status,
            "connection_stats": connection_stats
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/stats")
async def get_stats():
    """서버 통계 엔드포인트"""
    try:
        # 연결 통계 가져오기
        connection_stats = None
        for middleware in app.user_middleware:
            if hasattr(middleware.cls, 'get_stats'):
                connection_stats = middleware.cls(app).get_stats()
                break
        
        return {
            "connection_stats": connection_stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9001)
