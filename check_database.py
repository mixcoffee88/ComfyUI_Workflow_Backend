#!/usr/bin/env python3
"""
데이터베이스 연결 및 테이블 구조 확인 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from app.core.config import settings

def check_database():
    """데이터베이스 연결 및 테이블 구조 확인"""
    print("🔍 데이터베이스 연결 및 테이블 구조 확인 중...")
    
    # 엔진 생성
    engine = create_engine(settings.DATABASE_URL)
    
    try:
        with engine.connect() as connection:
            # 스키마 설정
            connection.execute(text("SET search_path TO public"))
            
            # 테이블 목록 확인
            result = connection.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            
            tables = [row[0] for row in result]
            print(f"📋 현재 데이터베이스의 테이블 목록: {', '.join(tables)}")
            
            # assets 테이블 존재 확인
            if 'assets' in tables:
                print("✅ Assets 테이블이 존재합니다!")
                
                # assets 테이블 구조 확인
                result = connection.execute(text("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_schema = 'public' AND table_name = 'assets'
                    ORDER BY ordinal_position
                """))
                
                print("📋 Assets 테이블 구조:")
                for row in result:
                    print(f"  - {row[0]}: {row[1]} (nullable: {row[2]}, default: {row[3]})")
                
                # 기존 assets 데이터 확인
                result = connection.execute(text("""
                    SELECT COUNT(*) as count FROM assets
                """))
                count = result.fetchone()[0]
                print(f"📊 Assets 테이블에 {count}개의 레코드가 있습니다.")
                
                if count > 0:
                    # 최근 assets 확인
                    result = connection.execute(text("""
                        SELECT id, execution_id, image_url, created_at 
                        FROM assets 
                        ORDER BY created_at DESC 
                        LIMIT 5
                    """))
                    
                    print("📋 최근 Assets 레코드:")
                    for row in result:
                        print(f"  - ID: {row[0]}, Execution ID: {row[1]}, URL: {row[2]}, Created: {row[3]}")
                
            else:
                print("❌ Assets 테이블이 존재하지 않습니다!")
                print("💡 Assets 테이블을 생성하려면 마이그레이션을 실행하세요.")
            
            # executions 테이블 확인
            if 'executions' in tables:
                result = connection.execute(text("""
                    SELECT COUNT(*) as count FROM executions
                """))
                count = result.fetchone()[0]
                print(f"📊 Executions 테이블에 {count}개의 레코드가 있습니다.")
                
                # execution_id 50 확인
                result = connection.execute(text("""
                    SELECT id, workflow_id, user_id, status, created_at 
                    FROM executions 
                    WHERE id = 50
                """))
                
                execution_50 = result.fetchone()
                if execution_50:
                    print(f"✅ Execution ID 50이 존재합니다: {execution_50}")
                else:
                    print("❌ Execution ID 50이 존재하지 않습니다.")
            
    except Exception as e:
        print(f"❌ 데이터베이스 확인 중 오류 발생: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = check_database()
    if success:
        print("🎉 데이터베이스 확인이 완료되었습니다!")
    else:
        print("💥 데이터베이스 확인에 실패했습니다.")
        sys.exit(1) 