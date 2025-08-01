#!/usr/bin/env python3
"""
PostgreSQL 스키마 문제 해결 스크립트
"""
import psycopg2
from dotenv import load_dotenv
import os

# .env 파일 로드
load_dotenv()

# 데이터베이스 연결 설정
DB_HOST = os.getenv("DB_HOST", "49.247.41.84")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "comfyui_db")
DB_USER = os.getenv("DB_USER", "comfyui")
DB_PASSWORD = os.getenv("DB_PASSWORD", "ibank1234!@#$")

print("🔍 PostgreSQL 스키마 상태 확인...")

try:
    # 데이터베이스 연결
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    
    cursor = conn.cursor()
    
    # 현재 스키마 확인
    cursor.execute("SELECT current_schema();")
    current_schema = cursor.fetchone()[0]
    print(f"📋 현재 스키마: {current_schema}")
    
    # search_path 확인
    cursor.execute("SHOW search_path;")
    search_path = cursor.fetchone()[0]
    print(f"🔍 현재 search_path: {search_path}")
    
    # 사용 가능한 스키마 목록
    cursor.execute("SELECT schema_name FROM information_schema.schemata;")
    schemas = cursor.fetchall()
    print(f"📚 사용 가능한 스키마: {[s[0] for s in schemas]}")
    
    # public 스키마 존재 확인
    cursor.execute("SELECT EXISTS(SELECT 1 FROM information_schema.schemata WHERE schema_name = 'public');")
    public_exists = cursor.fetchone()[0]
    print(f"✅ public 스키마 존재: {public_exists}")
    
    if not public_exists:
        print("🔧 public 스키마 생성 중...")
        cursor.execute("CREATE SCHEMA IF NOT EXISTS public;")
        print("✅ public 스키마 생성 완료")
    
    # search_path 설정
    print("🔧 search_path를 public으로 설정 중...")
    cursor.execute("SET search_path TO public;")
    
    # 권한 확인
    cursor.execute("""
        SELECT 
            has_schema_privilege(current_user, 'public', 'CREATE') as can_create,
            has_schema_privilege(current_user, 'public', 'USAGE') as can_use;
    """)
    permissions = cursor.fetchone()
    print(f"🔑 public 스키마 권한 - CREATE: {permissions[0]}, USAGE: {permissions[1]}")
    
    # 변경사항 저장
    conn.commit()
    print("✅ 스키마 설정 완료!")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ 오류 발생: {e}") 