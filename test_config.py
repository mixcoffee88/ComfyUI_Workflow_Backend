#!/usr/bin/env python3
"""
데이터베이스 연결 설정 테스트 스크립트
"""
import os
import sys
from pathlib import Path

# 프로젝트 루트 경로 설정
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 환경변수 로드 테스트
print("🔍 환경변수 확인:")
print(f"DATABASE_URL: {os.getenv('DATABASE_URL', 'NOT_SET')}")
print(f"DB_HOST: {os.getenv('DB_HOST', 'NOT_SET')}")
print(f"DB_USER: {os.getenv('DB_USER', 'NOT_SET')}")
print(f"DB_PASSWORD: {os.getenv('DB_PASSWORD', 'NOT_SET')}")
print(f"DB_NAME: {os.getenv('DB_NAME', 'NOT_SET')}")
print(f"DB_PORT: {os.getenv('DB_PORT', 'NOT_SET')}")

# .env 파일 로드 테스트
from dotenv import load_dotenv
load_dotenv()

print("\n🔍 .env 파일 로드 후:")
print(f"DATABASE_URL: {os.getenv('DATABASE_URL', 'NOT_SET')}")
print(f"DB_HOST: {os.getenv('DB_HOST', 'NOT_SET')}")
print(f"DB_USER: {os.getenv('DB_USER', 'NOT_SET')}")
print(f"DB_PASSWORD: {os.getenv('DB_PASSWORD', 'NOT_SET')}")
print(f"DB_NAME: {os.getenv('DB_NAME', 'NOT_SET')}")
print(f"DB_PORT: {os.getenv('DB_PORT', 'NOT_SET')}")

# Settings 클래스 테스트
try:
    from app.core.config import settings
    print("\n🔍 Settings 클래스:")
    print(f"db_host: {settings.db_host}")
    print(f"db_user: {settings.db_user}")
    print(f"db_password: {settings.db_password}")
    print(f"db_name: {settings.db_name}")
    print(f"db_port: {settings.db_port}")
    print(f"DATABASE_URL: {settings.DATABASE_URL}")
except Exception as e:
    print(f"❌ Settings 클래스 오류: {e}")

# 데이터베이스 연결 테스트
try:
    import psycopg2
    print("\n🔍 PostgreSQL 연결 테스트:")
    
    # Settings에서 가져온 값으로 연결 테스트
    conn = psycopg2.connect(
        host=settings.db_host,
        port=settings.db_port,
        database=settings.db_name,
        user=settings.db_user,
        password=settings.db_password
    )
    print("✅ PostgreSQL 연결 성공!")
    conn.close()
    
except Exception as e:
    print(f"❌ PostgreSQL 연결 실패: {e}")
    
    # 수동으로 연결 시도
    try:
        conn = psycopg2.connect(
            host="49.247.41.84",
            port="5432",
            database="comfyui_db",
            user="comfyui",
            password="password"
        )
        print("✅ 수동 연결 성공!")
        conn.close()
    except Exception as e2:
        print(f"❌ 수동 연결도 실패: {e2}") 