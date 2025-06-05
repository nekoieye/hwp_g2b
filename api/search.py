#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
나라장터 입찰공고 검색 API
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import uuid
import asyncio
from datetime import datetime

from core.unified_g2b_v2 import UnifiedG2BSearch

router = APIRouter()

# 검색 시스템 인스턴스
search_system = UnifiedG2BSearch()

# 요청 모델
class SearchRequest(BaseModel):
    keyword: str = Field(..., min_length=1, max_length=100, description="검색 키워드 (공고명)")
    start_date: str = Field(..., pattern=r"^\d{8}$", description="시작날짜 (YYYYMMDD)")
    end_date: str = Field(..., pattern=r"^\d{8}$", description="종료날짜 (YYYYMMDD)")
    num_rows: Optional[int] = Field(100, ge=1, le=500, description="검색 결과 수")

@router.post("/search")
async def search_endpoint(request: SearchRequest):
    """🔍 나라장터 공고 검색 및 파일 다운로드"""
    try:
        print(f"🔍 검색 시작: {request.keyword}, {request.start_date} ~ {request.end_date}")
        
        # 검색 ID 생성
        search_id = str(uuid.uuid4())
        
        # 검색 파라미터 구성
        search_params = {
            "bidNtceNm": request.keyword,
            "inqryBgnDt": request.start_date,
            "inqryEndDt": request.end_date,
            "numOfRows": request.num_rows,
            "pageNo": 1
        }
        
        # 검색 및 다운로드 실행
        result = await search_system.search_and_download(search_params, search_id)
        
        if "error" in result:
            print(f"❌ 검색 실패: {result['error']}")
            return {
                'success': False,
                'error': result["error"]
            }
        
        print(f"✅ 검색 완료: {len(result.get('items', []))}개 공고")
        
        processed_items = []
        for item in result.get("items", []):
            processed_item = {
                "bidNtceNo": item.get("bidNtceNo", ""),
                "bidNtceNm": item.get("bidNtceNm", ""),
                "ntceInsttNm": item.get("ntceInsttNm", ""),
                "bidNtceDt": search_system.format_date(item.get("bidNtceDt", "")),
                "opengDt": search_system.format_date(item.get("opengDt", "")),
                "asignBdgtAmt": search_system.format_currency(item.get("asignBdgtAmt", "")),
                "presmptPrce": search_system.format_currency(item.get("presmptPrce", "")),
                "cntrctCnclsMthdNm": item.get("cntrctCnclsMthdNm", ""),
                "ntceKindNm": item.get("ntceKindNm", ""),
                "bidNtceDtlUrl": item.get("bidNtceDtlUrl", ""),
                "ntceInsttOfclNm": item.get("ntceInsttOfclNm", ""),
                "ntceInsttOfclTelNo": item.get("ntceInsttOfclTelNo", ""),
                "ntceInsttOfclEmailAdrs": item.get("ntceInsttOfclEmailAdrs", ""),
                "attachments": [],
                "original_data": item
            }
            processed_items.append(processed_item)
        
        return {
            'success': True,
            'search_id': search_id,
            'total_count': result.get("total_count", 0),
            'results': processed_items,
            'search_dir': result.get("search_dir", ""),
            'json_file': result.get("json_file", "")
        }
        
    except Exception as e:
        print(f"💥 검색 오류: {e}")
        return {
            'success': False,
            'error': str(e)
        }

@router.get("/search/{search_id}/results")
async def get_search_results(search_id: str):
    """📊 검색 결과 조회"""
    try:
        result = search_system.get_search_result(search_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="검색 결과를 찾을 수 없습니다")
        
        processed_items = []
        for item in result.get("items", []):
            processed_item = {
                "bidNtceNo": item.get("bidNtceNo", ""),
                "bidNtceNm": item.get("bidNtceNm", ""),
                "ntceInsttNm": item.get("ntceInsttNm", ""),
                "bidNtceDt": search_system.format_date(item.get("bidNtceDt", "")),
                "opengDt": search_system.format_date(item.get("opengDt", "")),
                "asignBdgtAmt": search_system.format_currency(item.get("asignBdgtAmt", "")),
                "presmptPrce": search_system.format_currency(item.get("presmptPrce", "")),
                "cntrctCnclsMthdNm": item.get("cntrctCnclsMthdNm", ""),
                "ntceKindNm": item.get("ntceKindNm", ""),
                "bidNtceDtlUrl": item.get("bidNtceDtlUrl", ""),
                "ntceInsttOfclNm": item.get("ntceInsttOfclNm", ""),
                "ntceInsttOfclTelNo": item.get("ntceInsttOfclTelNo", ""),
                "ntceInsttOfclEmailAdrs": item.get("ntceInsttOfclEmailAdrs", ""),
                "attachments": [],
                "original_data": item
            }
            processed_items.append(processed_item)
        
        return {
            'success': True,
            'search_id': search_id,
            'total_count': result.get("total_count", 0),
            'results': processed_items
        }
        
    except Exception as e:
        print(f"결과 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/open-file")
async def open_file_endpoint(request: Dict[str, str]):
    """📂 다운로드된 파일 열기"""
    try:
        file_path = request.get("file_path")
        if not file_path:
            return {
                'success': False,
                'error': '파일 경로가 필요합니다'
            }
        
        success = search_system.open_local_file(file_path)
        
        return {
            'success': success,
            'message': "파일이 열렸습니다" if success else "파일을 열 수 없습니다"
        }
        
    except Exception as e:
        print(f"파일 열기 오류: {e}")
        return {
            'success': False,
            'error': str(e)
        }

@router.get("/system/info")
async def get_system_info():
    """ℹ️ 시스템 정보 조회"""
    return {
        "version": "2.0.0",
        "status": "running",
        "features": [
            "통합 검색",
            "JSON 자동 저장", 
            "HWP 파일 자동 다운로드",
            "검색ID별 폴더 구분",
            "로컬 파일 열기",
            "통계 정보 제공"
        ],
        "description": "나라장터 입찰공고 통합 검색 시스템"
    }