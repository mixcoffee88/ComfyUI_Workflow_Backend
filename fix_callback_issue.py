#!/usr/bin/env python3
"""
Callback 이슈 해결 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from app.core.config import settings
from app.models.asset import Asset
from app.models.execution import Execution
from sqlalchemy.orm import sessionmaker

def fix_callback_issue():
    """Callback 이슈 해결"""
    print("🔧 Callback 이슈 해결 중...")
    
    # 엔진 생성
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    try:
        # 1. 데이터베이스 연결 확인
        print("1️⃣ 데이터베이스 연결 확인 중...")
        with engine.connect() as connection:
            connection.execute(text("SET search_path TO public"))
            
            # 테이블 목록 확인
            result = connection.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            
            tables = [row[0] for row in result]
            print(f"📋 현재 테이블: {', '.join(tables)}")
        
        # 2. Assets 테이블 마이그레이션 실행
        print("2️⃣ Assets 테이블 마이그레이션 실행 중...")
        migration_file = os.path.join(os.path.dirname(__file__), "migrations", "fix_assets_table.sql")
        
        if os.path.exists(migration_file):
            with open(migration_file, 'r', encoding='utf-8') as f:
                migration_sql = f.read()
            
            with engine.connect() as connection:
                with connection.begin():
                    connection.execute(text("SET search_path TO public"))
                    connection.execute(text(migration_sql))
                    print("✅ Assets 테이블 마이그레이션 완료")
        else:
            print("❌ 마이그레이션 파일을 찾을 수 없습니다")
            return False
        
        # 3. 테이블 구조 확인
        print("3️⃣ 테이블 구조 확인 중...")
        with engine.connect() as connection:
            result = connection.execute(text("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_schema = 'public' AND table_name = 'assets'
                ORDER BY ordinal_position
            """))
            
            print("📋 Assets 테이블 구조:")
            for row in result:
                print(f"  - {row[0]}: {row[1]} (nullable: {row[2]}, default: {row[3]})")
        
        # 4. Execution ID 50 확인
        print("4️⃣ Execution ID 50 확인 중...")
        db = SessionLocal()
        try:
            execution = db.query(Execution).filter(Execution.id == 50).first()
            if execution:
                print(f"✅ Execution ID 50 발견: status={execution.status}")
            else:
                print("❌ Execution ID 50이 존재하지 않습니다")
                return False
        finally:
            db.close()
        
        # 5. Assets 테이블 테스트
        print("5️⃣ Assets 테이블 테스트 중...")
        db = SessionLocal()
        try:
            # 기존 assets 확인
            existing_assets = db.query(Asset).filter(Asset.execution_id == 50).all()
            print(f"📋 Execution 50의 기존 assets: {len(existing_assets)}개")
            
            # 테스트 asset 추가
            test_asset = Asset(
                execution_id=50,
                image_url="test_image_url"
            )
            db.add(test_asset)
            db.commit()
            print("✅ 테스트 asset 추가 성공")
            
            # 추가된 asset 확인
            test_assets = db.query(Asset).filter(Asset.execution_id == 50).all()
            print(f"📋 Execution 50의 총 assets: {len(test_assets)}개")
            
            # 테스트 asset 삭제
            db.delete(test_asset)
            db.commit()
            print("✅ 테스트 asset 삭제 성공")
            
        except Exception as e:
            print(f"❌ Assets 테이블 테스트 실패: {e}")
            db.rollback()
            return False
        finally:
            db.close()
        
        print("🎉 Callback 이슈 해결 완료!")
        return True
        
    except Exception as e:
        print(f"❌ Callback 이슈 해결 중 오류 발생: {e}")
        import traceback
        print(f"❌ Error traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = fix_callback_issue()
    if success:
        print("🎉 모든 작업이 성공적으로 완료되었습니다!")
    else:
        print("💥 작업 중 오류가 발생했습니다.")
        sys.exit(1) 