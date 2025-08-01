#!/usr/bin/env python3
"""
Assets 테이블 마이그레이션 실행 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from app.core.config import settings

def run_migration():
    """Assets 테이블 마이그레이션 실행"""
    print("🔧 Assets 테이블 마이그레이션 실행 중...")
    
    # 엔진 생성
    engine = create_engine(settings.DATABASE_URL)
    
    try:
        # 마이그레이션 SQL 파일 읽기
        migration_file = os.path.join(os.path.dirname(__file__), "migrations", "fix_assets_table.sql")
        
        if not os.path.exists(migration_file):
            print(f"❌ 마이그레이션 파일을 찾을 수 없습니다: {migration_file}")
            return False
        
        with open(migration_file, 'r', encoding='utf-8') as f:
            migration_sql = f.read()
        
        # 마이그레이션 실행
        with engine.connect() as connection:
            # 트랜잭션 시작
            with connection.begin():
                # 스키마 설정
                connection.execute(text("SET search_path TO public"))
                
                # 마이그레이션 SQL 실행
                connection.execute(text(migration_sql))
                
                print("✅ Assets 테이블 마이그레이션이 성공적으로 완료되었습니다!")
        
        # 마이그레이션 결과 확인
        with engine.connect() as connection:
            result = connection.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = 'assets'
            """))
            
            if result.fetchone():
                print("✅ Assets 테이블이 성공적으로 생성되었습니다!")
                
                # 테이블 구조 확인
                result = connection.execute(text("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_schema = 'public' AND table_name = 'assets'
                    ORDER BY ordinal_position
                """))
                
                print("📋 Assets 테이블 구조:")
                for row in result:
                    print(f"  - {row[0]}: {row[1]} (nullable: {row[2]}, default: {row[3]})")
            else:
                print("❌ Assets 테이블 생성에 실패했습니다.")
                return False
                
    except Exception as e:
        print(f"❌ 마이그레이션 실행 중 오류 발생: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = run_migration()
    if success:
        print("🎉 Assets 테이블 마이그레이션이 완료되었습니다!")
    else:
        print("💥 Assets 테이블 마이그레이션에 실패했습니다.")
        sys.exit(1) 