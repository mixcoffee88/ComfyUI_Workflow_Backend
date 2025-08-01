from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from pydantic import BaseModel

from app.db.database import get_db
from app.models.execution import Execution
from app.models.asset import Asset

router = APIRouter()

class CallbackRequest(BaseModel):
    images: List[dict]

@router.post("/{execution_id}")
async def callback(
    execution_id: int = Path(..., description="실행 ID"),
    request: CallbackRequest = None,
    db: Session = Depends(get_db)
):
    """
    워크플로우 실행 완료 callback API
    
    - execution_id: URL 경로로 받는 실행 ID
    - images: request body로 받는 이미지 URL 배열
    """
    print(f"🔔 Callback received for execution_id: {execution_id}")
    print(f"📦 Request body: {request}")
    
    try:
        # execution_id로 실행 기록 조회
        execution = db.query(Execution).filter(Execution.id == execution_id).first()
        if not execution:
            print(f"❌ Execution ID {execution_id} not found")
            raise HTTPException(status_code=404, detail=f"Execution ID {execution_id}를 찾을 수 없습니다.")
        
        print(f"✅ Found execution: {execution.id}, current status: {execution.status}")
        
        # 기존 assets 확인
        existing_assets = db.query(Asset).filter(Asset.execution_id == execution_id).all()
        print(f"📋 Found {len(existing_assets)} existing assets for execution {execution_id}")
        
        # request body가 없으면 기본값 설정
        if request is None:
            request = CallbackRequest(images=[])
            print("⚠️ No request body provided, using empty images list")
        
        # executions 테이블의 status를 completed로 업데이트
        execution.status = "completed"
        execution.completed_at = datetime.now()
        
        # assets 테이블에 이미지 URL들 삽입
        assets_added = 0
        for image in request.images:
            image_url = image.get("image")
            try:
                asset = Asset(
                    execution_id=execution_id,
                    image_url=image_url
                )
                db.add(asset)
                print(f"📸 Added asset: {image_url}")
                assets_added += 1
            except Exception as asset_error:
                print(f"❌ Error adding asset {image_url}: {asset_error}")
                raise
        
        # 변경사항 저장
        try:
            db.commit()
            print(f"✅ Successfully committed {assets_added} assets to database")
        except Exception as commit_error:
            print(f"❌ Error committing to database: {commit_error}")
            db.rollback()
            raise
        
        print(f"✅ Successfully processed callback for execution {execution_id}")
        
        return {
            "status": "success",
            "message": f"Execution {execution_id} 완료 처리 및 {len(request.images)}개 이미지 저장 완료",
            "execution_id": execution_id,
            "images_count": len(request.images),
            "assets_added": assets_added
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"❌ Error in callback: {str(e)}")
        print(f"❌ Error type: {type(e)}")
        import traceback
        print(f"❌ Error traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Callback 처리 중 오류 발생: {str(e)}") 