-- Assets 테이블 구조 수정
-- 실행 방법: psql -h [host] -p [port] -U [username] -d [database] -f fix_assets_table.sql

-- 기존 assets 테이블이 있다면 삭제 (데이터 손실 주의)
DROP TABLE IF EXISTS assets CASCADE;

-- 새로운 assets 테이블 생성
CREATE TABLE IF NOT EXISTS assets (
    id SERIAL PRIMARY KEY,
    execution_id INTEGER NOT NULL,
    image_url VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- 외래키 제약조건
    CONSTRAINT fk_assets_execution_id 
        FOREIGN KEY (execution_id) REFERENCES executions(id) ON DELETE CASCADE
);

-- Assets 테이블 인덱스
CREATE INDEX IF NOT EXISTS idx_assets_execution_id ON assets(execution_id);
CREATE INDEX IF NOT EXISTS idx_assets_created_at ON assets(created_at);

-- Assets 테이블 제약 조건
ALTER TABLE assets ADD CONSTRAINT chk_assets_image_url_not_empty 
    CHECK (image_url IS NOT NULL AND image_url != '');

-- Assets 테이블 코멘트
COMMENT ON TABLE assets IS '실행 결과 이미지 에셋';
COMMENT ON COLUMN assets.id IS '에셋 고유 ID';
COMMENT ON COLUMN assets.execution_id IS '실행 기록 ID';
COMMENT ON COLUMN assets.image_url IS '이미지 URL';
COMMENT ON COLUMN assets.created_at IS '에셋 생성일시';
COMMENT ON COLUMN assets.updated_at IS '마지막 수정일시';

-- updated_at 컬럼 자동 업데이트 트리거
CREATE TRIGGER update_assets_updated_at
    BEFORE UPDATE ON assets
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 테이블 구조 확인
\d assets; 