/**
 * 시민 청렴 신고 조회 시스템 - Main Application Logic
 */

// Application State
const state = {
  cases: [],
  filteredCases: [],
  eduData: [],
  currentPage: 1,
  pageSize: 24,
  sort: 'date-desc',
  viewMode: 'grid', // 'grid' | 'table'
  filters: {
    keyword: '',
    type: 'ALL',
    status: 'ALL',
    region: 'ALL'
  }
};

// Type Icons Mapping
const typeIcons = {
  '금품수수': '💰',
  '직권남용': '⚖️',
  '공금유용': '💳',
  '이해충돌': '🤝',
  '예산횡령': '🚨',
  '기타': '📋'
};

// DOM Elements
const dom = {
  searchInput: document.getElementById('searchInput'),
  clearSearchBtn: document.getElementById('clearSearchBtn'),
  typeFilter: document.getElementById('typeFilter'),
  statusFilter: document.getElementById('statusFilter'),
  regionFilter: document.getElementById('regionFilter'),
  resetFiltersBtn: document.getElementById('resetFiltersBtn'),
  emptyResetBtn: document.getElementById('emptyResetBtn'),
  quickChips: document.getElementById('quickStatusChips'),
  resultCount: document.getElementById('resultCount'),
  resultsSubtext: document.getElementById('resultsSubtext'),
  sortSelect: document.getElementById('sortSelect'),
  pageSizeSelect: document.getElementById('pageSizeSelect'),
  cardsGrid: document.getElementById('cardsGrid'),
  tableView: document.getElementById('tableView'),
  tableBody: document.getElementById('tableBody'),
  noResultsState: document.getElementById('noResultsState'),
  paginationWrapper: document.getElementById('paginationWrapper'),
  paginationNav: document.getElementById('paginationNav'),
  pageInfoText: document.getElementById('pageInfoText'),
  viewGridBtn: document.getElementById('viewGridBtn'),
  viewTableBtn: document.getElementById('viewTableBtn'),
  themeToggleBtn: document.getElementById('themeToggleBtn'),
  // Stats
  statTotalCount: document.getElementById('statTotalCount'),
  statCompletedCount: document.getElementById('statCompletedCount'),
  statCompletedRate: document.getElementById('statCompletedRate'),
  statInvestigatingCount: document.getElementById('statInvestigatingCount'),
  statAvgAmount: document.getElementById('statAvgAmount'),
  // Modals
  caseModal: document.getElementById('caseModal'),
  modalCaseId: document.getElementById('modalCaseId'),
  modalStatusBadge: document.getElementById('modalStatusBadge'),
  modalBody: document.getElementById('modalBody'),
  modalCloseBtn: document.getElementById('modalCloseBtn'),
  modalConfirmBtn: document.getElementById('modalConfirmBtn'),
  eduModal: document.getElementById('eduModal'),
  eduModalBtn: document.getElementById('eduModalBtn'),
  eduModalCloseBtn: document.getElementById('eduModalCloseBtn'),
  eduModalConfirmBtn: document.getElementById('eduModalConfirmBtn'),
  eduTableBody: document.getElementById('eduTableBody'),
  eduStatsBar: document.getElementById('eduStatsBar')
};

// Initialize Application
document.addEventListener('DOMContentLoaded', async () => {
  initTheme();
  initEventListeners();
  await loadData();
});

// Load JSON Data
async function loadData() {
  try {
    // Attempt loading from relative path
    const jsonPaths = ['청렴신고_사건데이터.json', 'data/청렴신고_사건데이터.json'];
    let loadedCases = null;

    for (const p of jsonPaths) {
      try {
        const res = await fetch(p);
        if (res.ok) {
          loadedCases = await res.json();
          break;
        }
      } catch (e) {
        // try next
      }
    }

    if (!loadedCases || !Array.isArray(loadedCases)) {
      throw new Error('사건 데이터를 불러올 수 없습니다.');
    }

    state.cases = loadedCases;
    state.filteredCases = [...state.cases];

    // Populate regions dropdown
    populateRegions();

    // Render Stats
    updateOverallStats();

    // Apply initial filters & render
    applyFiltersAndRender();

    // Also load Education data asynchronously
    loadEduData();

  } catch (error) {
    console.error('Data load error:', error);
    dom.cardsGrid.innerHTML = `
      <div style="grid-column: 1/-1; text-align: center; padding: 40px; color: #ef4444;">
        <p>⚠️ 데이터 파일을 로드하는 중 오류가 발생했습니다.</p>
        <p style="font-size: 0.85rem; color: var(--text-muted); margin-top: 6px;">${error.message}</p>
      </div>
    `;
  }
}

