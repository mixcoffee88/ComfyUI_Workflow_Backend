from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base

class Workflow(Base):
    __tablename__ = "workflows"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    workflow_data = Column(JSON)  # ComfyUI 워크플로우 JSON 데이터
    input_fields = Column(JSON)  # 동적 입력 필드 설정 정보
    status = Column(String(20), default="WAIT", nullable=False)  # WAIT, OPEN
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 관계 설정
    user = relationship("User", back_populates="workflows")
    executions = relationship("Execution", back_populates="workflow", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Workflow(id={self.id}, name='{self.name}', status='{self.status}', user_id={self.user_id})>"

# User 모델에 workflows 관계 추가를 위한 import
from app.models.user import User
User.workflows = relationship("Workflow", back_populates="user", cascade="all, delete-orphan") 