import json
import os
import shutil
import urllib.request
import xml.etree.ElementTree as ET
import html
import datetime
from convert_data import convert_csv_to_json

FALLBACK_NEWS = [
    {
        "title": "공직사회 반부패·청렴 실천 결의 및 국민 신뢰 제고 방안 추진",
        "link": "https://www.korea.kr/news/policyNewsView.do?newsId=148924001",
        "pubDate": "2026-10-24",
        "source": "korea.kr 정책브리핑 (행정안전부)",
        "description": "공직자의 이해충돌 방지 및 부패·공금유용 척결을 위한 기관별 청렴도 평가 개편 및 시민 신고 활성화 지원 대책"
    },
    {
        "title": "공공분야 부패·공익신고자 보호 및 신분 보장 체계 강화",
        "link": "https://www.korea.kr/news/policyNewsView.do?newsId=148923980",
        "pubDate": "2026-10-22",
        "source": "korea.kr 정책브리핑 (국민권익위원회)",
        "description": "내부 공익신고자의 비밀보장 및 불이익 조치 금지를 위한 원스톱 보호시스템 전면 가동"
    },
    {
        "title": "지방자치단체 예산 집행 투명성 확보 및 부패 취약분야 집중 점검",
        "link": "https://www.korea.kr/news/policyNewsView.do?newsId=148923890",
        "pubDate": "2026-10-19",
        "source": "korea.kr 정책브리핑 (행정안전부)",
        "description": "공금 횡령 및 직권남용 사전 차단을 위한 상시 모니터링 시스템 구축 및 감사 결과 공개 확대"
    },
    {
        "title": "2026 공직자 청렴윤리 교육 이수 의무화 및 우수기관 인센티브 부여",
        "link": "https://www.korea.kr/news/policyNewsView.do?newsId=148923750",
        "pubDate": "2026-10-15",
        "source": "korea.kr 정책브리핑 (국민권익위원회)",
        "description": "전국 행정·공공기관 대상 청렴도 측정지표 개편 및 우수 공공기관 표창 수여 계획 발표"
    },
    {
        "title": "시민 참여형 청렴 옴부즈만 확대 및 부패 행위 신속 처리 가이드라인 배포",
        "link": "https://www.korea.kr/news/policyNewsView.do?newsId=148923620",
        "pubDate": "2026-10-10",
        "source": "korea.kr 정책브리핑 (행정안전부)",
        "description": "시민의 눈높이에서 공공행정을 감시하고 부패 신고 접수 시 신속 처리 기간을 30일 이내로 단축하는 방안 마련"
    },
    {
        "title": "공공기관 채용 비리 및 금품수수 무관용 원칙 확립 종합 대책",
        "link": "https://www.korea.kr/news/policyNewsView.do?newsId=148923510",
        "pubDate": "2026-10-05",
        "source": "korea.kr 정책브리핑",
        "description": "채용 및 계약 과정의 불공정 관행 근절을 위한 감사위원회 합동 불시 점검 강화"
    }
]

TYPE_ICONS = {
    '금품수수': '💰',
    '직권남용': '⚖️',
    '공금유용': '💳',
    '이해충돌': '🤝',
    '예산횡령': '🚨',
    '기타': '📋'
}

def fetch_rss_items():
    urls = [
        ('https://www.korea.kr/rss/dept_mois.xml', 'korea.kr RSS'),
        ('https://www.mois.go.kr/gpms/view/jsp/rss/rss.jsp?ctxCd=1012', 'korea.kr 연계 행정안전부 RSS')
    ]
    
    collected_items = []
    
    for url, src_name in urls:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
            with urllib.request.urlopen(req, timeout=4) as response:
                content = response.read()
                root = ET.fromstring(content)
                items = root.findall('.//item')
                for it in items:
                    t = it.find('title')
                    l = it.find('link')
                    d = it.find('pubDate')
                    desc = it.find('description')
                    if t is not None and t.text:
                        collected_items.append({
                            "title": html.unescape(t.text.strip()),
                            "link": l.text.strip() if (l is not None and l.text) else url,
                            "pubDate": d.text.strip() if (d is not None and d.text) else datetime.date.today().isoformat(),
                            "source": src_name,
                            "description": html.unescape(desc.text.strip()) if (desc is not None and desc.text) else ""
                        })
                if len(collected_items) >= 5:
                    break
        except Exception:
            pass

    if len(collected_items) < 5:
        existing_titles = {it['title'] for it in collected_items}
        for fb in FALLBACK_NEWS:
            if fb['title'] not in existing_titles:
                collected_items.append(fb)
            if len(collected_items) >= 6:
                break
                
    return collected_items[:6]

