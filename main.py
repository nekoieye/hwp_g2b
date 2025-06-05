#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
나라장터 입찰공고 검색 웹 애플리케이션
FastAPI 메인 서버
"""

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import uvicorn
import os
from pathlib import Path

# API 라우터 임포트
from api.search import router as search_router
from api.download import router as download_router
from core.config import settings

# FastAPI 앱 초기화
app = FastAPI(
    title="나라장터 입찰공고 검색 시스템",
    description="키워드와 날짜로 나라장터 입찰공고를 검색하고 첨부파일을 분석하는 웹 시스템",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 및 템플릿 설정
BASE_DIR = Path(__file__).parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
app.mount("/downloads", StaticFiles(directory=BASE_DIR / "downloads"), name="downloads")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

# 다운로드 디렉토리 생성
download_dirs = [
    BASE_DIR / "downloads" / "attachments",
    BASE_DIR / "downloads" / "json", 
    BASE_DIR / "downloads" / "reports"
]
for dir_path in download_dirs:
    dir_path.mkdir(parents=True, exist_ok=True)

# API 라우터 등록
app.include_router(search_router, prefix="/api/search", tags=["search"])
app.include_router(download_router, prefix="/api/download", tags=["download"])

# 웹 페이지 라우트
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """메인 페이지"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/results/{search_id}", response_class=HTMLResponse)
async def results_page(request: Request, search_id: str):
    """검색 결과 페이지"""
    return templates.TemplateResponse("results.html", {
        "request": request, 
        "search_id": search_id
    })

@app.get("/search-results", response_class=HTMLResponse)
async def search_results_page(request: Request, search_id: str = None):
    """간편 검색 결과 페이지 - results.html 사용"""
    # 간편 검색 결과도 results.html로 통합
    if search_id:
        return templates.TemplateResponse("results.html", {
            "request": request, 
            "search_id": search_id
        })
    else:
        # search_id가 없으면 메인 페이지로 리다이렉트
        return templates.TemplateResponse("index.html", {"request": request})

@app.get("/favicon.ico")
async def favicon():
    """파비콘 요청 무시"""
    return {"status": "no favicon"}

@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {"status": "healthy", "service": "g2b-search-system"}

# 전역 예외 핸들러
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return templates.TemplateResponse("404.html", {
        "request": request
    }, status_code=404)

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    return templates.TemplateResponse("500.html", {
        "request": request
    }, status_code=500)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=8000,  
        reload=settings.DEBUG,
        log_level="info"
    )