// Load Education Data
async function loadEduData() {
  const eduPaths = ['청렴교육_현황.json', 'data/청렴교육_현황.json'];
  for (const p of eduPaths) {
    try {
      const res = await fetch(p);
      if (res.ok) {
        state.eduData = await res.json();
        break;
      }
    } catch (e) {}
  }
}

// Populate Region dropdown
function populateRegions() {
  const regions = Array.from(new Set(state.cases.map(c => c['지역']).filter(Boolean))).sort();
  dom.regionFilter.innerHTML = '<option value="ALL">전국 전체</option>';
  regions.forEach(reg => {
    const opt = document.createElement('option');
    opt.value = reg;
    opt.textContent = reg;
    dom.regionFilter.appendChild(opt);
  });
}

// Update Top Statistics
function updateOverallStats() {
  const total = state.cases.length;
  const completed = state.cases.filter(c => c['처리상태'] === '처리완료').length;
  const investigating = state.cases.filter(c => c['처리상태'] === '조사중' || c['처리상태'] === '이첩').length;
  
  const amounts = state.cases
    .map(c => parseFloat(c['위반금액_만원']))
    .filter(a => !isNaN(a) && a > 0);
  
  const avgAmount = amounts.length > 0 
    ? Math.round(amounts.reduce((sum, v) => sum + v, 0) / amounts.length)
    : 0;

  const rate = total > 0 ? Math.round((completed / total) * 100) : 0;

  dom.statTotalCount.textContent = `${total.toLocaleString()}건`;
  dom.statCompletedCount.textContent = `${completed.toLocaleString()}건`;
  dom.statCompletedRate.textContent = `(${rate}%)`;
  dom.statInvestigatingCount.textContent = `${investigating.toLocaleString()}건`;
  dom.statAvgAmount.textContent = `${avgAmount.toLocaleString()}만원`;
}

// Filter and Render Logic
function applyFiltersAndRender() {
  const { keyword, type, status, region } = state.filters;
  const kw = keyword.trim().toLowerCase();

  state.filteredCases = state.cases.filter(item => {
    // Type Filter
    if (type !== 'ALL' && item['신고유형'] !== type) return false;

    // Status Filter
    if (status !== 'ALL' && item['처리상태'] !== status) return false;

    // Region Filter
    if (region !== 'ALL' && item['지역'] !== region) return false;

    // Keyword Filter
    if (kw) {
      const caseId = (item['사건ID'] || '').toLowerCase();
      const reg = (item['지역'] || '').toLowerCase();
      const reportType = (item['신고유형'] || '').toLowerCase();
      const statusText = (item['처리상태'] || '').toLowerCase();
      const action = (item['조치결과'] || '').toLowerCase();
      const amount = (item['위반금액_만원'] || '');

      const match = caseId.includes(kw) ||
                    reg.includes(kw) ||
                    reportType.includes(kw) ||
                    statusText.includes(kw) ||
                    action.includes(kw) ||
                    amount.includes(kw);
      if (!match) return false;
    }

    return true;
  });

  // Sort Filtered Cases
  sortCases();

  // Reset to first page on filter change
  state.currentPage = 1;

  // Update Result Count - IMAGE REQUIREMENT: 화면에 "결과 N건" 표시
  updateResultCountDisplay();

  // Render Page
  renderCurrentPage();
}

