#!/usr/bin/env python3
"""
PostgreSQL 권한 확인 및 수정 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from app.core.config import settings

def check_and_fix_permissions():
    """권한 확인 및 수정"""
    print("🔍 PostgreSQL 권한 확인 중...")
    
    # 엔진 생성
    engine = create_engine(settings.DATABASE_URL)
    
    try:
        with engine.connect() as connection:
            # 현재 사용자 확인
            result = connection.execute(text("SELECT current_user"))
            current_user = result.fetchone()[0]
            print(f"👤 현재 사용자: {current_user}")
            
            # 테이블 존재 확인
            result = connection.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = 'workflows'
            """))
            if result.fetchone():
                print("✅ workflows 테이블이 존재합니다.")
            else:
                print("❌ workflows 테이블이 존재하지 않습니다.")
                return False
            
            # 권한 확인
            result = connection.execute(text("""
                SELECT privilege_type 
                FROM information_schema.table_privileges 
                WHERE table_name = 'workflows' AND grantee = current_user
            """))
            privileges = [row[0] for row in result]
            print(f"🔑 현재 권한: {', '.join(privileges)}")
            
            # 권한 부여
            print("🔧 권한 부여 중...")
            connection.execute(text("GRANT ALL PRIVILEGES ON TABLE workflows TO comfyui"))
            connection.execute(text("GRANT ALL PRIVILEGES ON TABLE users TO comfyui"))
            connection.execute(text("GRANT ALL PRIVILEGES ON TABLE executions TO comfyui"))
            connection.execute(text("GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO comfyui"))
            connection.commit()
            print("✅ 권한이 부여되었습니다.")
            
            # 권한 다시 확인
            result = connection.execute(text("""
                SELECT privilege_type 
                FROM information_schema.table_privileges 
                WHERE table_name = 'workflows' AND grantee = current_user
            """))
            privileges = [row[0] for row in result]
            print(f"🔑 수정된 권한: {', '.join(privileges)}")
            
    except Exception as e:
        print(f"❌ 권한 확인 중 오류 발생: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = check_and_fix_permissions()
    if success:
        print("🎉 권한 설정이 완료되었습니다!")
    else:
        print("💥 권한 설정에 실패했습니다.")
        sys.exit(1) 