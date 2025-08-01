from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os
from urllib.parse import quote_plus
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

class Settings(BaseSettings):
    # 데이터베이스 설정
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: str = "5432"
    DATABASE_NAME: str = "comfyui_db"
    DATABASE_USER: str = "postgres"
    DATABASE_PASSWORD: str = "1234"
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.DATABASE_USER}:{quote_plus(self.DATABASE_PASSWORD)}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
    
    # JWT 설정
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # ComfyUI 설정
    COMFYUI_API_URL: str = "http://localhost:8188"
    COMFYUI_WS_URL: str = "ws://localhost:8188/ws"
    
    # 디버그 설정
    DEBUG: str = "false"
    
    # S3 설정
    S3_URL: str = ""
    
    # 세션 및 연결 설정
    SESSION_TIMEOUT_MINUTES: int = 60
    CONNECTION_POOL_SIZE: int = 10
    CONNECTION_POOL_RECYCLE: int = 3600
    CONNECTION_POOL_TIMEOUT: int = 30
    
    # CORS 설정
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:8080"]
    
    # 로깅 설정
    LOG_LEVEL: str = "INFO"
    
    model_config = SettingsConfigDict(
        case_sensitive=True, 
        env_file_encoding='utf-8'
    )

settings = Settings()
print(f"settings.DATABASE_URL: {settings.DATABASE_URL}")