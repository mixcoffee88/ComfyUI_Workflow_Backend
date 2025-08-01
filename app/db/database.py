from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from app.core.config import settings

# 동기 엔진 (일반적인 사용)
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=10,  # 연결 풀 크기
    max_overflow=20,  # 최대 오버플로우 연결 수
    pool_pre_ping=True,  # 연결 전 핑 테스트
    pool_recycle=3600,  # 1시간마다 연결 재생성
    pool_timeout=30,  # 연결 타임아웃
    echo=False  # SQL 로그 출력 (개발 시 True)
)

# 연결 후 스키마 설정
def setup_schema():
    """데이터베이스 연결 후 스키마 설정"""
    with engine.connect() as connection:
        # public 스키마 사용
        connection.execute(text("SET search_path TO public"))
        connection.commit()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 비동기 엔진 (필요한 경우)
async_engine = create_async_engine(
    settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
)
AsyncSessionLocal = sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()

# 데이터베이스 세션 의존성
def get_db() -> Session:
    db = SessionLocal()
    try:
        # 스키마 설정
        db.execute(text("SET search_path TO public"))
        db.commit()
        yield db
    finally:
        db.close()

# 비동기 세션 의존성 (필요한 경우)
async def get_async_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

# 데이터베이스 초기화
async def init_db():
    """데이터베이스 테이블 생성"""
    # 스키마 설정
    setup_schema()
    
    # 모든 모델을 import하여 테이블 생성
    from app.models import User, Workflow, Execution, Asset
    
    # 테이블 생성
    Base.metadata.create_all(bind=engine)
    print("✅ 데이터베이스 테이블이 생성되었습니다.")
    
    # 기본 관리자 계정 생성
    await create_default_admin()

async def create_default_admin():
    """기본 관리자 계정 생성"""
    from app.models.user import User
    from app.api.auth import get_password_hash
    from datetime import datetime
    
    db = SessionLocal()
    try:
        # 스키마 설정
        db.execute(text("SET search_path TO public"))
        db.commit()
        
        # 관리자 계정 존재 확인
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            admin_user = User(
                username="admin",
                email="admin@example.com",
                hashed_password=get_password_hash("secret"),
                role="admin",
                is_approved=True,
                is_active=True,
                created_at=datetime.now()
            )
            db.add(admin_user)
            db.commit()
            print("✅ 기본 관리자 계정이 생성되었습니다. (username: admin, password: secret)")
        else:
            print("ℹ️ 관리자 계정이 이미 존재합니다.")
    except Exception as e:
        print(f"❌ 기본 관리자 계정 생성 중 오류: {e}")
        db.rollback()
    finally:
        db.close() 