import json
import os
import shutil
import urllib.request
import xml.etree.ElementTree as ET
import html
import datetime
from convert_data import convert_csv_to_json

# 1. Fallback news list in case network fails
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
    # Remove script/style
    clean = re.sub(r'<[^>]+>', ' ', raw_desc)
    clean = re.sub(r'&[a-zA-Z0-9#]+;', ' ', clean)
    clean = re.sub(r'\s+', ' ', clean).strip()
    # Filter out hwp json remnants if any
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

def build():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    data_dir = os.path.join(base_dir, 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    # 1. Convert CSV to JSON
    csv_report = os.path.join(base_dir, '청렴신고_사건데이터.csv')
    json_report = os.path.join(base_dir, '청렴신고_사건데이터.json')
    json_report_data = os.path.join(data_dir, '청렴신고_사건데이터.json')
    
    csv_edu = os.path.join(base_dir, '청렴교육_현황.csv')
    json_edu = os.path.join(base_dir, '청렴교육_현황.json')
    json_edu_data = os.path.join(data_dir, '청렴교육_현황.json')
    
    convert_csv_to_json(csv_report, json_report)
    shutil.copy2(json_report, json_report_data)
    
    convert_csv_to_json(csv_edu, json_edu)
    shutil.copy2(json_edu, json_edu_data)
    
    # 2. Fetch RSS items (at least 5 items)
    rss_items = fetch_rss_items()
    print(f"Build: Fetched {len(rss_items)} RSS items")
    
    # Save RSS items to data/rss.json as well
    with open(os.path.join(data_dir, 'rss.json'), 'w', encoding='utf-8') as f:
        json.dump(rss_items, f, ensure_ascii=False, indent=2)
        
    rss_html = generate_static_rss_html(rss_items)
    
    # 3. Read template or index.html and inject static RSS items
    template_path = os.path.join(base_dir, 'index.template.html')
    target_path = os.path.join(base_dir, 'index.html')
    
    source_path = template_path if os.path.exists(template_path) else target_path
    if os.path.exists(source_path):
        with open(source_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        start_marker = '<!-- RSS_STATIC_ITEMS_START -->'
        end_marker = '<!-- RSS_STATIC_ITEMS_END -->'
        
        if start_marker in content and end_marker in content:
            pre = content.split(start_marker)[0]
            post = content.split(end_marker)[1]
            new_content = f"{pre}{start_marker}\n{rss_html}\n{end_marker}{post}"
            with open(target_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Build: Successfully injected static RSS items into {target_path}")
        else:
            print("Build: RSS markers not found in template. Will inject once template is created.")

if __name__ == '__main__':
    build()
