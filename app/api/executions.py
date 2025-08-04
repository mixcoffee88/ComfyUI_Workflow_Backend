from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from app.db.database import get_db
from app.models.execution import Execution
from app.models.workflow import Workflow
from app.models.asset import Asset
from app.api.auth import get_current_user
from app.models.user import User
from app.services.comfyui_service import ComfyUIService

router = APIRouter()

class ExecutionResponse(BaseModel):
    id: int
    workflow_id: int
    user_id: int
    status: str
    input_data: Optional[dict]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    comfyui_prompt_id: Optional[str]
    workflow: Optional[dict]
    assets: Optional[List[dict]]

    class Config:
        from_attributes = True

@router.get("/my", response_model=List[ExecutionResponse])
async def get_my_executions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """현재 사용자의 실행 기록 조회"""
    try:
        executions = db.query(Execution).filter(
            Execution.user_id == current_user.id
        ).order_by(Execution.started_at.desc()).all()
        
        print(f"🔍 사용자 {current_user.id}의 실행 기록 개수: {len(executions)}")
        result = []
        for execution in executions:
            # 워크플로우 정보 가져오기
            workflow = db.query(Workflow).filter(Workflow.id == execution.workflow_id).first()
            workflow_data = None
            if workflow:
                workflow_data = {
                    "id": workflow.id,
                    "name": workflow.name,
                    "description": workflow.description
                }
            
            # 에셋 정보 가져오기
            try:
                assets = db.query(Asset).filter(Asset.execution_id == execution.id).all()
                print(f"🔍 Execution {execution.id}의 assets 개수: {len(assets)}")
                assets_data = []
                for asset in assets:
                    print(f"📸 Asset ID: {asset.id}, URL: {asset.image_url}")
                    assets_data.append({
                        "id": asset.id,
                        "image_url": asset.image_url,
                        "created_at": asset.created_at
                    })
            except Exception as asset_error:
                print(f"❌ Assets 조회 오류 (Execution {execution.id}): {asset_error}")
                assets_data = []
            
            execution_data = {
                "id": execution.id,
                "workflow_id": execution.workflow_id,
                "user_id": execution.user_id,
                "status": execution.status,
                "input_data": execution.input_data,
                "started_at": execution.started_at,
                "completed_at": execution.completed_at,
                "comfyui_prompt_id": execution.comfyui_prompt_id,
                "workflow": workflow_data,
                "assets": assets_data
            }
            result.append(execution_data)
        
        return result
    except Exception as e:
        print(f"실행 기록 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=f"실행 기록 조회 실패: {str(e)}")

@router.get("/", response_model=List[ExecutionResponse])
async def get_all_executions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """모든 실행 기록 조회 (관리자용)"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")
    
    try:
        executions = db.query(Execution).order_by(Execution.started_at.desc()).offset(skip).limit(limit).all()
        
        result = []
        for execution in executions:
            # 워크플로우 정보 가져오기
            workflow = db.query(Workflow).filter(Workflow.id == execution.workflow_id).first()
            workflow_data = None
            if workflow:
                workflow_data = {
                    "id": workflow.id,
                    "name": workflow.name,
                    "description": workflow.description
                }
            
            # 에셋 정보 가져오기
            assets = db.query(Asset).filter(Asset.execution_id == execution.id).all()
            assets_data = []
            for asset in assets:
                assets_data.append({
                    "id": asset.id,
                    "image_url": asset.image_url,
                    "created_at": asset.created_at
                })
            
            execution_data = {
                "id": execution.id,
                "workflow_id": execution.workflow_id,
                "user_id": execution.user_id,
                "status": execution.status,
                "input_data": execution.input_data,
                "started_at": execution.started_at,
                "completed_at": execution.completed_at,
                "comfyui_prompt_id": execution.comfyui_prompt_id,
                "workflow": workflow_data,
                "assets": assets_data
            }
            result.append(execution_data)
        
        return result
    except Exception as e:
        print(f"실행 기록 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=f"실행 기록 조회 실패: {str(e)}")

@router.get("/{execution_id}", response_model=ExecutionResponse)
async def get_execution(
    execution_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """특정 실행 기록 조회"""
    try:
        execution = db.query(Execution).filter(Execution.id == execution_id).first()
        if not execution:
            raise HTTPException(status_code=404, detail="실행 기록을 찾을 수 없습니다.")
        
        # 권한 확인 (본인 또는 관리자만 조회 가능)
        if execution.user_id != current_user.id and current_user.role != 'admin':
            raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")
        
        # 워크플로우 정보 가져오기
        workflow = db.query(Workflow).filter(Workflow.id == execution.workflow_id).first()
        workflow_data = None
        if workflow:
            workflow_data = {
                "id": workflow.id,
                "name": workflow.name,
                "description": workflow.description
            }
        
        # 에셋 정보 가져오기
        assets = db.query(Asset).filter(Asset.execution_id == execution.id).all()
        assets_data = []
        for asset in assets:
            assets_data.append({
                "id": asset.id,
                "image_url": asset.image_url,
                "created_at": asset.created_at
            })
        
        execution_data = {
            "id": execution.id,
            "workflow_id": execution.workflow_id,
            "user_id": execution.user_id,
            "status": execution.status,
            "input_data": execution.input_data,
            "started_at": execution.started_at,
            "completed_at": execution.completed_at,
            "comfyui_prompt_id": execution.comfyui_prompt_id,
            "workflow": workflow_data,
            "assets": assets_data
        }
        
        return execution_data
    except HTTPException:
        raise
    except Exception as e:
        print(f"실행 기록 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=f"실행 기록 조회 실패: {str(e)}")

@router.delete("/{execution_id}")
async def delete_execution(
    execution_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """실행 기록 삭제"""
    try:
        execution = db.query(Execution).filter(Execution.id == execution_id).first()
        if not execution:
            raise HTTPException(status_code=404, detail="실행 기록을 찾을 수 없습니다.")
        
        # 권한 확인 (본인 또는 관리자만 삭제 가능)
        if execution.user_id != current_user.id and current_user.role != 'admin':
            raise HTTPException(status_code=403, detail="삭제 권한이 없습니다.")
        
        # 실행 중인 경우 삭제 불가
        if execution.status == 'running':
            raise HTTPException(status_code=400, detail="실행 중인 워크플로우는 삭제할 수 없습니다.")
        
        # 관련 에셋도 함께 삭제
        db.query(Asset).filter(Asset.execution_id == execution_id).delete()
        
        # 실행 기록 삭제
        db.delete(execution)
        db.commit()
        
        return {"message": "실행 기록이 삭제되었습니다."}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"실행 기록 삭제 오류: {e}")
        raise HTTPException(status_code=500, detail=f"실행 기록 삭제 실패: {str(e)}")

@router.get("/queue/status")
async def get_queue_status(
    current_user: User = Depends(get_current_user)
):
    """ComfyUI 큐 상태 조회"""
    try:
        comfyui_service = ComfyUIService()
        queue_status = await comfyui_service.get_queue_status()
        
        return {
            "running": queue_status.get("running", 0),
            "pending": queue_status.get("pending", 0),
            "total": queue_status.get("total", 0),
            "queue_data": queue_status.get("queue_data", {})
        }
    except Exception as e:
        print(f"큐 상태 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=f"큐 상태 조회 실패: {str(e)}") 