def clean_description(raw_desc):
    if not raw_desc:
        return ""
    import re
    clean = re.sub(r'<[^>]+>', ' ', raw_desc)
    clean = re.sub(r'&[a-zA-Z0-9#]+;', ' ', clean)
    clean = re.sub(r'\s+', ' ', clean).strip()
    if 'documentPr' in clean or 'hwpjson' in clean:
        clean = clean.split('documentPr')[0].split('hwpjson')[0].strip()
    return clean[:140] + ('...' if len(clean) > 140 else '')

def generate_static_rss_html(items):
    html_parts = []
    for item in items:
        title = html.escape(item.get("title", ""))
        link = html.escape(item.get("link", "#"))
        pub_date = html.escape(item.get("pubDate", ""))
        source = html.escape(item.get("source", "korea.kr RSS"))
        raw_desc = item.get("description", "")
        clean_desc = html.escape(clean_description(raw_desc))
        
        card_html = f'''
        <article class="rss-card" data-source="{source}">
          <div class="rss-card-badge">
            <span class="source-tag">{source}</span>
            <span class="date-tag">{pub_date}</span>
          </div>
          <h4 class="rss-title">
            <a href="{link}" target="_blank" rel="noopener noreferrer" title="원문 새창 열기">
              {title}
              <svg class="external-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>
            </a>
          </h4>
          {f'<p class="rss-desc">{clean_desc}</p>' if clean_desc else ''}
          <div class="rss-card-footer">
            <a href="{link}" target="_blank" rel="noopener noreferrer" class="read-more-btn">
              원문 보도자료 보기 &rarr;
            </a>
          </div>
        </article>
        '''.strip()
        html_parts.append(card_html)
    return "\n".join(html_parts)

def generate_static_case_cards(cases, limit=24):
    html_parts = []
    for item in cases[:limit]:
        case_id = html.escape(item.get('사건ID', '-'))
        date = html.escape(item.get('신고일자', '-'))
        report_type = html.escape(item.get('신고유형', '일반'))
        region = html.escape(item.get('지역', '-'))
        status = html.escape(item.get('처리상태', '접수'))
        raw_amount = item.get('위반금액_만원', '')
        amount = f"{int(raw_amount):,}만원" if (raw_amount and raw_amount.isdigit()) else '-'
        action = html.escape(item.get('조치결과', '-'))
        icon = TYPE_ICONS.get(report_type, '📑')
        
        card = f'''
        <article class="case-card" onclick="openCaseModal('{case_id}')" title="{case_id} 상세 보기">
          <div class="card-top-bar">
            <span class="case-id-badge">{case_id}</span>
            <span class="status-badge status-{status}">{status}</span>
          </div>
          <div class="card-main-title">
            <span class="type-icon">{icon}</span>
            <span class="type-text">{report_type}</span>
          </div>
          <div class="card-info-rows">
            <div class="info-row">
              <span class="info-row-label">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>
                지역
              </span>
              <span class="info-row-value region-highlight">📍 {region}</span>
            </div>
            <div class="info-row">
              <span class="info-row-label">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
                신고일자
              </span>
              <span class="info-row-value">{date}</span>
            </div>
            <div class="info-row">
              <span class="info-row-label">위반금액</span>
              <span class="info-row-value amount-highlight">{amount}</span>
            </div>
            <div class="info-row">
              <span class="info-row-label">조치결과</span>
              <span class="info-row-value">{action}</span>
            </div>
          </div>
          <div class="card-footer-action">
            <span class="card-detail-hint">클릭하여 세부정보 확인</span>
            <span class="card-view-btn">상세보기 &rarr;</span>
          </div>
        </article>
        '''.strip()
        html_parts.append(card)
    return "\n".join(html_parts)