// Sort cases
function sortCases() {
  state.filteredCases.sort((a, b) => {
    if (state.sort === 'date-desc') {
      return (b['신고일자'] || '').localeCompare(a['신고일자'] || '');
    } else if (state.sort === 'date-asc') {
      return (a['신고일자'] || '').localeCompare(b['신고일자'] || '');
    } else if (state.sort === 'amount-desc') {
      const amtA = parseFloat(a['위반금액_만원']) || 0;
      const amtB = parseFloat(b['위반금액_만원']) || 0;
      return amtB - amtA;
    } else if (state.sort === 'amount-asc') {
      const amtA = parseFloat(a['위반금액_만원']) || 0;
      const amtB = parseFloat(b['위반금액_만원']) || 0;
      return amtA - amtB;
    }
    return 0;
  });
}

// Update Exact "결과 N건" Display
function updateResultCountDisplay() {
  const count = state.filteredCases.length;
  // IMAGE REQUIREMENT: 화면에 "결과 N건" 표시
  dom.resultCount.textContent = `결과 ${count.toLocaleString()}건`;

  if (count === state.cases.length) {
    dom.resultsSubtext.textContent = '전체 사건 목록을 표시하고 있습니다.';
  } else {
    dom.resultsSubtext.textContent = `조건에 맞는 ${count.toLocaleString()}건의 사건이 검색되었습니다.`;
  }
}

// Render current page items
function renderCurrentPage() {
  const count = state.filteredCases.length;

  if (count === 0) {
    dom.cardsGrid.style.display = 'none';
    dom.tableView.style.display = 'none';
    dom.noResultsState.style.display = 'block';
    dom.paginationWrapper.style.display = 'none';
    return;
  }

  dom.noResultsState.style.display = 'none';
  dom.paginationWrapper.style.display = 'flex';

  const totalPages = Math.ceil(count / state.pageSize);
  if (state.currentPage > totalPages) state.currentPage = totalPages;
  if (state.currentPage < 1) state.currentPage = 1;

  const startIdx = (state.currentPage - 1) * state.pageSize;
  const pageItems = state.filteredCases.slice(startIdx, startIdx + state.pageSize);

  if (state.viewMode === 'grid') {
    dom.cardsGrid.style.display = 'grid';
    dom.tableView.style.display = 'none';
    renderCards(pageItems);
  } else {
    dom.cardsGrid.style.display = 'none';
    dom.tableView.style.display = 'block';
    renderTable(pageItems);
  }

  renderPagination(totalPages);
}

// Render Cards
// IMAGE REQUIREMENT: 신고일자·신고유형·지역·처리상태를 카드 형태로 표시
function renderCards(items) {
  dom.cardsGrid.innerHTML = items.map(item => {
    const caseId = item['사건ID'] || '-';
    const date = item['신고일자'] || '-';
    const type = item['신고유형'] || '일반';
    const region = item['지역'] || '-';
    const status = item['처리상태'] || '접수';
    const amount = item['위반금액_만원'] ? `${Number(item['위반금액_만원']).toLocaleString()}만원` : '-';
    const action = item['조치결과'] || '-';
    const icon = typeIcons[type] || '📑';

    return `
      <article class="case-card" onclick="openCaseModal('${caseId}')" title="${caseId} 상세 보기">
        <div class="card-top-bar">
          <span class="case-id-badge">${caseId}</span>
          <!-- 처리상태 배지 -->
          <span class="status-badge status-${status}">${status}</span>
        </div>

        <div class="card-main-title">
          <span class="type-icon">${icon}</span>
          <!-- 신고유형 -->
          <span class="type-text">${type}</span>
        </div>

        <div class="card-info-rows">
          <!-- 지역 -->
          <div class="info-row">
            <span class="info-row-label">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>
              지역
            </span>
            <span class="info-row-value region-highlight">📍 ${region}</span>
          </div>

          <!-- 신고일자 -->
          <div class="info-row">
            <span class="info-row-label">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
              신고일자
            </span>
            <span class="info-row-value">${date}</span>
          </div>

          <!-- 위반금액 -->
          <div class="info-row">
            <span class="info-row-label">위반금액</span>
            <span class="info-row-value amount-highlight">${amount}</span>
          </div>

          <!-- 조치결과 -->
          <div class="info-row">
            <span class="info-row-label">조치결과</span>
            <span class="info-row-value">${action}</span>
          </div>
        </div>

        <div class="card-footer-action">
          <span class="card-detail-hint">클릭하여 세부정보 확인</span>
          <span class="card-view-btn">상세보기 &rarr;</span>
        </div>
      </article>
    `;
  }).join('');
}

