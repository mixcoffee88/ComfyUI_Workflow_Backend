from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.api.auth import get_current_user, get_password_hash
from app.db.database import get_db
from app.models.user import User
from app.models.workflow import Workflow
from app.models.execution import Execution

router = APIRouter()

# Pydantic 모델들
class UserManagement(BaseModel):
    id: int
    username: str
    email: str
    role: str
    is_approved: bool
    created_at: datetime

class UserUpdate(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None
    is_approved: Optional[bool] = None

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: str = "user"
    is_approved: bool = False

class SystemStats(BaseModel):
    total_users: int
    approved_users: int
    pending_users: int
    total_workflows: int
    total_executions: int
    completed_executions: int
    failed_executions: int
    server_status: str

class ServerSettings(BaseModel):
    maintenance_mode: bool = False
    allow_registration: bool = True
    max_workflows_per_user: int = 50
    max_executions_per_hour: int = 100

class PaginatedResponse(BaseModel):
    data: List[dict]
    pagination: dict

# 관리자 권한 확인
async def get_admin_user(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

# 사용자 관리 엔드포인트
@router.get("/users", response_model=List[UserManagement])
async def get_all_users(
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """모든 사용자 조회 (관리자용) - 등록일 기준 내림차순 정렬"""
    users = db.query(User).order_by(User.created_at.desc()).all()
    return [UserManagement(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
        is_approved=user.is_approved,
        created_at=user.created_at
    ) for user in users]

@router.put("/users/{user_id}")
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """사용자 정보 업데이트"""
    # 사용자 찾기
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 업데이트 적용
    if user_update.username is not None:
        # 사용자명 중복 체크
        existing_user = db.query(User).filter(
            User.username == user_update.username,
            User.id != user_id
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )
        target_user.username = user_update.username
    if user_update.role is not None:
        target_user.role = user_update.role
    if user_update.is_approved is not None:
        target_user.is_approved = user_update.is_approved
    
    db.commit()
    db.refresh(target_user)
    
    return {"message": "User updated successfully"}

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """사용자 삭제"""
    # 관리자는 삭제할 수 없음
    if user_id == admin_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own admin account"
        )
    
    # 사용자 찾기 및 삭제
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(target_user)
    db.commit()
    
    return {"message": "User deleted successfully"}

@router.post("/users", response_model=UserManagement)
async def create_user_by_admin(
    user_data: UserCreate,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """관리자가 사용자 생성"""
    # 사용자명 중복 체크
    existing_user = db.query(User).filter(
        (User.username == user_data.username) | (User.email == user_data.email)
    ).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already exists"
        )
    
    # 새 사용자 생성
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        role=user_data.role,
        is_approved=user_data.is_approved,
        is_active=True
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return UserManagement(
        id=new_user.id,
        username=new_user.username,
        email=new_user.email,
        role=new_user.role,
        is_approved=new_user.is_approved,
        created_at=new_user.created_at
    )

# 시스템 통계
@router.get("/stats", response_model=SystemStats)
async def get_system_stats(
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """시스템 통계 조회"""
    # 사용자 통계
    total_users = db.query(User).count()
    approved_users = db.query(User).filter(User.is_approved == True).count()
    pending_users = total_users - approved_users
    
    # 워크플로우 통계
    total_workflows = db.query(Workflow).count()
    
    # 실행 기록 통계
    total_executions = db.query(Execution).count()
    completed_executions = db.query(Execution).filter(Execution.status == "completed").count()
    failed_executions = db.query(Execution).filter(Execution.status == "failed").count()
    
    return SystemStats(
        total_users=total_users,
        approved_users=approved_users,
        pending_users=pending_users,
        total_workflows=total_workflows,
        total_executions=total_executions,
        completed_executions=completed_executions,
        failed_executions=failed_executions,
        server_status="running"
    )

# 워크플로우 관리
@router.post("/workflows")
async def create_workflow_admin(
    workflow_data: dict,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """새 워크플로우 생성 (관리자용)"""
    new_workflow = Workflow(
        name=workflow_data.get("name"),
        description=workflow_data.get("description", ""),
        workflow_data=workflow_data.get("workflow_data"),
        input_fields=workflow_data.get("input_fields", {}),  # 입력 필드 설정 저장
        user_id=admin_user.id  # 관리자가 소유자가 됨
    )
    
    db.add(new_workflow)
    db.commit()
    db.refresh(new_workflow)
    
    return {
        "message": "Workflow created successfully",
        "workflow_id": new_workflow.id,
        "workflow": {
            "id": new_workflow.id,
            "name": new_workflow.name,
            "description": new_workflow.description,
            "has_input_fields": bool(new_workflow.input_fields),
            "input_fields_count": len(new_workflow.input_fields) if new_workflow.input_fields else 0,
            "created_at": new_workflow.created_at
        }
    }

@router.get("/workflows", response_model=PaginatedResponse)
async def get_all_workflows_admin(
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="페이지 번호"),
    page_size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    search: Optional[str] = Query(None, description="검색어"),
    status: Optional[str] = Query(None, description="상태 필터")
):
    """모든 워크플로우 조회 (관리자용) - 페이지네이션 지원"""
    try:
        # 기본 쿼리
        query = db.query(Workflow, User.username).join(User, Workflow.user_id == User.id)
        
        # 검색 필터
        if search:
            query = query.filter(
                or_(
                    Workflow.name.ilike(f"%{search}%"),
                    Workflow.description.ilike(f"%{search}%"),
                    User.username.ilike(f"%{search}%")
                )
            )
        
        # 상태 필터
        if status:
            query = query.filter(Workflow.status == status)
        
        # 전체 개수 계산
        total_count = query.count()
        
        # 페이지네이션 적용
        offset = (page - 1) * page_size
        workflows = query.order_by(Workflow.created_at.desc()).offset(offset).limit(page_size).all()
        
        print(f"🔍 관리자 워크플로우 조회 - 페이지: {page}, 크기: {page_size}, 검색: {search}, 상태: {status}")
        print(f"🔍 총 개수: {total_count}, 현재 페이지 개수: {len(workflows)}")
        
        result = []
        for workflow, username in workflows:
            # 실행 통계 계산
            executions = db.query(Execution).filter(Execution.workflow_id == workflow.id).all()
            total_executions = len(executions)
            completed_executions = len([e for e in executions if e.status == "completed"])
            success_rate = f"{(completed_executions / total_executions * 100):.1f}%" if total_executions > 0 else "0%"
            last_executed = max([e.created_at for e in executions]) if executions else None
            
            result.append({
                "id": workflow.id,
                "name": workflow.name,
                "description": workflow.description,
                "workflow_data": workflow.workflow_data,
                "input_fields": workflow.input_fields or {},
                "status": workflow.status,
                "user_id": workflow.user_id,
                "username": username,
                "owner": username,
                "executions_count": total_executions,
                "success_rate": success_rate,
                "last_executed": last_executed,
                "has_input_fields": bool(workflow.input_fields),
                "input_fields_count": len(workflow.input_fields) if workflow.input_fields else 0,
                "created_at": workflow.created_at,
                "updated_at": workflow.updated_at
            })
        
        return {
            "data": result,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total_count,
                "total_pages": (total_count + page_size - 1) // page_size
            }
        }
    except Exception as e:
        print(f"워크플로우 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=f"워크플로우 조회 실패: {str(e)}")

@router.put("/workflows/{workflow_id}")
async def update_workflow_admin(
    workflow_id: int,
    workflow_data: dict,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """워크플로우 수정 (관리자용)"""
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # 워크플로우 업데이트
    workflow.name = workflow_data.get("name", workflow.name)
    workflow.description = workflow_data.get("description", workflow.description)
    workflow.workflow_data = workflow_data.get("workflow_data", workflow.workflow_data)
    workflow.input_fields = workflow_data.get("input_fields", workflow.input_fields or {})
    
    db.commit()
    db.refresh(workflow)
    
    return {
        "message": "Workflow updated successfully",
        "workflow": {
            "id": workflow.id,
            "name": workflow.name,
            "description": workflow.description,
            "workflow_data": workflow.workflow_data,
            "input_fields": workflow.input_fields or {},
            "has_input_fields": bool(workflow.input_fields),
            "input_fields_count": len(workflow.input_fields) if workflow.input_fields else 0,
            "user_id": workflow.user_id,
            "created_at": workflow.created_at,
            "updated_at": workflow.updated_at
        }
    }

@router.get("/workflows/{workflow_id}/executions")
async def get_workflow_executions_admin(
    workflow_id: int,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """워크플로우 실행 기록 조회 (관리자용)"""
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    executions = (
        db.query(Execution)
        .filter(Execution.workflow_id == workflow_id)
        .order_by(Execution.created_at.desc())
        .limit(20)  # 최근 20개만
        .all()
    )
    
    return [
        {
            "id": e.id,
            "status": e.status,
            "started_at": e.started_at,
            "completed_at": e.completed_at,
            "error_message": e.error_message,
            "created_at": e.created_at
        }
        for e in executions
    ]

@router.post("/workflows/duplicate")
async def duplicate_workflow_admin(
    request: dict,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """워크플로우 복제 (관리자용)"""
    workflow_id = request.get("workflow_id")
    new_name = request.get("name")
    new_description = request.get("description")
    
    # 원본 워크플로우 조회
    original_workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not original_workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # 새 워크플로우 생성
    new_workflow = Workflow(
        name=new_name or f"{original_workflow.name} (복사본)",
        description=new_description or original_workflow.description,
        workflow_data=original_workflow.workflow_data,
        user_id=admin_user.id  # 관리자 소유로 복제
    )
    
    db.add(new_workflow)
    db.commit()
    db.refresh(new_workflow)
    
    return {
        "message": "Workflow duplicated successfully",
        "new_workflow_id": new_workflow.id
    }

@router.get("/workflows/export")
async def export_all_workflows_admin(
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """모든 워크플로우 내보내기 (관리자용)"""
    from fastapi.responses import JSONResponse
    
    workflows = db.query(Workflow).all()
    
    export_data = {
        "export_date": datetime.now().isoformat(),
        "exported_by": admin_user.username,
        "total_workflows": len(workflows),
        "workflows": [
            {
                "id": w.id,
                "name": w.name,
                "description": w.description,
                "workflow_data": w.workflow_data,
                "created_at": w.created_at.isoformat() if w.created_at else None,
                "updated_at": w.updated_at.isoformat() if w.updated_at else None
            }
            for w in workflows
        ]
    }
    
    return JSONResponse(
        content=export_data,
        headers={
            "Content-Disposition": f"attachment; filename=workflows_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        }
    )

@router.delete("/workflows/bulk")
async def bulk_delete_workflows_admin(
    request: dict,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """워크플로우 일괄 삭제 (관리자용)"""
    workflow_ids = request.get("workflow_ids", [])
    if not workflow_ids:
        raise HTTPException(status_code=400, detail="No workflow IDs provided")
    
    # 워크플로우들 조회 및 삭제
    workflows = db.query(Workflow).filter(Workflow.id.in_(workflow_ids)).all()
    if not workflows:
        raise HTTPException(status_code=404, detail="No workflows found")
    
    deleted_count = len(workflows)
    for workflow in workflows:
        db.delete(workflow)
    
    db.commit()
    
    return {
        "message": f"{deleted_count} workflows deleted successfully",
        "deleted_count": deleted_count
    }

@router.post("/workflows/bulk-export")
async def bulk_export_workflows_admin(
    request: dict,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """선택된 워크플로우 내보내기 (관리자용)"""
    from fastapi.responses import JSONResponse
    
    workflow_ids = request.get("workflow_ids", [])
    if not workflow_ids:
        raise HTTPException(status_code=400, detail="No workflow IDs provided")
    
    workflows = db.query(Workflow).filter(Workflow.id.in_(workflow_ids)).all()
    if not workflows:
        raise HTTPException(status_code=404, detail="No workflows found")
    
    export_data = {
        "export_date": datetime.now().isoformat(),
        "exported_by": admin_user.username,
        "total_workflows": len(workflows),
        "workflows": [
            {
                "id": w.id,
                "name": w.name,
                "description": w.description,
                "workflow_data": w.workflow_data,
                "created_at": w.created_at.isoformat() if w.created_at else None,
                "updated_at": w.updated_at.isoformat() if w.updated_at else None
            }
            for w in workflows
        ]
    }
    
    return JSONResponse(
        content=export_data,
        headers={
            "Content-Disposition": f"attachment; filename=selected_workflows_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        }
    )

@router.put("/workflows/{workflow_id}/status")
async def update_workflow_status_admin(
    workflow_id: int,
    status_update: dict,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """워크플로우 상태 변경 (관리자용)"""
    if status_update.get("status") not in ["WAIT", "OPEN"]:
        raise HTTPException(status_code=400, detail="상태값은 'WAIT' 또는 'OPEN'이어야 합니다.")
    
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    workflow.status = status_update.get("status")
    db.commit()
    db.refresh(workflow)
    
    return {
        "message": "Workflow status updated successfully",
        "workflow": {
            "id": workflow.id,
            "name": workflow.name,
            "status": workflow.status
        }
    }

@router.delete("/workflows/{workflow_id}")
async def delete_workflow_admin(
    workflow_id: int,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """워크플로우 삭제 (관리자용)"""
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    db.delete(workflow)
    db.commit()
    
    return {"message": "Workflow deleted successfully"}

# 실행 기록 관리
@router.get("/executions", response_model=PaginatedResponse)
async def get_all_executions_admin(
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="페이지 번호"),
    page_size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    search: Optional[str] = Query(None, description="검색어"),
    status: Optional[str] = Query(None, description="상태 필터")
):
    """모든 실행 기록 조회 (관리자용) - 페이지네이션 지원"""
    try:
        # 기본 쿼리
        query = db.query(Execution).join(Workflow).join(User)
        
        # 검색 필터
        if search:
            query = query.filter(
                or_(
                    Workflow.name.ilike(f"%{search}%"),
                    Workflow.description.ilike(f"%{search}%"),
                    User.username.ilike(f"%{search}%")
                )
            )
        
        # 상태 필터
        if status:
            query = query.filter(Execution.status == status)
        
        # 전체 개수 계산
        total_count = query.count()
        
        # 페이지네이션 적용
        offset = (page - 1) * page_size
        executions = query.order_by(Execution.created_at.desc()).offset(offset).limit(page_size).all()
        
        print(f"🔍 관리자 실행 기록 조회 - 페이지: {page}, 크기: {page_size}, 검색: {search}, 상태: {status}")
        print(f"🔍 총 개수: {total_count}, 현재 페이지 개수: {len(executions)}")
        
        result = []
        for execution in executions:
            # 워크플로우 정보 가져오기
            workflow = db.query(Workflow).filter(Workflow.id == execution.workflow_id).first()
            workflow_name = workflow.name if workflow else "Unknown"
            
            # 사용자 정보 가져오기
            user = db.query(User).filter(User.id == execution.user_id).first()
            username = user.username if user else "Unknown"
            
            result.append({
                "id": execution.id,
                "workflow_id": execution.workflow_id,
                "workflow_name": workflow_name,
                "user_id": execution.user_id,
                "username": username,
                "status": execution.status,
                "input_data": execution.input_data,
                "started_at": execution.started_at,
                "completed_at": execution.completed_at,
                "comfyui_prompt_id": execution.comfyui_prompt_id,
                "error_message": execution.error_message,
                "created_at": execution.created_at
            })
        
        return {
            "data": result,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total_count,
                "total_pages": (total_count + page_size - 1) // page_size
            }
        }
    except Exception as e:
        print(f"실행 기록 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=f"실행 기록 조회 실패: {str(e)}")

@router.delete("/executions/{execution_id}")
async def delete_execution_admin(
    execution_id: int,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """실행 기록 삭제 (관리자용)"""
    execution = db.query(Execution).filter(Execution.id == execution_id).first()
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    db.delete(execution)
    db.commit()
    
    return {"message": "Execution deleted successfully"}

# 시스템 설정
@router.get("/settings", response_model=ServerSettings)
async def get_server_settings(
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """서버 설정 조회"""
    # 임시 설정 (실제로는 데이터베이스나 설정 파일에서 읽어옴)
    return ServerSettings()

@router.put("/settings")
async def update_server_settings(
    settings: ServerSettings,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """서버 설정 업데이트"""
    # 실제로는 데이터베이스나 설정 파일에 저장
    return {"message": "Settings updated successfully", "settings": settings} 