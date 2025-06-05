// 나라장터 검색 시스템 JavaScript
let currentSearchId = null;
let toastInstance = null;

// DOM 로드 완료 시 초기화
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

// 애플리케이션 초기화
function initializeApp() {
    // Bootstrap 컴포넌트 초기화
    initializeBootstrapComponents();
    
    // 이벤트 리스너 설정
    setupEventListeners();
    
    // 토스트 인스턴스 생성
    const toastElement = document.getElementById('toast');
    if (toastElement) {
        toastInstance = new bootstrap.Toast(toastElement);
    }
}

// Bootstrap 컴포넌트 초기화
function initializeBootstrapComponents() {
    // 툴팁 초기화
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// 이벤트 리스너 설정
function setupEventListeners() {
    // 검색 폼 이벤트
    const searchForm = document.getElementById('searchForm');
    if (searchForm) {
        searchForm.addEventListener('submit', handleSearchSubmit);
    }
}

// 검색 폼 제출 처리
async function handleSearchSubmit(event) {
    event.preventDefault();
    console.log('🔍 검색 시작');
    
    // 폼 데이터 수집
    const formData = collectFormData();
    
    // 유효성 검사
    if (!validateFormData(formData)) {
        return;
    }
    
    console.log('📤 검색 데이터:', formData);
    
    try {
        showLoadingModal('검색 중...', '나라장터 데이터를 검색하고 파일을 다운로드하고 있습니다.');
        
        const response = await fetch('/api/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        hideLoadingModal();
        
        console.log('✅ 검색 결과:', result);
        
        if (result.success) {
            currentSearchId = result.search_id;
            displaySearchResults(result);
            showToast(`검색 완료! ${result.total_count}건의 결과를 찾았습니다.`, 'success');
        } else {
            showToast(`검색 오류: ${result.error}`, 'error');
        }
        
    } catch (error) {
        hideLoadingModal();
        console.error('💥 검색 오류:', error);
        showToast('검색 중 오류가 발생했습니다: ' + error.message, 'error');
    }
}

// 폼 데이터 수집
function collectFormData() {
    const keyword = document.getElementById('keyword').value.trim();
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;
    const numRows = parseInt(document.getElementById('numRows').value) || 100;
    
    // 날짜를 API 형식으로 변환 (YYYYMMDD)
    const startDateFormatted = startDate.replace(/-/g, '');
    const endDateFormatted = endDate.replace(/-/g, '');
    
    return {
        keyword: keyword,
        start_date: startDateFormatted,
        end_date: endDateFormatted,
        num_rows: numRows
    };
}

// 폼 데이터 유효성 검사
function validateFormData(formData) {
    if (!formData.keyword) {
        showToast('검색 키워드를 입력해주세요.', 'error');
        return false;
    }
    
    if (!formData.start_date || !formData.end_date) {
        showToast('시작 날짜와 종료 날짜를 선택해주세요.', 'error');
        return false;
    }
    
    return true;
}

// 검색 결과 표시
function displaySearchResults(searchResult) {
    console.log('📊 검색 결과 표시:', searchResult);
    
    const resultsContainer = document.getElementById('searchResults');
    if (!resultsContainer) {
        console.error('검색 결과 컨테이너를 찾을 수 없습니다.');
        return;
    }
    
    const results = searchResult.results || [];
    
    if (results.length === 0) {
        resultsContainer.innerHTML = `
            <div class="alert alert-info">
                <i class="bi bi-info-circle"></i>
                검색 결과가 없습니다.
            </div>
        `;
        return;
    }
    
    let html = `
        <div class="card">
            <div class="card-header d-flex justify-content-between align-items-center">
                <h5 class="mb-0">
                    <i class="bi bi-list"></i> 검색 결과: ${results.length}건
                </h5>
                <div class="btn-group">
                    <button class="btn btn-primary btn-sm" onclick="downloadAllFiles('${searchResult.search_id}')">
                        <i class="bi bi-download"></i> 전체 다운로드
                    </button>
                </div>
            </div>
            <div class="card-body p-0">
                <div class="table-responsive">
                    <table class="table table-hover mb-0">
                        <thead class="table-light">
                            <tr>
                                <th>공고번호</th>
                                <th>공고명</th>
                                <th>발주기관</th>
                                <th>공고일</th>
                                <th>개찰일</th>
                                <th>예산</th>
                                <th>첨부파일</th>
                                <th>액션</th>
                            </tr>
                        </thead>
                        <tbody>
    `;
    
    results.forEach(item => {
        const attachmentCount = item.attachments ? item.attachments.length : 0;
        const hasAttachments = attachmentCount > 0;
        
        html += `
            <tr>
                <td>
                    <small class="text-muted">${item.bidNtceNo || '-'}</small>
                </td>
                <td>
                    <strong>${item.bidNtceNm || '-'}</strong>
                    <br>
                    <small class="text-muted">${item.cntrctCnclsMthdNm || ''}</small>
                </td>
                <td>${item.ntceInsttNm || '-'}</td>
                <td>${item.bidNtceDt || '-'}</td>
                <td>${item.opengDt || '-'}</td>
                <td>
                    <span class="badge bg-success">${item.presmptPrce || '미공개'}</span>
                </td>
                <td>
                    ${hasAttachments ? `
                        <span class="badge bg-primary" onclick="showAttachmentList('${item.bidNtceNo}', '${searchResult.search_id}')" style="cursor: pointer;">
                            <i class="bi bi-paperclip"></i> ${attachmentCount}개
                        </span>
                    ` : `
                        <span class="badge bg-secondary">
                            <i class="bi bi-dash"></i> 없음
                        </span>
                    `}
                </td>
                <td>
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-outline-primary" onclick="showBidDetail('${item.bidNtceNo}', '${searchResult.search_id}')">
                            <i class="bi bi-eye"></i> 상세보기
                        </button>
                        ${hasAttachments ? `
                            <button class="btn btn-outline-success" onclick="showAttachmentList('${item.bidNtceNo}', '${searchResult.search_id}')">
                                <i class="bi bi-download"></i> 첨부파일
                            </button>
                        ` : ''}
                    </div>
                </td>
            </tr>
        `;
    });
    
    html += `
                        </tbody>
                    </table>
                </div>
            </div>
            <div class="card-footer text-muted">
                <small>
                    <i class="bi bi-clock"></i> 검색 완료: ${new Date().toLocaleString()}
                    ${searchResult.search_dir ? `| <i class="bi bi-folder"></i> 저장 위치: ${searchResult.search_dir}` : ''}
                </small>
            </div>
        </div>
    `;
    
    resultsContainer.innerHTML = html;
    
    // 결과 영역으로 스크롤
    resultsContainer.scrollIntoView({ behavior: 'smooth' });
}

// 상세보기 모달
async function showBidDetail(bidNtceNo, searchId) {
    try {
        showLoadingModal('상세 정보 로딩 중...', '');
        
        const response = await fetch(`/api/search/${searchId}/results`);
        const result = await response.json();
        
        hideLoadingModal();
        
        if (!result.success) {
            showToast('상세 정보를 불러올 수 없습니다.', 'error');
            return;
        }
        
        const item = result.results.find(r => r.bidNtceNo === bidNtceNo);
        if (!item) {
            showToast('해당 공고를 찾을 수 없습니다.', 'error');
            return;
        }
        
        // 상세보기 모달 표시
        displayDetailModal(item, searchId);
        
    } catch (error) {
        hideLoadingModal();
        console.error('상세보기 오류:', error);
        showToast('상세 정보를 불러오는 중 오류가 발생했습니다.', 'error');
    }
}

// 상세보기 모달 표시
function displayDetailModal(item, searchId) {
    const modalBody = document.getElementById('detailModalBody');
    if (!modalBody) {
        console.error('상세보기 모달을 찾을 수 없습니다.');
        return;
    }
    
    const originalData = item.original_data || item;
    
    modalBody.innerHTML = `
        <div class="row">
            <div class="col-md-8">
                <table class="table table-striped">
                    <tr><th width="150">공고번호</th><td>${originalData.bidNtceNo || '-'}</td></tr>
                    <tr><th>공고명</th><td><strong>${originalData.bidNtceNm || '-'}</strong></td></tr>
                    <tr><th>발주기관</th><td>${originalData.ntceInsttNm || '-'}</td></tr>
                    <tr><th>수요기관</th><td>${originalData.dminsttNm || '-'}</td></tr>
                    <tr><th>공고일시</th><td>${originalData.bidNtceDt || '-'}</td></tr>
                    <tr><th>개찰일시</th><td>${originalData.opengDt || '-'}</td></tr>
                    <tr><th>마감일시</th><td>${originalData.bidClseDt || '-'}</td></tr>
                    <tr><th>계약방법</th><td>${originalData.cntrctCnclsMthdNm || '-'}</td></tr>
                    <tr><th>입찰방법</th><td>${originalData.bidMethdNm || '-'}</td></tr>
                    <tr><th>예정가격</th><td><span class="badge bg-success">${originalData.presmptPrce || '미공개'}</span></td></tr>
                    <tr><th>배정예산</th><td><span class="badge bg-info">${originalData.asignBdgtAmt || '미공개'}</span></td></tr>
                    <tr><th>담당자</th><td>${originalData.ntceInsttOfclNm || '-'}</td></tr>
                    <tr><th>연락처</th><td>${originalData.ntceInsttOfclTelNo || '-'}</td></tr>
                    <tr><th>이메일</th><td>${originalData.ntceInsttOfclEmailAdrs || '-'}</td></tr>
                </table>
            </div>
            <div class="col-md-4">
                <div class="card">
                    <div class="card-header">
                        <h6><i class="bi bi-paperclip"></i> 첨부파일</h6>
                    </div>
                    <div class="card-body">
                        ${item.attachments && item.attachments.length > 0 ? 
                            item.attachments.map(att => `
                                <div class="d-flex justify-content-between align-items-center mb-2">
                                    <small>${att.filename}</small>
                                    <div class="btn-group btn-group-sm">
                                        ${att.downloaded ? `
                                            <button class="btn btn-success" onclick="openLocalFile('${att.local_path}')">
                                                <i class="bi bi-box-arrow-up-right"></i> 열기
                                            </button>
                                        ` : `
                                            <span class="badge bg-warning">다운로드 실패</span>
                                        `}
                                    </div>
                                </div>
                            `).join('') : 
                            '<p class="text-muted">첨부파일이 없습니다.</p>'
                        }
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // 모달 표시
    const modal = new bootstrap.Modal(document.getElementById('detailModal'));
    modal.show();
}

// 첨부파일 목록 표시
async function showAttachmentList(bidNtceNo, searchId) {
    try {
        const response = await fetch(`/api/search/${searchId}/results`);
        const result = await response.json();
        
        if (!result.success) {
            showToast('첨부파일 목록을 불러올 수 없습니다.', 'error');
            return;
        }
        
        const item = result.results.find(r => r.bidNtceNo === bidNtceNo);
        if (!item || !item.attachments || item.attachments.length === 0) {
            showToast('첨부파일이 없습니다.', 'info');
            return;
        }
        
        displayAttachmentModal(item);
        
    } catch (error) {
        console.error('첨부파일 목록 오류:', error);
        showToast('첨부파일 목록을 불러오는 중 오류가 발생했습니다.', 'error');
    }
}

// 첨부파일 모달 표시
function displayAttachmentModal(item) {
    const modalBody = document.getElementById('attachmentModalBody');
    if (!modalBody) {
        console.error('첨부파일 모달을 찾을 수 없습니다.');
        return;
    }
    
    modalBody.innerHTML = `
        <div class="list-group">
            ${item.attachments.map(att => `
                <div class="list-group-item d-flex justify-content-between align-items-center">
                    <div>
                        <i class="bi bi-file-earmark text-primary"></i>
                        <strong>${att.filename}</strong>
                        <br>
                        <small class="text-muted">
                            상태: ${att.downloaded ? 
                                '<span class="badge bg-success">다운로드 완료</span>' : 
                                '<span class="badge bg-danger">다운로드 실패</span>'
                            }
                        </small>
                    </div>
                    <div class="btn-group">
                        ${att.downloaded ? `
                            <button class="btn btn-success btn-sm" onclick="openLocalFile('${att.local_path}')">
                                <i class="bi bi-box-arrow-up-right"></i> 열기
                            </button>
                        ` : `
                            <a href="${att.url}" target="_blank" class="btn btn-primary btn-sm">
                                <i class="bi bi-download"></i> 재다운로드
                            </a>
                        `}
                    </div>
                </div>
            `).join('')}
        </div>
    `;
    
    // 모달 표시
    const modal = new bootstrap.Modal(document.getElementById('attachmentModal'));
    modal.show();
}

// 로컬 파일 열기
async function openLocalFile(filePath) {
    try {
        const response = await fetch('/api/open-file', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ file_path: filePath })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showToast('파일을 열었습니다.', 'success');
        } else {
            showToast('파일을 열 수 없습니다: ' + result.error, 'error');
        }
        
    } catch (error) {
        console.error('파일 열기 오류:', error);
        showToast('파일을 여는 중 오류가 발생했습니다.', 'error');
    }
}

// 전체 파일 다운로드
async function downloadAllFiles(searchId) {
    try {
        showToast('패키지를 준비하고 있습니다...', 'info');
        
        // 검색 결과 폴더 열기
        const response = await fetch(`/api/search/${searchId}/results`);
        const result = await response.json();
        
        if (result.success && result.search_dir) {
            await openLocalFile(result.search_dir);
            showToast('다운로드 폴더를 열었습니다.', 'success');
        } else {
            showToast('다운로드 폴더를 찾을 수 없습니다.', 'error');
        }
        
    } catch (error) {
        console.error('패키지 다운로드 오류:', error);
        showToast('패키지 다운로드 중 오류가 발생했습니다.', 'error');
    }
}

// 로딩 모달 표시
function showLoadingModal(title, message) {
    const loadingModal = document.getElementById('loadingModal');
    const loadingTitle = document.getElementById('loadingTitle');
    const loadingMessage = document.getElementById('loadingMessage');
    
    if (loadingTitle) loadingTitle.textContent = title;
    if (loadingMessage) loadingMessage.textContent = message;
    
    if (loadingModal) {
        const modal = new bootstrap.Modal(loadingModal);
        modal.show();
    }
}

// 로딩 모달 숨김
function hideLoadingModal() {
    const loadingModal = document.getElementById('loadingModal');
    if (loadingModal) {
        const modal = bootstrap.Modal.getInstance(loadingModal);
        if (modal) {
            modal.hide();
        }
    }
}

// 토스트 메시지 표시
function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    const toastBody = toast.querySelector('.toast-body');
    const toastIcon = toast.querySelector('.toast-header i');
    
    if (toastBody) {
        toastBody.textContent = message;
    }
    
    // 아이콘과 색상 설정
    if (toastIcon) {
        toastIcon.className = `bi me-2 ${getToastIcon(type)}`;
    }
    
    if (toastInstance) {
        toastInstance.show();
    }
}

// 토스트 아이콘 반환
function getToastIcon(type) {
    switch (type) {
        case 'success': return 'bi-check-circle text-success';
        case 'error': return 'bi-exclamation-circle text-danger';
        case 'warning': return 'bi-exclamation-triangle text-warning';
        default: return 'bi-info-circle text-primary';
    }
}