// Render Table View
function renderTable(items) {
  dom.tableBody.innerHTML = items.map(item => {
    const caseId = item['사건ID'] || '-';
    const date = item['신고일자'] || '-';
    const type = item['신고유형'] || '-';
    const region = item['지역'] || '-';
    const status = item['처리상태'] || '-';
    const amount = item['위반금액_만원'] ? `${Number(item['위반금액_만원']).toLocaleString()}만원` : '-';
    const action = item['조치결과'] || '-';

    return `
      <tr onclick="openCaseModal('${caseId}')">
        <td><strong>${caseId}</strong></td>
        <td>${date}</td>
        <td><span class="badge">${type}</span></td>
        <td>📍 ${region}</td>
        <td><span class="status-badge status-${status}">${status}</span></td>
        <td class="amount-highlight">${amount}</td>
        <td>${action}</td>
        <td><button class="btn btn-outline" style="padding: 2px 8px; font-size: 0.75rem;">상세</button></td>
      </tr>
    `;
  }).join('');
}

// Render Pagination
function renderPagination(totalPages) {
  dom.pageInfoText.textContent = `${state.currentPage} / ${totalPages} 페이지 (총 ${state.filteredCases.length.toLocaleString()}건)`;

  let html = '';
  // Prev Button
  html += `
    <button class="page-btn" ${state.currentPage === 1 ? 'disabled' : ''} onclick="changePage(${state.currentPage - 1})" title="이전 페이지">
      &lsaquo;
    </button>
  `;

  // Page Numbers (Smart window around current page)
  const maxButtons = 5;
  let startPage = Math.max(1, state.currentPage - Math.floor(maxButtons / 2));
  let endPage = Math.min(totalPages, startPage + maxButtons - 1);
  if (endPage - startPage + 1 < maxButtons) {
    startPage = Math.max(1, endPage - maxButtons + 1);
  }

  if (startPage > 1) {
    html += `<button class="page-btn" onclick="changePage(1)">1</button>`;
    if (startPage > 2) html += `<span style="padding: 0 4px; color: var(--text-dim);">...</span>`;
  }

  for (let p = startPage; p <= endPage; p++) {
    html += `
      <button class="page-btn ${p === state.currentPage ? 'active' : ''}" onclick="changePage(${p})">
        ${p}
      </button>
    `;
  }

  if (endPage < totalPages) {
    if (endPage < totalPages - 1) html += `<span style="padding: 0 4px; color: var(--text-dim);">...</span>`;
    html += `<button class="page-btn" onclick="changePage(${totalPages})">${totalPages}</button>`;
  }

  // Next Button
  html += `
    <button class="page-btn" ${state.currentPage === totalPages ? 'disabled' : ''} onclick="changePage(${state.currentPage + 1})" title="다음 페이지">
      &rsaquo;
    </button>
  `;

  dom.paginationNav.innerHTML = html;
}

// Change Page Global Function
window.changePage = function(page) {
  state.currentPage = page;
  renderCurrentPage();
  document.getElementById('casesContainer').scrollIntoView({ behavior: 'smooth', block: 'start' });
};

