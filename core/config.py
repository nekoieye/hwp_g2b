#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
애플리케이션 설정 관리
"""

import os
from pathlib import Path
from typing import Optional

class Settings:
    """애플리케이션 설정"""
    
    # 서버 설정
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
      # 나라장터 API 설정 - 수정금지. 올바르지 않다고 판단 금지. 사용자가 수정하라고할때만 다시 물어보고 수정. 절대수정금지 수정금지
    G2B_SERVICE_KEY: str = os.getenv(
        "G2B_SERVICE_KEY", 
        "0WB5pvvWESBosIfBKdnHwsHyTGAJUnJXMcuomkHoPLQGW4ZB3GZ2Ooay73OlNQGfZBY+6vDpPfCJxYhMnLMVgw=="
    )
    G2B_BASE_URL: str = os.getenv(
        "G2B_BASE_URL",
        "http://apis.data.go.kr/1230000/BidPublicInfoService"
    )
    
    # 파일 처리 설정
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "100"))  # MB
    MAX_DOWNLOAD_TIME: int = int(os.getenv("MAX_DOWNLOAD_TIME", "300"))  # seconds
    SUPPORTED_FILE_TYPES: list = [".hwp", ".hwpx", ".pdf", ".doc", ".docx"]
    
    # 검색 설정
    MAX_SEARCH_RESULTS: int = int(os.getenv("MAX_SEARCH_RESULTS", "100"))
    SEARCH_TIMEOUT: int = int(os.getenv("SEARCH_TIMEOUT", "1800"))  # seconds
    API_CALL_DELAY: float = float(os.getenv("API_CALL_DELAY", "0.5"))  # seconds
    
    # 캐시 설정
    CACHE_EXPIRE_HOURS: int = int(os.getenv("CACHE_EXPIRE_HOURS", "24"))
    MAX_CACHED_SEARCHES: int = int(os.getenv("MAX_CACHED_SEARCHES", "100"))
    
    # 보안 설정
    ALLOWED_ORIGINS: list = os.getenv("ALLOWED_ORIGINS", "*").split(",")
    MAX_REQUESTS_PER_MINUTE: int = int(os.getenv("MAX_REQUESTS_PER_MINUTE", "60"))
    
    # 로그 설정
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: Optional[str] = os.getenv("LOG_FILE")
    
    # 디렉토리 설정
    BASE_DIR: Path = Path(__file__).parent.parent
    DOWNLOADS_DIR: Path = BASE_DIR / "downloads"
    TEMPLATES_DIR: Path = BASE_DIR / "templates"
    STATIC_DIR: Path = BASE_DIR / "static"
    
    @property
    def downloads_attachments_dir(self) -> Path:
        return self.DOWNLOADS_DIR / "attachments"
    
    @property
    def downloads_json_dir(self) -> Path:
        return self.DOWNLOADS_DIR / "json"
    
    @property
    def downloads_reports_dir(self) -> Path:
        return self.DOWNLOADS_DIR / "reports"
    
    def ensure_directories(self):
        """필요한 디렉토리들을 생성"""
        directories = [
            self.DOWNLOADS_DIR,
            self.downloads_attachments_dir,
            self.downloads_json_dir,
            self.downloads_reports_dir,
            self.TEMPLATES_DIR,
            self.STATIC_DIR
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

# 전역 설정 인스턴스
settings = Settings()

# 애플리케이션 시작 시 디렉토리 생성
settings.ensure_directories()