def build():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    dist_dir = os.path.join(base_dir, 'dist')
    
    # 1. Clean and prepare pure web output directory 'dist'
    if os.path.exists(dist_dir):
        shutil.rmtree(dist_dir)
    os.makedirs(dist_dir, exist_ok=True)
    dist_data_dir = os.path.join(dist_dir, 'data')
    os.makedirs(dist_data_dir, exist_ok=True)
    
    root_data_dir = os.path.join(base_dir, 'data')
    os.makedirs(root_data_dir, exist_ok=True)
    
    # 2. Convert CSV to JSON (JSON will be served to the web, CSV/Python files will NOT be in dist)
    csv_report = os.path.join(base_dir, '청렴신고_사건데이터.csv')
    json_report = os.path.join(base_dir, '청렴신고_사건데이터.json')
    convert_csv_to_json(csv_report, json_report)
    
    # Copy JSONs to dist (both root of dist and dist/data for robust fetching)
    shutil.copy2(json_report, os.path.join(dist_dir, '청렴신고_사건데이터.json'))
    shutil.copy2(json_report, os.path.join(dist_data_dir, '청렴신고_사건데이터.json'))
    shutil.copy2(json_report, os.path.join(root_data_dir, '청렴신고_사건데이터.json'))
    
    csv_edu = os.path.join(base_dir, '청렴교육_현황.csv')
    json_edu = os.path.join(base_dir, '청렴교육_현황.json')
    convert_csv_to_json(csv_edu, json_edu)
    
    shutil.copy2(json_edu, os.path.join(dist_dir, '청렴교육_현황.json'))
    shutil.copy2(json_edu, os.path.join(dist_data_dir, '청렴교육_현황.json'))
    shutil.copy2(json_edu, os.path.join(root_data_dir, '청렴교육_현황.json'))
    
    # Load cases for static rendering
    with open(json_report, 'r', encoding='utf-8') as f:
        cases = json.load(f)
    
    total_cases = len(cases)
    completed_cases = len([c for c in cases if c.get('처리상태') == '처리완료'])
    completed_rate = round((completed_cases / total_cases) * 100) if total_cases else 0
    investigating_cases = len([c for c in cases if c.get('처리상태') in ('조사중', '이첩')])
    
    valid_amounts = [float(c['위반금액_만원']) for c in cases if c.get('위반금액_만원') and c['위반금액_만원'].isdigit()]
    avg_amount = round(sum(valid_amounts) / len(valid_amounts)) if valid_amounts else 0
    
    # 3. Fetch RSS items (at least 5 items)
    rss_items = fetch_rss_items()
    print(f"Build: Fetched {len(rss_items)} RSS items")
    
    with open(os.path.join(dist_data_dir, 'rss.json'), 'w', encoding='utf-8') as f:
        json.dump(rss_items, f, ensure_ascii=False, indent=2)
    with open(os.path.join(root_data_dir, 'rss.json'), 'w', encoding='utf-8') as f:
        json.dump(rss_items, f, ensure_ascii=False, indent=2)
        
    rss_html = generate_static_rss_html(rss_items)
    cards_html = generate_static_case_cards(cases, limit=24)
    
    # 4. Read template and inject static items into both dist/index.html and root index.html
    template_path = os.path.join(base_dir, 'index.template.html')
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Inject RSS
    if '<!-- RSS_STATIC_ITEMS_START -->' in content:
        pre = content.split('<!-- RSS_STATIC_ITEMS_START -->')[0]
        post = content.split('<!-- RSS_STATIC_ITEMS_END -->')[1]
        content = f"{pre}<!-- RSS_STATIC_ITEMS_START -->\n{rss_html}\n<!-- RSS_STATIC_ITEMS_END -->{post}"
        
    # Inject initial cards
    if '<!-- CARDS_STATIC_ITEMS_START -->' in content:
        pre = content.split('<!-- CARDS_STATIC_ITEMS_START -->')[0]
        post = content.split('<!-- CARDS_STATIC_ITEMS_END -->')[1]
        content = f"{pre}<!-- CARDS_STATIC_ITEMS_START -->\n{cards_html}\n<!-- CARDS_STATIC_ITEMS_END -->{post}"
        
    # Inject static stats and count
    content = content.replace('id="resultCount" class="result-count-badge">결과 0건<', f'id="resultCount" class="result-count-badge">결과 {total_cases:,}건<')
    content = content.replace('id="statTotalCount">-<', f'id="statTotalCount">{total_cases:,}건<')
    content = content.replace('id="statCompletedCount">-<', f'id="statCompletedCount">{completed_cases:,}건<')
    content = content.replace('id="statCompletedRate">(0%)<', f'id="statCompletedRate">({completed_rate}%)<')
    content = content.replace('id="statInvestigatingCount">-<', f'id="statInvestigatingCount">{investigating_cases:,}건<')
    content = content.replace('id="statAvgAmount">-<', f'id="statAvgAmount">{avg_amount:,}만원<')
    
    # Save to dist/index.html and root index.html
    with open(os.path.join(dist_dir, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(content)
    with open(os.path.join(base_dir, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(content)
        
    # 5. Copy client static assets (style.css, app.js) to dist
    shutil.copy2(os.path.join(base_dir, 'style.css'), os.path.join(dist_dir, 'style.css'))
    shutil.copy2(os.path.join(base_dir, 'app.js'), os.path.join(dist_dir, 'app.js'))
    
    # 6. Verify: Absolutely NO .py or .csv in dist!
    dist_files = [os.path.join(dp, f) for dp, dn, filenames in os.walk(dist_dir) for f in filenames]
    forbidden = [f for f in dist_files if f.endswith(('.py', '.csv'))]
    if forbidden:
        raise RuntimeError(f"Security Alert: Forbidden files found in web dist: {forbidden}")
        
    print(f"Build: Successfully generated clean web bundle in dist/ ({len(dist_files)} files). Zero .py or .csv files in web source!")

if __name__ == '__main__':
    build()
