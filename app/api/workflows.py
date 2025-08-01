from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import json
import re
from datetime import datetime

from app.api.auth import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.models.workflow import Workflow
from app.models.execution import Execution
from app.services.comfyui_service import ComfyUIService

router = APIRouter()

class WorkflowCreate(BaseModel):
    name: str
    description: str = ""
    workflow_data: dict
    input_fields: Optional[dict] = {}

class WorkflowResponse(BaseModel):
    id: int
    name: str
    description: str
    workflow_data: dict
    input_fields: Optional[dict] = {}
    status: str
    user_id: int
    created_at: datetime

class WorkflowExecuteRequest(BaseModel):
    workflow_id: int
    input_values: Optional[dict] = {}

class WorkflowStatusUpdate(BaseModel):
    status: str  # "WAIT" 또는 "OPEN"

# 상태값 한글 매핑
STATUS_DISPLAY_MAP = {
    "WAIT": "대기",
    "OPEN": "오픈"
}

@router.get("/", response_model=List[WorkflowResponse])
async def get_workflows(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """워크플로우 목록 조회"""
    if current_user.role == 'admin':
        # 관리자는 모든 워크플로우 조회 가능
        workflows = db.query(Workflow).all()
    else:
        # 일반 사용자는 오픈 상태인 워크플로우만 조회 가능
        workflows = db.query(Workflow).filter(Workflow.status == "OPEN").all()
    
    return [WorkflowResponse(
        id=w.id,
        name=w.name,
        description=w.description,
        workflow_data=w.workflow_data,
        input_fields=w.input_fields or {},
        status=w.status,
        user_id=w.user_id,
        created_at=w.created_at
    ) for w in workflows]

@router.post("/", response_model=WorkflowResponse)
async def create_workflow(
    workflow: WorkflowCreate, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """새 워크플로우 생성"""
    new_workflow = Workflow(
        name=workflow.name,
        description=workflow.description,
        workflow_data=workflow.workflow_data,
        input_fields=workflow.input_fields or {},
        user_id=current_user.id
    )
    
    db.add(new_workflow)
    db.commit()
    db.refresh(new_workflow)
    
    return WorkflowResponse(
        id=new_workflow.id,
        name=new_workflow.name,
        description=new_workflow.description,
        workflow_data=new_workflow.workflow_data,
        input_fields=new_workflow.input_fields or {},
        status=new_workflow.status,
        user_id=new_workflow.user_id,
        created_at=new_workflow.created_at
    )

@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: int, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """특정 워크플로우 조회"""
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # 소유자만 접근 가능
    if workflow.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return WorkflowResponse(
        id=workflow.id,
        name=workflow.name,
        description=workflow.description,
        workflow_data=workflow.workflow_data,
        input_fields=workflow.input_fields or {},
        status=workflow.status,
        user_id=workflow.user_id,
        created_at=workflow.created_at
    )

@router.put("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: int, 
    workflow_update: WorkflowCreate, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """워크플로우 업데이트"""
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # 소유자만 수정 가능
    if workflow.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    workflow.name = workflow_update.name
    workflow.description = workflow_update.description
    workflow.workflow_data = workflow_update.workflow_data
    workflow.input_fields = workflow_update.input_fields or {}
    
    db.commit()
    db.refresh(workflow)
    
    return WorkflowResponse(
        id=workflow.id,
        name=workflow.name,
        description=workflow.description,
        workflow_data=workflow.workflow_data,
        input_fields=workflow.input_fields or {},
        status=workflow.status,
        user_id=workflow.user_id,
        created_at=workflow.created_at
    )

@router.delete("/{workflow_id}")
async def delete_workflow(
    workflow_id: int, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """워크플로우 삭제"""
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # 소유자만 삭제 가능
    if workflow.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    db.delete(workflow)
    db.commit()
    
    return {"message": "Workflow deleted successfully"}

@router.put("/{workflow_id}/status", response_model=WorkflowResponse)
async def update_workflow_status(
    workflow_id: int,
    status_update: WorkflowStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """워크플로우 상태 변경 (관리자만 가능)"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")
    
    if status_update.status not in ["WAIT", "OPEN"]:
        raise HTTPException(status_code=400, detail="상태값은 'WAIT' 또는 'OPEN'이어야 합니다.")
    
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    workflow.status = status_update.status
    db.commit()
    db.refresh(workflow)
    
    return WorkflowResponse(
        id=workflow.id,
        name=workflow.name,
        description=workflow.description,
        workflow_data=workflow.workflow_data,
        input_fields=workflow.input_fields or {},
        status=workflow.status,
        user_id=workflow.user_id,
        created_at=workflow.created_at
    )

@router.post("/execute")
async def execute_workflow_with_inputs(
    execute_request: WorkflowExecuteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """입력값을 적용하여 워크플로우 실행"""
    workflow = db.query(Workflow).filter(Workflow.id == execute_request.workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # 소유자만 실행 가능 (또는 관리자가 생성한 공개 워크플로우)
    if workflow.status != "OPEN" and workflow.role == "user":
        # 추후에 공개 워크플로우 기능을 추가할 수 있음
        raise HTTPException(status_code=403, detail="Access denied")
    
    # 새 실행 기록 생성
    new_execution = Execution(
        workflow_id=execute_request.workflow_id,
        user_id=current_user.id,
        status="pending",
        input_data=execute_request.input_values,
        started_at=datetime.now()
    )
    
    db.add(new_execution)
    db.commit()
    db.refresh(new_execution)
    try:
        # 플레이스홀더를 실제 값으로 replace
        processed_workflow_data = replace_placeholders(
            workflow.workflow_data, 
            workflow.input_fields or {}, 
            execute_request.input_values or {}
        )
        
        # ComfyUI API 호출 (workflow_api_sample.py 참조)
        comfyui_service = ComfyUIService()
        result = await comfyui_service.execute_workflow(new_execution.id, processed_workflow_data)
        
        # 실행 결과 업데이트
        new_execution.status = result.get("status", "completed")
        new_execution.output_data = result
        new_execution.completed_at = datetime.now()
        
        # prompt_id 저장
        if result.get("prompt_id"):
            new_execution.comfyui_prompt_id = result.get("prompt_id")
        
        if result.get("status") == "failed" or result.get("status") == "timeout":
            new_execution.error_message = result.get("error", "Unknown error")
        
        db.commit()
        
        return {
            "message": "Workflow executed successfully",
            "execution_id": new_execution.id,
            "status": new_execution.status,
            "result": result,
            "processed_workflow_data": processed_workflow_data,
            "original_placeholders": list((workflow.input_fields or {}).keys()),
            "applied_values": execute_request.input_values
        }
        
    except Exception as e:
        # 실행 실패 시 에러 기록
        new_execution.status = "failed"
        new_execution.error_message = str(e)
        new_execution.completed_at = datetime.now()
        db.commit()
        
        raise HTTPException(
            status_code=500, 
            detail=f"Workflow execution failed: {str(e)}"
        )

def replace_placeholders(workflow_data: dict, field_configs: dict, input_values: dict) -> dict:
    """워크플로우 JSON에서 플레이스홀더를 실제 값으로 교체"""
    
    # JSON을 문자열로 변환
    workflow_json_str = json.dumps(workflow_data, ensure_ascii=False)
    
    # 각 플레이스홀더를 실제 값으로 교체
    for placeholder, field_config in field_configs.items():

        # 사용자가 입력한 값 또는 기본값 사용
        value = input_values.get(placeholder, field_config.get('defaultValue', ''))
        
        # 타입에 따른 값 변환
        field_type = field_config.get('type', 'text')
        if field_type == 'number':
            try:
                value = int(value) if value else 0
            except (ValueError, TypeError):
                value = 0
        elif field_type == 'float':
            try:
                value = float(value) if value else 0.0
            except (ValueError, TypeError):
                value = 0.0
        elif field_type in ['text', 'textarea', 'select']:
            value = str(value) if value is not None else ''
        
        # 플레이스홀더를 실제 값으로 교체
        # JSON에서 문자열 값인 경우와 다른 타입인 경우를 구분
        if field_type in ['number', 'float']:
            # 숫자 타입인 경우 따옴표 없이 교체                 
            pattern = f'"{placeholder}"'
            print(f"pattern : {pattern}, value : {value}")
            workflow_json_str = workflow_json_str.replace(pattern, str(value))
        else:
            # 문자열 타입인 경우 따옴표 포함하여 교체
            workflow_json_str = workflow_json_str.replace(placeholder, str(value))
    
    # 문자열을 다시 JSON으로 변환
    try:
        return json.loads(workflow_json_str)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Failed to process workflow data: {str(e)}")

@router.get("/{workflow_id}/input-form")
async def get_workflow_input_form(
    workflow_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """워크플로우의 입력 폼 정보 조회"""
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # 소유자만 접근 가능
    if workflow.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return {
        "workflow_id": workflow.id,
        "workflow_name": workflow.name,
        "input_fields": workflow.input_fields or {},
        "has_input_fields": bool(workflow.input_fields)
    } 