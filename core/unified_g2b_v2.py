import os
import uuid
import json
import aiohttp
import asyncio
import subprocess
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse, parse_qs

class UnifiedG2BSearch:
    def __init__(self):
        self.base_url = "http://apis.data.go.kr/1230000/BidPublicInfoService"
        self.service_key = "0WB5pvvWESBosIfBKdnHwsHyTGAJUnJXMcuomkHoPLQGW4ZB3GZ2Ooay73OlNQGfZBY+6vDpPfCJxYhMnLMVgw=="
        self.base_dir = os.path.join(os.getcwd(), "downloads")
        self.search_cache = {}
        
    def create_search_directory(self, search_id: str) -> str:
        """검색 ID별 디렉토리 생성"""
        search_dir = os.path.join(self.base_dir, search_id)
        os.makedirs(search_dir, exist_ok=True)
        return search_dir
    
    def format_currency(self, amount: str) -> str:
        """금액 포맷팅 (원화 단위)"""
        if not amount or amount == "":
            return "0원"
        try:
            num = int(amount)
            return f"{num:,}원"
        except (ValueError, TypeError):
            return "0원"
    
    def format_date(self, date_str: str) -> str:
        """날짜 포맷팅"""
        if not date_str or date_str == "":
            return "-"
        try:
            # "2025-06-02 09:27:20" -> "2025-06-02"
            return date_str.split(' ')[0]
        except:
            return date_str
    
    def extract_attachments(self, item: Dict) -> List[Dict]:
        """첨부파일 정보 추출"""
        attachments = []
        for i in range(1, 11):
            url_key = f"ntceSpecDocUrl{i}"
            name_key = f"ntceSpecFileNm{i}"
            
            if item.get(url_key) and item.get(name_key):
                attachments.append({
                    "filename": item[name_key],
                    "url": item[url_key],
                    "seq": i
                })
        return attachments
    
    async def download_file(self, url: str, filepath: str) -> bool:
        """파일 다운로드"""
        try:
            # 최대 3번 재시도
            for attempt in range(3):
                try:
                    timeout = aiohttp.ClientTimeout(total=60)  # 60초 타임아웃 설정
                    async with aiohttp.ClientSession(timeout=timeout) as session:
                        async with session.get(url) as response:
                            if response.status == 200:
                                with open(filepath, 'wb') as f:
                                    f.write(await response.read())
                                return True
                            else:
                                print(f"다운로드 실패 (상태 코드: {response.status}), 재시도 {attempt+1}/3")
                except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                    print(f"다운로드 중 오류 발생: {e}, 재시도 {attempt+1}/3")
                    await asyncio.sleep(1)  # 1초 대기 후 재시도
        except Exception as e:
            print(f"Download error: {e}")
        return False
    
    async def download_attachments(self, attachments: List[Dict], search_dir: str, bid_notice_no: str) -> List[Dict]:
        """첨부파일들 다운로드"""
        downloaded_files = []
        download_tasks = []
        
        # 다운로드 작업 생성
        for attachment in attachments:
            filename = attachment["filename"]
            url = attachment["url"]
            
            # 파일명에 입찰공고번호 prefix 추가
            safe_filename = f"{bid_notice_no}_{filename}"
            filepath = os.path.join(search_dir, safe_filename)
            
            # 비동기 다운로드 작업 목록에 추가
            download_tasks.append({
                "url": url,
                "filepath": filepath,
                "filename": filename,
                "attachment": attachment
            })
        
        # 최대 5개 동시 다운로드 실행
        concurrent_downloads = min(5, len(download_tasks))
        chunks = [download_tasks[i:i + concurrent_downloads] 
                  for i in range(0, len(download_tasks), concurrent_downloads)]
        
        for chunk in chunks:
            # 각 청크를 병렬로 다운로드
            tasks = [self.process_download_task(task) for task in chunk]
            download_results = await asyncio.gather(*tasks)
            downloaded_files.extend(download_results)
            
            # 청크 간 약간의 딜레이 (서버 부하 방지)
            await asyncio.sleep(0.5)
        
        return downloaded_files
    
    async def process_download_task(self, task: Dict) -> Dict:
        """단일 다운로드 작업 처리"""
        url = task["url"]
        filepath = task["filepath"]
        filename = task["filename"]
        
        # 다운로드 실행
        success = await self.download_file(url, filepath)
        
        if success:
            return {
                "filename": filename,
                "local_path": filepath,
                "url": url,
                "downloaded": True
            }
        else:
            return {
                "filename": filename,
                "local_path": None,
                "url": url,
                "downloaded": False
            }
    
    async def search_api(self, search_params: Dict) -> Dict:
        """나라장터 API 검색"""
        try:
            # 기본 파라미터 설정
            params = {
                "serviceKey": self.service_key,
                "numOfRows": search_params.get("numOfRows", 100),
                "pageNo": search_params.get("pageNo", 1),
                "type": "json"
            }
            
            # 검색 조건 추가
            if search_params.get("bidNtceNm"):
                params["bidNtceNm"] = search_params["bidNtceNm"]
            if search_params.get("ntceInsttNm"):
                params["ntceInsttNm"] = search_params["ntceInsttNm"]
            if search_params.get("inqryDivCd"):
                params["inqryDivCd"] = search_params["inqryDivCd"]
            if search_params.get("inqryBgnDt"):
                params["inqryBgnDt"] = search_params["inqryBgnDt"]
            if search_params.get("inqryEndDt"):
                params["inqryEndDt"] = search_params["inqryEndDt"]
            
            url = f"{self.base_url}/getBidPblancListInfoThng"
            
            # 최대 5번 재시도
            max_attempts = 5
            for attempt in range(max_attempts):
                try:
                    timeout = aiohttp.ClientTimeout(total=30)  # 30초 타임아웃 설정
                    async with aiohttp.ClientSession(timeout=timeout) as session:
                        async with session.get(url, params=params) as response:
                            if response.status == 200:
                                try:
                                    data = await response.json()
                                    # 응답 구조 확인
                                    if "response" in data:
                                        return data
                                    else:
                                        print(f"API 응답 구조 오류 (시도 {attempt+1}/{max_attempts})")
                                except json.JSONDecodeError:
                                    print(f"API 응답이 JSON 형식이 아님 (시도 {attempt+1}/{max_attempts})")
                            else:
                                print(f"API 요청 실패: {response.status} (시도 {attempt+1}/{max_attempts})")
                    
                    # 재시도 간 대기 시간 (점진적 증가)
                    wait_time = 1 * (attempt + 1)
                    print(f"{wait_time}초 후 재시도...")
                    await asyncio.sleep(wait_time)
                    
                except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                    print(f"API 요청 중 네트워크 오류: {str(e)} (시도 {attempt+1}/{max_attempts})")
                    await asyncio.sleep(2)  # 2초 대기 후 재시도
            
            return {"error": f"API 요청이 5회 연속 실패했습니다. 네트워크 연결을 확인하세요."}
        
        except Exception as e:
            return {"error": f"API 호출 중 오류: {str(e)}"}
    
    async def search_and_download(self, search_params: Dict, search_id: str) -> Dict:
        """통합 검색 및 다운로드 실행"""
        try:
            # 검색 디렉토리 생성
            search_dir = self.create_search_directory(search_id)
            
            # API 검색 실행
            api_result = await self.search_api(search_params)
            
            if "error" in api_result:
                return api_result
            
            # JSON 파일 저장
            json_filepath = os.path.join(search_dir, f"{search_id}_search_results.json")
            with open(json_filepath, 'w', encoding='utf-8') as f:
                json.dump(api_result, f, ensure_ascii=False, indent=2)
            
            # 결과 처리
            if "response" in api_result and "body" in api_result["response"]:
                body = api_result["response"]["body"]
                items = body.get("items", [])
                
                # 각 입찰공고의 첨부파일 다운로드
                processed_items = []
                
                for item in items:
                    bid_notice_no = item.get("bidNtceNo", "")
                    attachments = self.extract_attachments(item)
                    
                    # 첨부파일 다운로드
                    downloaded_files = []
                    if attachments:
                        downloaded_files = await self.download_attachments(
                            attachments, search_dir, bid_notice_no
                        )
                    
                    # 아이템 정보 정리
                    processed_item = {
                        "bidNtceNo": bid_notice_no,
                        "bidNtceNm": item.get("bidNtceNm", ""),
                        "ntceInsttNm": item.get("ntceInsttNm", ""),
                        "bidNtceDt": self.format_date(item.get("bidNtceDt", "")),
                        "opengDt": self.format_date(item.get("opengDt", "")),
                        "bidClseDt": self.format_date(item.get("bidClseDt", "")),  # 마감일 추가
                        "asignBdgtAmt": self.format_currency(item.get("asignBdgtAmt", "")),
                        "presmptPrce": self.format_currency(item.get("presmptPrce", "")),
                        "cntrctCnclsMthdNm": item.get("cntrctCnclsMthdNm", ""),
                        "ntceKindNm": item.get("ntceKindNm", ""),
                        "bidNtceDtlUrl": item.get("bidNtceDtlUrl", ""),
                        "ntceInsttOfclNm": item.get("ntceInsttOfclNm", ""),  # 담당자
                        "ntceInsttOfclTelNo": item.get("ntceInsttOfclTelNo", ""),  # 연락처
                        "ntceInsttOfclEmailAdrs": item.get("ntceInsttOfclEmailAdrs", ""),  # 이메일
                        "attachments": downloaded_files,
                        "original_data": item
                    }
                    processed_items.append(processed_item)
                
                # 검색 결과 캐시에 저장
                result = {
                    "search_id": search_id,
                    "search_params": search_params,
                    "search_dir": search_dir,
                    "json_file": json_filepath,
                    "total_count": body.get("totalCount", 0),
                    "items": processed_items,
                    "timestamp": datetime.now().isoformat()
                }
                
                self.search_cache[search_id] = result
                return result
            
            else:
                return {"error": "API 응답 형식이 올바르지 않습니다."}
        
        except Exception as e:
            return {"error": f"검색 및 다운로드 중 오류: {str(e)}"}
    
    def get_search_result(self, search_id: str) -> Optional[Dict]:
        """검색 결과 조회"""
        return self.search_cache.get(search_id)
    
    def get_search_statistics(self, search_id: str) -> Dict:
        """검색 통계 정보"""
        result = self.search_cache.get(search_id)
        if not result:
            return {"error": "검색 결과를 찾을 수 없습니다."}
        
        items = result.get("items", [])
        
        # 통계 계산
        stats = {
            "total_notices": len(items),
            "total_budget": 0,
            "notice_types": {},
            "contract_methods": {},
            "institutions": {}
        }
        
        for item in items:
            # 예산 총액 계산
            try:
                budget_str = item["original_data"].get("asignBdgtAmt", "0")
                if budget_str:
                    stats["total_budget"] += int(budget_str)
            except:
                pass
            
            # 공고 유형별 통계
            notice_type = item.get("ntceKindNm", "기타")
            stats["notice_types"][notice_type] = stats["notice_types"].get(notice_type, 0) + 1
            
            # 계약 방법별 통계
            contract_method = item.get("cntrctCnclsMthdNm", "기타")
            stats["contract_methods"][contract_method] = stats["contract_methods"].get(contract_method, 0) + 1
            
            # 기관별 통계
            institution = item.get("ntceInsttNm", "기타")
            stats["institutions"][institution] = stats["institutions"].get(institution, 0) + 1
        
        stats["total_budget_formatted"] = self.format_currency(str(stats["total_budget"]))
        
        return stats
    
    def create_download_package(self, search_id: str) -> Optional[str]:
        """전체 패키지 다운로드 파일 생성"""
        result = self.search_cache.get(search_id)
        if not result:
            return None
        
        search_dir = result["search_dir"]
        package_path = os.path.join(search_dir, f"{search_id}_package.zip")
        
        # ZIP 파일 생성 (향후 구현)
        # 현재는 검색 디렉토리 경로만 반환
        return search_dir
    
    def open_local_file(self, filepath: str) -> bool:
        """로컬 파일 열기"""
        try:
            if os.path.exists(filepath):
                if os.name == 'nt':  # Windows
                    os.startfile(filepath)
                elif os.name == 'posix':  # macOS/Linux
                    subprocess.run(['open', filepath])
                return True
        except Exception as e:
            print(f"파일 열기 오류: {e}")
        return False