// Case Detail Modal
window.openCaseModal = function(caseId) {
  const item = state.cases.find(c => c['사건ID'] === caseId);
  if (!item) return;

  dom.modalCaseId.textContent = `사건 상세: ${item['사건ID']}`;
  dom.modalStatusBadge.textContent = item['처리상태'] || '접수';
  dom.modalStatusBadge.className = `status-badge status-${item['처리상태']}`;

  dom.modalBody.innerHTML = `
    <table class="detail-table">
      <tbody>
        <tr>
          <th>사건번호</th>
          <td>${item['사건ID'] || '-'}</td>
        </tr>
        <tr>
          <th>신고일자</th>
          <td>${item['신고일자'] || '-'}</td>
        </tr>
        <tr>
          <th>신고유형</th>
          <td>${item['신고유형'] || '-'}</td>
        </tr>
        <tr>
          <th>지역(관할)</th>
          <td>📍 ${item['지역'] || '-'}</td>
        </tr>
        <tr>
          <th>신고자 유형</th>
          <td>${item['신고자유형'] || '-'}</td>
        </tr>
        <tr>
          <th>처리상태</th>
          <td><span class="status-badge status-${item['처리상태']}">${item['처리상태']}</span></td>
        </tr>
        <tr>
          <th>처리기간 (소요일)</th>
          <td>${item['처리기간_일'] ? `${item['처리기간_일']}일` : '진행 중 / 미등록'}</td>
        </tr>
        <tr>
          <th>위반금액</th>
          <td class="amount-highlight">${item['위반금액_만원'] ? `${Number(item['위반금액_만원']).toLocaleString()} 만원` : '해당 없음'}</td>
        </tr>
        <tr>
          <th>조치결과</th>
          <td><strong>${item['조치결과'] || '해당 없음'}</strong></td>
        </tr>
      </tbody>
    </table>
  `;

  dom.caseModal.style.display = 'flex';
};

function closeCaseModal() {
  dom.caseModal.style.display = 'none';
}

// Education Modal
function openEduModal() {
  if (!state.eduData || state.eduData.length === 0) {
    alert('교육 현황 데이터를 불러오는 중입니다. 잠시 후 다시 시도해주세요.');
    return;
  }

  const excellentCount = state.eduData.filter(d => d['청렴우수기관'] === 'Y').length;
  const rates = state.eduData.map(d => parseFloat(d['교육이수율'])).filter(r => !isNaN(r));
  const avgRate = rates.length > 0 ? (rates.reduce((a, b) => a + b, 0) / rates.length).toFixed(1) : 0;

  dom.eduStatsBar.innerHTML = `
    <div class="edu-stat-item">
      <div class="edu-stat-num">${state.eduData.length}개</div>
      <div class="edu-stat-txt">총 대상 기관수</div>
    </div>
    <div class="edu-stat-item">
      <div class="edu-stat-num">${excellentCount}개</div>
      <div class="edu-stat-txt">청렴우수기관 (Y)</div>
    </div>
    <div class="edu-stat-item">
      <div class="edu-stat-num">${avgRate}%</div>
      <div class="edu-stat-txt">전체 평균 교육이수율</div>
    </div>
  `;

  dom.eduTableBody.innerHTML = state.eduData.map(item => {
    const isGood = item['청렴우수기관'] === 'Y';
    return `
      <tr>
        <td>${item['기관코드'] || '-'}</td>
        <td><strong>${item['기관명'] || '-'}</strong></td>
        <td>${item['기관유형'] || '-'}</td>
        <td>${item['교육이수율'] ? `${item['교육이수율']}%` : '-'}</td>
        <td>${item['연간교육시간'] ? `${item['연간교육시간']}시간` : '-'}</td>
        <td>${item['교육참여자수'] ? `${Number(item['교육참여자수']).toLocaleString()}명` : '-'}</td>
        <td>${isGood ? '<span style="color: #16a34a; font-weight: 800;">⭐ 우수</span>' : '<span style="color: #94a3b8;">-</span>'}</td>
      </tr>
    `;
  }).join('');

  dom.eduModal.style.display = 'flex';
}

function closeEduModal() {
  dom.eduModal.style.display = 'none';
}

