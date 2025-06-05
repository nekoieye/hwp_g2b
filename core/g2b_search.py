#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
나라장터 입찰공고 검색 시스템 (웹 최적화 버전)
"""

import asyncio
import aiohttp
import aiofiles
import json
import os
import re
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from urllib.parse import quote, unquote
import uuid
import time

# Windows HWP 파일 처리용 - 제거됨 (다운로드만 수행)
# try:
#     import win32com.client as win32
#     import pythoncom
#     HWP_AVAILABLE = True
# except ImportError:
#     HWP_AVAILABLE = False
HWP_AVAILABLE = False  # HWP 텍스트 분석 기능 비활성화

class SearchProgress:
    """검색 진행상황 클래스"""
    def __init__(self):
        self.total_bids = 0
        self.processed_bids = 0
        self.current_bid = ""
        self.current_step = ""
        self.errors = []
        self.start_time = datetime.now()
        
    def to_dict(self):
        return {
            "total_bids": self.total_bids,
            "processed_bids": self.processed_bids,
            "current_bid": self.current_bid,
            "current_step": self.current_step,
            "progress_percent": (self.processed_bids / self.total_bids * 100) if self.total_bids > 0 else 0,
            "errors": self.errors,
            "elapsed_time": (datetime.now() - self.start_time).seconds
        }

class G2BWebSearchSystem:
    """나라장터 입찰공고 검색 시스템 (웹 버전)"""
    
    def __init__(self, base_dir: Path):
        self.service_key = "0WB5pvvWESBosIfBKdnHwsHyTGAJUnJXMcuomkHoPLQGW4ZB3GZ2Ooay73OlNQGfZBY+6vDpPfCJxYhMnLMVgw=="
        self.base_url = "http://apis.data.go.kr/1230000/ad/BidPublicInfoService"
        
        # 디렉토리 설정
        self.base_dir = base_dir
        self.json_dir = base_dir / "downloads" / "json"
        self.attachment_dir = base_dir / "downloads" / "attachments" 
        self.reports_dir = base_dir / "downloads" / "reports"
          # 디렉토리 생성
        for directory in [self.json_dir, self.attachment_dir, self.reports_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # 검색 상태 저장
        self.search_status: Dict[str, SearchProgress] = {}
        self.search_results: Dict[str, Any] = {}
    
    async def search_bid_list_async(self, keyword: str, start_date: str, end_date: str, num_rows: int = 100) -> List[Dict]:
        """비동기 입찰공고 목록 검색"""
        url = f"{self.base_url}/getBidPblancListInfoThngPPSSrch"
        
        params = {
            'ServiceKey': self.service_key,
            'type': 'json',
            'numOfRows': str(num_rows),
            'pageNo': '1',
            'inqryDiv': '1',
            'inqryBgnDt': start_date,
            'inqryEndDt': end_date,
            'bidNtceNm': keyword
        }
        
        try:
            print(f"[DEBUG] API 요청 URL: {url}")
            print(f"[DEBUG] API 파라미터: {params}")
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
                async with session.get(url, params=params) as response:
                    response.raise_for_status()
                    data = await response.json()
                    print(f"[DEBUG] API 응답 상태: {response.status}")
                    print(f"[DEBUG] API 응답 헤더: {data.get('response', {}).get('header', {})}")
                    
                    if data.get('response', {}).get('header', {}).get('resultCode') == '00':
                        body = data.get('response', {}).get('body', {})
                        items = body.get('items', [])
                        total_count = body.get('totalCount', 0)                       
                        print(f"[DEBUG] API 응답 성공")
                        print(f"[DEBUG] totalCount: {total_count}")
                        print(f"[DEBUG] items 타입: {type(items)}")
                        
                        if isinstance(items, list) and len(items) > 0:
                            print(f"[DEBUG] 검색된 공고 수: {len(items)}")
                            # 첫 번째 항목의 키를 출력하여 구조 확인
                            if items:
                                print(f"[DEBUG] 첫 번째 항목 키: {list(items[0].keys())}")                            
                            return items
                        elif total_count == 0:
                            print(f"[DEBUG] 검색 조건에 맞는 공고가 없습니다.")
                            return []
                        else:
                            print(f"[DEBUG] 예상치 못한 items 구조: {items}")
                            return []
                    else:
                        result_code = data.get('response', {}).get('header', {}).get('resultCode', 'Unknown')
                        result_msg = data.get('response', {}).get('header', {}).get('resultMsg', '알 수 없는 오류')
                        print(f"[DEBUG] API 오류 - 코드: {result_code}, 메시지: {result_msg}")
                        return []
                    
        except Exception as e:
            print(f"API 호출 오류: {e}")
            return []
    
    async def get_bid_detail_async(self, bid_ntce_no: str, bid_ntce_ord: str = "01") -> Dict:
        """비동기 공고 상세 정보 조회"""
        url = f"{self.base_url}/getBidPblancListInfoThng"
        
        params = {
            'ServiceKey': self.service_key,
            'type': 'json',
            'inqryDiv': '2',
            'bidNtceNo': bid_ntce_no,
            'bidNtceOrd': bid_ntce_ord
        }
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
                async with session.get(url, params=params) as response:
                    response.raise_for_status()
                    data = await response.json()
                    
                    print(f"[DEBUG] 상세조회 API 응답 상태: {response.status}")
                    print(f"[DEBUG] 상세조회 API 응답 헤더: {data.get('response', {}).get('header', {})}")
                    if data.get('response', {}).get('header', {}).get('resultCode') == '00':
                        body = data.get('response', {}).get('body', {})
                        items = body.get('items', [])
                        
                        print(f"[DEBUG] 상세조회 items 타입: {type(items)}")
                        print(f"[DEBUG] 상세조회 items 길이: {len(items) if isinstance(items, list) else 'Not a list'}")
                        
                        # 실제 JSON 구조: response.body.items는 배열
                        if isinstance(items, list) and len(items) > 0:
                            print(f"[DEBUG] 상세조회 성공 - 첫 번째 항목 반환")
                            return items[0]
                        else:
                            print(f"[DEBUG] 상세조회 결과 없음 또는 빈 배열")
                            return {}
                    else:
                        result_code = data.get('response', {}).get('header', {}).get('resultCode', 'Unknown')
                        result_msg = data.get('response', {}).get('header', {}).get('resultMsg', '알 수 없는 오류')
                        print(f"[DEBUG] 상세조회 API 오류 - 코드: {result_code}, 메시지: {result_msg}")
                        return {}
                    
        except Exception as e:
            print(f"상세 조회 오류: {e}")
            return {}
    
    async def save_bid_json_async(self, bid_data: Dict, bid_no: str) -> Optional[str]:
        """비동기 JSON 저장"""
        filepath = self.json_dir / f"{bid_no}.json"
        try:
            async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(bid_data, ensure_ascii=False, indent=4))
            return str(filepath)
        except Exception as e:
            print(f"JSON 저장 오류: {e}")
            return None
    
    async def download_attachment_async(self, url: str, filename: str) -> Optional[str]:
        """비동기 첨부파일 다운로드"""
        if not url or url in ['추후제공예정', '']:
            return None
        
        # 안전한 파일명 생성
        safe_filename = "".join(c for c in filename if c.isalnum() or c in ['.', '_', '-', ' ']).strip()
        if not safe_filename:
            safe_filename = f"attachment_{int(time.time())}"
        
        filepath = self.attachment_dir / safe_filename
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=120)) as session:
                async with session.get(url) as response:
                    response.raise_for_status()
                    
                    async with aiofiles.open(filepath, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            await f.write(chunk)
            
            return str(filepath)
            
        except Exception as e:
            print(f"파일 다운로드 오류 ({filename}): {e}")
            return None
    
    # HWP 텍스트 추출 기능 제거됨 (다운로드만 수행)
    # def extract_text_from_hwp(self, hwp_path: str) -> str:
    #     """HWP 파일 텍스트 추출 (동기) - 제거됨"""
    #     return ""
    
    # def extract_text_from_hwpx(self, hwpx_path: str) -> str:
    #     """HWPX 파일 텍스트 추출 - 제거됨"""
    #     return ""
    
    # def search_keyword_in_text(self, text: str, keyword: str, context_chars: int = 100) -> List[str]:
    #     """텍스트에서 키워드 검색 및 스니펫 생성 - 제거됨"""    #     return []
    
    async def process_bid_attachments_async(self, bid_detail: Dict, keyword: str, progress: SearchProgress) -> Dict:
        """비동기 첨부파일 처리 (다운로드만)"""
        attachment_results = {}
        
        # 첨부파일 처리 (최대 10개)
        for i in range(1, 11):
            file_url_key = f"ntceSpecDocUrl{i}"
            file_name_key = f"ntceSpecFileNm{i}"
            
            file_url = bid_detail.get(file_url_key)
            file_name = bid_detail.get(file_name_key)
            
            if file_name and file_url:
                progress.current_step = f"첨부파일 다운로드: {file_name}"
                
                downloaded_path = await self.download_attachment_async(file_url, file_name)
                
                if downloaded_path:
                    file_ext = os.path.splitext(file_name.lower())[1]
                    
                    # 파일 정보만 저장 (내용 분석 없이)
                    attachment_results[file_name] = {
                        'path': downloaded_path,
                        'file_size': os.path.getsize(downloaded_path),
                        'file_extension': file_ext,
                        'download_url': f'/downloads/attachments/{os.path.basename(downloaded_path)}',
                        'downloaded': True
                    }
                    
                    print(f"[DEBUG] 첨부파일 다운로드 완료: {file_name} ({os.path.getsize(downloaded_path)} bytes)")
        
        return attachment_results
    
    async def generate_search_report_async(self, search_results: List[Dict], keyword: str, search_id: str) -> str:
        """비동기 검색 보고서 생성"""
        report_path = self.reports_dir / f"search_report_{keyword}_{search_id}.json"
        
        report_data = {
            'search_id': search_id,
            'search_keyword': keyword,
            'search_date': datetime.now().isoformat(),
            'total_bids_found': len(search_results),
            'results': search_results
        }
        
        try:
            async with aiofiles.open(report_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(report_data, ensure_ascii=False, indent=4))
            return str(report_path)
        except Exception as e:
            print(f"보고서 저장 오류: {e}")
            return ""
    
    async def run_search_async(self, keyword: str, start_date: str, end_date: str, 
                             progress_callback: Optional[Callable] = None) -> str:
        """비동기 전체 검색 프로세스"""
        search_id = str(uuid.uuid4())
        progress = SearchProgress()
        
        self.search_status[search_id] = progress
        
        try:
            # 1단계: 공고 목록 검색
            progress.current_step = "공고 목록 검색 중..."
            if progress_callback:
                await progress_callback(progress.to_dict())
            
            bid_list = await self.search_bid_list_async(keyword, start_date, end_date)
            if not bid_list:
                progress.current_step = "검색 결과 없음"
                progress.errors.append("검색된 공고가 없습니다")
                if progress_callback:
                    await progress_callback(progress.to_dict())
                return search_id
            
            progress.total_bids = len(bid_list)
            all_results = []
            
            # 각 공고 처리
            for idx, bid_item in enumerate(bid_list):
                bid_ntce_no = bid_item.get('bidNtceNo')
                bid_ntce_ord = bid_item.get('bidNtceOrd', '01')
                
                if not bid_ntce_no:
                    continue
                
                progress.processed_bids = idx + 1
                progress.current_bid = f"{bid_ntce_no} - {bid_item.get('bidNtceNm', '')}"
                progress.current_step = "상세 정보 조회 중..."
                
                if progress_callback:
                    await progress_callback(progress.to_dict())
                
                # 상세 정보 조회
                bid_detail = await self.get_bid_detail_async(bid_ntce_no, bid_ntce_ord)
                if not bid_detail:
                    progress.errors.append(f"상세 조회 실패: {bid_ntce_no}")
                    continue
                
                # JSON 저장
                await self.save_bid_json_async(bid_detail, bid_ntce_no)
                
                # 첨부파일 처리
                attachment_results = await self.process_bid_attachments_async(bid_detail, keyword, progress)
                
                # 결과 수집
                if attachment_results:
                    result_entry = {
                        'bid_info': bid_detail,
                        'attachments': attachment_results,
                        'processed_date': datetime.now().isoformat()
                    }
                    all_results.append(result_entry)
                
                # API 호출 제한
                await asyncio.sleep(0.5)
            
            # 최종 보고서 생성
            progress.current_step = "보고서 생성 중..."
            if progress_callback:
                await progress_callback(progress.to_dict())
            
            report_path = await self.generate_search_report_async(all_results, keyword, search_id)
            
            # 검색 결과 저장
            self.search_results[search_id] = {
                'results': all_results,
                'report_path': report_path,
                'keyword': keyword,
                'search_date': datetime.now().isoformat(),
                'total_found': len(all_results)
            }
            
            progress.current_step = "완료"
            if progress_callback:
                await progress_callback(progress.to_dict())
            
        except Exception as e:
            progress.errors.append(f"검색 오류: {str(e)}")
            progress.current_step = "오류 발생"
            if progress_callback:
                await progress_callback(progress.to_dict())
        
        return search_id
    
    def get_search_status(self, search_id: str) -> Optional[Dict]:
        """검색 상태 조회"""
        if search_id in self.search_status:
            return self.search_status[search_id].to_dict()
        return None
    
    def get_search_results(self, search_id: str) -> Optional[Dict]:
        """검색 결과 조회"""
        return self.search_results.get(search_id)
    
    def cleanup_old_searches(self, max_age_hours: int = 24):
        """오래된 검색 결과 정리"""
        current_time = datetime.now()
        expired_searches = []
        
        for search_id, progress in self.search_status.items():
            if (current_time - progress.start_time).seconds > max_age_hours * 3600:
                expired_searches.append(search_id)
        
        for search_id in expired_searches:
            self.search_status.pop(search_id, None)
            self.search_results.pop(search_id, None)