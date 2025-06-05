#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
파일 다운로드 API 엔드포인트
"""

from fastapi import APIRouter, HTTPException, Path, Query
from fastapi.responses import FileResponse, StreamingResponse
from pathlib import Path as PathLib
import os
import mimetypes
import zipfile
import io
from typing import List, Optional
import urllib.parse

from core.config import settings

router = APIRouter()

# 허용된 파일 타입과 MIME 타입 매핑
MIME_TYPES = {
    '.hwp': 'application/haansofthwp',
    '.hwpx': 'application/haansofthwpx', 
    '.pdf': 'application/pdf',
    '.doc': 'application/msword',
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    '.json': 'application/json',
    '.txt': 'text/plain',
    '.zip': 'application/zip'
}

def get_safe_path(base_dir: PathLib, filename: str) -> PathLib:
    """안전한 파일 경로 생성 (경로 트래버설 방지)"""
    # 파일명에서 위험한 문자 제거
    safe_filename = os.path.basename(filename)
    safe_filename = "".join(c for c in safe_filename if c.isalnum() or c in ['.', '_', '-', ' '])
    
    if not safe_filename:
        raise HTTPException(status_code=400, detail="유효하지 않은 파일명입니다")
    
    file_path = base_dir / safe_filename
    
    # 경로가 기본 디렉토리 내에 있는지 확인
    try:
        file_path.resolve().relative_to(base_dir.resolve())
    except ValueError:
        raise HTTPException(status_code=400, detail="유효하지 않은 파일 경로입니다")
    
    return file_path

def get_content_type(file_path: PathLib) -> str:
    """파일 확장자에 따른 Content-Type 반환"""
    extension = file_path.suffix.lower()
    
    if extension in MIME_TYPES:
        return MIME_TYPES[extension]
    
    # mimetypes 모듈로 추측
    mime_type, _ = mimetypes.guess_type(str(file_path))
    return mime_type or 'application/octet-stream'

@router.get("/attachment/{filename}")
async def download_attachment(
    filename: str = Path(..., description="다운로드할 첨부파일명"),
    inline: bool = Query(False, description="브라우저에서 바로 열기")
):
    """첨부파일 다운로드"""
    try:
        file_path = get_safe_path(settings.downloads_attachments_dir, filename)
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다")
        
        # 파일 크기 확인
        file_size = file_path.stat().st_size
        if file_size > settings.MAX_FILE_SIZE * 1024 * 1024:  # MB to bytes
            raise HTTPException(status_code=413, detail="파일이 너무 큽니다")
        
        content_type = get_content_type(file_path)
        
        headers = {
            "Content-Length": str(file_size)
        }
        
        if not inline:
            # 다운로드로 처리
            encoded_filename = urllib.parse.quote(filename.encode('utf-8'))
            headers["Content-Disposition"] = f"attachment; filename*=UTF-8''{encoded_filename}"
        
        return FileResponse(
            path=str(file_path),
            media_type=content_type,
            headers=headers
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파일 다운로드 오류: {str(e)}")

@router.get("/json/{filename}")
async def download_json(
    filename: str = Path(..., description="다운로드할 JSON 파일명")
):
    """JSON 파일 다운로드"""
    try:
        # .json 확장자 확인/추가
        if not filename.endswith('.json'):
            filename += '.json'
        
        file_path = get_safe_path(settings.downloads_json_dir, filename)
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="JSON 파일을 찾을 수 없습니다")
        
        return FileResponse(
            path=str(file_path),
            media_type='application/json',
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"JSON 다운로드 오류: {str(e)}")

@router.get("/report/{filename}")
async def download_report(
    filename: str = Path(..., description="다운로드할 보고서 파일명")
):
    """검색 보고서 다운로드"""
    try:
        if not filename.endswith('.json'):
            filename += '.json'
        
        file_path = get_safe_path(settings.downloads_reports_dir, filename)
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="보고서를 찾을 수 없습니다")
        
        return FileResponse(
            path=str(file_path),
            media_type='application/json',
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"보고서 다운로드 오류: {str(e)}")

@router.get("/search-results/{search_id}")
async def download_search_results_zip(search_id: str):
    """특정 검색 결과의 모든 파일을 ZIP으로 다운로드"""
    try:
        # 메모리에 ZIP 파일 생성
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            file_count = 0
            
            # JSON 파일들 추가
            for json_file in settings.downloads_json_dir.glob("*.json"):
                if search_id in json_file.name:
                    zip_file.write(json_file, f"json/{json_file.name}")
                    file_count += 1
            
            # 보고서 파일 추가
            for report_file in settings.downloads_reports_dir.glob("*.json"):
                if search_id in report_file.name:
                    zip_file.write(report_file, f"reports/{report_file.name}")
                    file_count += 1
            
            # 첨부파일들 추가 (크기 제한 적용)
            total_size = 0
            max_total_size = 500 * 1024 * 1024  # 500MB 제한
            
            for attachment_file in settings.downloads_attachments_dir.iterdir():
                if attachment_file.is_file():
                    file_size = attachment_file.stat().st_size
                    
                    if total_size + file_size > max_total_size:
                        continue  # 크기 제한 초과 시 스킵
                    
                    zip_file.write(attachment_file, f"attachments/{attachment_file.name}")
                    total_size += file_size
                    file_count += 1
        
        if file_count == 0:
            raise HTTPException(status_code=404, detail="다운로드할 파일이 없습니다")
        
        zip_buffer.seek(0)
        
        # 스트리밍 응답으로 ZIP 파일 전송
        def generate():
            while True:
                chunk = zip_buffer.read(8192)
                if not chunk:
                    break
                yield chunk
        
        return StreamingResponse(
            generate(),
            media_type='application/zip',
            headers={
                "Content-Disposition": f"attachment; filename=search_results_{search_id}.zip"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ZIP 다운로드 오류: {str(e)}")

@router.get("/list/{file_type}")
async def list_files(
    file_type: str = Path(..., description="파일 타입 (attachment/json/report)"),
    search_id: Optional[str] = Query(None, description="특정 검색 ID 필터")
):
    """파일 목록 조회"""
    try:
        if file_type == "attachment":
            base_dir = settings.downloads_attachments_dir
        elif file_type == "json":
            base_dir = settings.downloads_json_dir
        elif file_type == "report":
            base_dir = settings.downloads_reports_dir
        else:
            raise HTTPException(status_code=400, detail="유효하지 않은 파일 타입입니다")
        
        files = []
        
        for file_path in base_dir.iterdir():
            if file_path.is_file():
                # 검색 ID 필터 적용
                if search_id and search_id not in file_path.name:
                    continue
                
                file_info = {
                    "filename": file_path.name,
                    "size": file_path.stat().st_size,
                    "modified": file_path.stat().st_mtime,
                    "type": file_path.suffix.lower(),
                    "download_url": f"/api/download/{file_type}/{file_path.name}"
                }
                files.append(file_info)
        
        # 수정일 기준 내림차순 정렬
        files.sort(key=lambda x: x["modified"], reverse=True)
        
        return {
            "file_type": file_type,
            "total_files": len(files),
            "files": files
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파일 목록 조회 오류: {str(e)}")

@router.delete("/{file_type}/{filename}")
async def delete_file(
    file_type: str = Path(..., description="파일 타입"),
    filename: str = Path(..., description="삭제할 파일명")
):
    """파일 삭제"""
    try:
        if file_type == "attachment":
            base_dir = settings.downloads_attachments_dir
        elif file_type == "json":
            base_dir = settings.downloads_json_dir
        elif file_type == "report":
            base_dir = settings.downloads_reports_dir
        else:
            raise HTTPException(status_code=400, detail="유효하지 않은 파일 타입입니다")
        
        file_path = get_safe_path(base_dir, filename)
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다")
        
        file_path.unlink()
        
        return {"message": f"파일이 삭제되었습니다: {filename}"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파일 삭제 오류: {str(e)}")

@router.get("/disk-usage")
async def get_disk_usage():
    """디스크 사용량 조회"""
    try:
        def get_dir_size(path: PathLib) -> int:
            total = 0
            for file_path in path.rglob('*'):
                if file_path.is_file():
                    total += file_path.stat().st_size
            return total
        
        usage = {
            "attachments": {
                "size_bytes": get_dir_size(settings.downloads_attachments_dir),
                "file_count": len(list(settings.downloads_attachments_dir.glob('*')))
            },
            "json": {
                "size_bytes": get_dir_size(settings.downloads_json_dir),
                "file_count": len(list(settings.downloads_json_dir.glob('*')))
            },
            "reports": {
                "size_bytes": get_dir_size(settings.downloads_reports_dir),
                "file_count": len(list(settings.downloads_reports_dir.glob('*')))
            }
        }
        
        # 총합 계산
        total_size = sum(item["size_bytes"] for item in usage.values())
        total_files = sum(item["file_count"] for item in usage.values())
        
        usage["total"] = {
            "size_bytes": total_size,
            "size_mb": round(total_size / (1024 * 1024), 2),
            "file_count": total_files
        }
        
        return usage
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"디스크 사용량 조회 오류: {str(e)}")

@router.post("/cleanup")
async def cleanup_files(
    file_type: Optional[str] = Query(None, description="정리할 파일 타입"),
    older_than_days: int = Query(7, ge=1, description="며칠 이전 파일 삭제")
):
    """오래된 파일 정리"""
    try:
        import time
        
        cutoff_time = time.time() - (older_than_days * 24 * 3600)
        deleted_files = []
        
        # 정리할 디렉토리 결정
        if file_type == "attachment":
            dirs_to_clean = [settings.downloads_attachments_dir]
        elif file_type == "json":
            dirs_to_clean = [settings.downloads_json_dir]
        elif file_type == "report":
            dirs_to_clean = [settings.downloads_reports_dir]
        else:
            dirs_to_clean = [
                settings.downloads_attachments_dir,
                settings.downloads_json_dir,
                settings.downloads_reports_dir
            ]
        
        for directory in dirs_to_clean:
            for file_path in directory.iterdir():
                if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                    try:
                        file_path.unlink()
                        deleted_files.append(str(file_path.name))
                    except Exception as e:
                        print(f"파일 삭제 실패: {file_path} - {e}")
        
        return {
            "message": f"{len(deleted_files)}개 파일이 삭제되었습니다",
            "deleted_files": deleted_files,
            "cutoff_days": older_than_days
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파일 정리 오류: {str(e)}")