# 나라장터 입찰공고 검색 웹 프로젝트 완전 구현

기존의 나라장터 입찰공고 검색 시스템을 FastAPI 기반의 완전한 웹 애플리케이션으로 구현해주세요.
        self.service_key = "0WB5pvvWESBosIfBKdnHwsHyTGAJUnJXMcuomkHoPLQGW4ZB3GZ2Ooay73OlNQGfZBY+6vDpPfCJxYhMnLMVgw=="
        self.base_url = "://apis.data.go.kr/1230000/ad/BidPublicInfoService"

## 프로젝트 요구사항

### 1. 프로젝트 구조
```
g2b_web_search/
├── main.py                 # FastAPI 메인 서버
├── core/
│   ├── __init__.py
│   ├── g2b_search.py      # 기존 검색 로직 (클래스 기반)
│   └── config.py          # 설정 파일
├── api/
│   ├── __init__.py
│   ├── search.py          # 검색 API 엔드포인트
│   └── download.py        # 파일 다운로드 API
├── static/
│   ├── css/
│   │   └── style.css      # CSS 스타일
│   ├── js/
│   │   └── app.js         # JavaScript 로직
│   └── images/            # 이미지 파일들
├── templates/
│   ├── index.html         # 메인 페이지
│   ├── results.html       # 검색 결과 페이지
│   └── base.html          # 기본 템플릿
├── downloads/             # 다운로드 파일 저장소
│   ├── attachments/       # 첨부파일들
│   ├── json/              # JSON 파일들
│   └── reports/           # 검색 보고서들
├── requirements.txt       # 의존성 패키지
└── README.md             # 프로젝트 설명
```

### 2. FastAPI 백엔드 구현

#### main.py 요구사항:
- FastAPI 앱 초기화
- 정적 파일 서빙 설정
- CORS 설정
- 템플릿 엔진 설정 (Jinja2)
- 모든 API 라우터 등록

#### API 엔드포인트 요구사항:

**검색 API (`/api/search`)**:
- POST 요청으로 키워드, 시작날짜, 종료날짜 받기
- 백그라운드 태스크로 검색 실행
- 실시간 진행상황 WebSocket 또는 SSE로 전송
- 검색 완료 시 결과 반환

**결과 조회 API (`/api/results/{search_id}`)**:
- 특정 검색 결과 조회
- 페이지네이션 지원

**파일 다운로드 API (`/api/download/{file_type}/{filename}`)**:
- 첨부파일, JSON, 보고서 다운로드
- 파일 존재 여부 확인
- 적절한 Content-Type 헤더 설정

**검색 상태 API (`/api/status/{search_id}`)**:
- 검색 진행 상태 확인
- 실시간 업데이트

### 3. 웹 UI 구현

#### 메인 페이지 (index.html) 요구사항:
- 깔끔하고 현대적인 디자인
- 키워드 입력 필드
- 날짜 선택기 (시작날짜, 종료날짜)
- 검색 버튼
- 진행상황 표시 영역
- 반응형 디자인 (모바일 지원)

#### 검색 결과 페이지 (results.html) 요구사항:
- 검색된 공고 목록 표시
- 각 공고별 기본 정보 (공고명, 기관명, 개찰일시, 추정가격)
- 키워드가 발견된 첨부파일 정보
- 스니펫 미리보기
- 개별 파일 다운로드 버튼
- 전체 결과 다운로드 버튼
- 필터링 및 정렬 기능
- 페이지네이션

#### JavaScript 기능 요구사항:
- 폼 유효성 검사
- AJAX를 통한 비동기 검색 요청
- 실시간 진행상황 업데이트
- 파일 다운로드 처리
- 검색 결과 동적 렌더링
- 로딩 스피너 및 사용자 피드백

### 4. 핵심 기능 구현

#### 검색 시스템 개선:
- 기존 G2BBidSearchSystem 클래스를 웹 환경에 맞게 수정
- 비동기 처리 지원
- 진행상황 콜백 함수 추가
- 검색 ID 기반 결과 관리
- 에러 핸들링 강화

#### 파일 관리 시스템:
- 다운로드 폴더 자동 생성 및 관리
- 파일 경로 보안 검증
- 임시 파일 정리 기능
- 파일 크기 제한 설정

#### 데이터베이스 (선택사항):
- SQLite를 사용한 검색 이력 저장
- 검색 결과 캐싱
- 사용자 세션 관리

### 5. 보안 및 성능

#### 보안 요구사항:
- 파일 경로 트래버설 방지
- 입력값 검증 및 sanitization
- CORS 적절한 설정
- 파일 업로드/다운로드 크기 제한

#### 성능 최적화:
- 비동기 파일 처리
- 검색 결과 캐싱
- 정적 파일 압축
- 백그라운드 태스크 큐

### 6. 사용자 경험

#### UI/UX 요구사항:
- 직관적인 인터페이스
- 명확한 오류 메시지
- 로딩 상태 표시
- 성공/실패 알림
- 키보드 단축키 지원
- 다크모드 지원 (선택사항)

#### 접근성:
- 스크린 리더 지원
- 키보드 네비게이션
- 적절한 색상 대비
- 반응형 디자인

### 7. 배포 및 운영

#### 설정 파일 요구사항:
- 환경변수를 통한 설정 관리
- 개발/운영 환경 분리
- 로깅 설정
- API 키 보안 관리

#### Docker 지원 (선택사항):
- Dockerfile 작성
- docker-compose.yml 설정
- 환경변수 설정

### 8. 추가 기능 (우선순위 낮음)

- 검색 이력 관리
- 즐겨찾기 기능
- 알림 설정
- 엑셀 내보내기
- 통계 대시보드

## 구현 순서

1. **FastAPI 기본 구조 및 라우팅 설정**
2. **기존 검색 로직을 웹 환경에 맞게 수정**
3. **기본 HTML 템플릿 및 CSS 구현**
4. **검색 API 구현 및 테스트**
5. **파일 다운로드 API 구현**
6. **JavaScript를 통한 동적 UI 구현**
7. **에러 처리 및 사용자 피드백 강화**
8. **성능 최적화 및 보안 강화**
9. **테스트 및 디버깅**
10. **문서화 및 배포 준비**

## 기술 스택

- **백엔드**: FastAPI, Uvicorn, Pydantic
- **프론트엔드**: HTML5, CSS3, Vanilla JavaScript (또는 원하는 프레임워크)
- **템플릿**: Jinja2
- **파일처리**: 기존 pywin32, zipfile, xml.etree.ElementTree
- **HTTP클라이언트**: requests, httpx
- **기타**: python-multipart, aiofiles

위 요구사항을 모두 만족하는 완전한 웹 애플리케이션을 구현해주세요. 각 파일을 개별 아티팩트로 생성하여 실제 동작 가능한 프로젝트를 만들어주세요.