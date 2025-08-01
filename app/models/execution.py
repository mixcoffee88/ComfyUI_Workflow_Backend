from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base

class Execution(Base):
    __tablename__ = "executions"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String(20), default="pending", nullable=False)  # pending, running, completed, failed
    comfyui_prompt_id = Column(String(100))  # ComfyUI에서 받은 prompt ID
    input_data = Column(JSON)  # 실행 시 입력 데이터
    output_data = Column(JSON)  # 실행 결과 데이터
    error_message = Column(Text)  # 에러 발생 시 메시지
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 관계 설정
    workflow = relationship("Workflow", back_populates="executions")
    user = relationship("User", back_populates="executions")
    assets = relationship("Asset", back_populates="execution", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Execution(id={self.id}, workflow_id={self.workflow_id}, status='{self.status}')>"

# User 모델에 executions 관계 추가
from app.models.user import User
User.executions = relationship("Execution", back_populates="user", cascade="all, delete-orphan") 