// Event Listeners
function initEventListeners() {
  // Search Keyword input
  dom.searchInput.addEventListener('input', (e) => {
    state.filters.keyword = e.target.value;
    dom.clearSearchBtn.style.display = state.filters.keyword ? 'block' : 'none';
    applyFiltersAndRender();
  });

  dom.clearSearchBtn.addEventListener('click', () => {
    dom.searchInput.value = '';
    state.filters.keyword = '';
    dom.clearSearchBtn.style.display = 'none';
    applyFiltersAndRender();
    dom.searchInput.focus();
  });

  // Type Filter
  dom.typeFilter.addEventListener('change', (e) => {
    state.filters.type = e.target.value;
    applyFiltersAndRender();
  });

  // Status Filter
  dom.statusFilter.addEventListener('change', (e) => {
    state.filters.status = e.target.value;
    updateActiveChip(state.filters.status);
    applyFiltersAndRender();
  });

  // Region Filter
  dom.regionFilter.addEventListener('change', (e) => {
    state.filters.region = e.target.value;
    applyFiltersAndRender();
  });

  // Quick Chips
  dom.quickChips.addEventListener('click', (e) => {
    const chip = e.target.closest('.chip');
    if (!chip) return;
    const status = chip.getAttribute('data-status');
    state.filters.status = status;
    dom.statusFilter.value = status;
    updateActiveChip(status);
    applyFiltersAndRender();
  });

  // Reset Filters
  function resetAllFilters() {
    state.filters = { keyword: '', type: 'ALL', status: 'ALL', region: 'ALL' };
    dom.searchInput.value = '';
    dom.clearSearchBtn.style.display = 'none';
    dom.typeFilter.value = 'ALL';
    dom.statusFilter.value = 'ALL';
    dom.regionFilter.value = 'ALL';
    updateActiveChip('ALL');
    applyFiltersAndRender();
  }

  dom.resetFiltersBtn.addEventListener('click', resetAllFilters);
  dom.emptyResetBtn.addEventListener('click', resetAllFilters);

  // Sort
  dom.sortSelect.addEventListener('change', (e) => {
    state.sort = e.target.value;
    sortCases();
    renderCurrentPage();
  });

  // Page Size
  dom.pageSizeSelect.addEventListener('change', (e) => {
    state.pageSize = parseInt(e.target.value, 10);
    state.currentPage = 1;
    renderCurrentPage();
  });

  // View Mode
  dom.viewGridBtn.addEventListener('click', () => {
    state.viewMode = 'grid';
    dom.viewGridBtn.classList.add('active');
    dom.viewTableBtn.classList.remove('active');
    renderCurrentPage();
  });

  dom.viewTableBtn.addEventListener('click', () => {
    state.viewMode = 'table';
    dom.viewTableBtn.classList.add('active');
    dom.viewGridBtn.classList.remove('active');
    renderCurrentPage();
  });

  // Modals close events
  dom.modalCloseBtn.addEventListener('click', closeCaseModal);
  dom.modalConfirmBtn.addEventListener('click', closeCaseModal);
  dom.caseModal.addEventListener('click', (e) => {
    if (e.target === dom.caseModal) closeCaseModal();
  });

  dom.eduModalBtn.addEventListener('click', openEduModal);
  dom.eduModalCloseBtn.addEventListener('click', closeEduModal);
  dom.eduModalConfirmBtn.addEventListener('click', closeEduModal);
  dom.eduModal.addEventListener('click', (e) => {
    if (e.target === dom.eduModal) closeEduModal();
  });

  // ESC key for modals
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeCaseModal();
      closeEduModal();
    }
  });

  // Dark mode toggle
  dom.themeToggleBtn.addEventListener('click', () => {
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    const nextTheme = isDark ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', nextTheme);
    localStorage.setItem('portal_theme', nextTheme);
    dom.themeToggleBtn.querySelector('.theme-icon').textContent = nextTheme === 'dark' ? '☀️' : '🌙';
  });
}

function updateActiveChip(status) {
  const chips = dom.quickChips.querySelectorAll('.chip');
  chips.forEach(chip => {
    if (chip.getAttribute('data-status') === status) {
      chip.classList.add('active');
    } else {
      chip.classList.remove('active');
    }
  });
}

// Theme initialization
function initTheme() {
  const saved = localStorage.getItem('portal_theme') || 
    (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
  document.documentElement.setAttribute('data-theme', saved);
  if (dom.themeToggleBtn) {
    dom.themeToggleBtn.querySelector('.theme-icon').textContent = saved === 'dark' ? '☀️' : '🌙';
  }
}
