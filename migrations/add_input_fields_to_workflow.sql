-- 워크플로우 테이블에 input_fields 컬럼 추가
-- 실행 방법: psql -h [host] -p [port] -U [username] -d [database] -f add_input_fields_to_workflow.sql

-- input_fields 컬럼 추가 (JSON 타입)
ALTER TABLE workflows ADD COLUMN IF NOT EXISTS input_fields JSON;

-- 기존 레코드에 대해 빈 JSON 객체로 초기화
UPDATE workflows SET input_fields = '{}' WHERE input_fields IS NULL;

-- 확인
SELECT 
    column_name, 
    data_type, 
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'workflows' 
    AND column_name = 'input_fields';

-- 테이블 구조 확인
\d workflows; 