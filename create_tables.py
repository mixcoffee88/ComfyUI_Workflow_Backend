#!/usr/bin/env python3
"""
데이터베이스 테이블 생성 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from app.core.config import settings
from app.db.database import Base
from app.models import User, Workflow, Execution

def create_tables():
    """데이터베이스 테이블 생성"""
    print("🔧 데이터베이스 테이블 생성 중...")
    
    # 엔진 생성
    engine = create_engine(settings.DATABASE_URL)
    
    try:
        # 스키마 설정
        with engine.connect() as connection:
            connection.execute(text("SET search_path TO public"))
            connection.commit()
        
        # 테이블 생성
        Base.metadata.create_all(bind=engine)
        print("✅ 데이터베이스 테이블이 성공적으로 생성되었습니다!")
        
        # 생성된 테이블 확인
        with engine.connect() as connection:
            result = connection.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result]
            print(f"📋 생성된 테이블: {', '.join(tables)}")
            
    except Exception as e:
        print(f"❌ 테이블 생성 중 오류 발생: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = create_tables()
    if success:
        print("🎉 데이터베이스 설정이 완료되었습니다!")
    else:
        print("💥 데이터베이스 설정에 실패했습니다.")
        sys.exit(1) 