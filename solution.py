"""
청렴 신고 사건 및 청렴 교육 현황 분석 자동화 도구
- 표준 라이브러리(csv, pathlib, sys 등)만 사용
- 청렴신고_사건데이터.csv, 청렴교육_현황.csv 분석
- 콘솔 출력 및 결과_요약.csv 생성
"""

import sys
import csv
from pathlib import Path
from collections import Counter, defaultdict

# Windows 콘솔 한글 인코딩 대응
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


def read_csv_safely(file_path: Path):
    """CSV 파일을 다양한 인코딩(utf-8-sig, utf-8, cp949)으로 안전하게 읽습니다."""
    encodings = ['utf-8-sig', 'utf-8', 'cp949']
    for enc in encodings:
        try:
            with open(file_path, 'r', encoding=enc) as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                return rows
        except Exception:
            continue
    raise FileNotFoundError(f"파일을 읽을 수 없습니다: {file_path}")


def analyze_data():
    base_dir = Path(__file__).resolve().parent
    report_csv_path = base_dir / '청렴신고_사건데이터.csv'
    edu_csv_path = base_dir / '청렴교육_현황.csv'
    output_csv_path = base_dir / '결과_요약.csv'

    # 1. 청렴신고_사건데이터 분석
    reports = read_csv_safely(report_csv_path)

    # 1-1. 총 신고 사건 수 (정수)
    total_cases = len(reports)

    # 1-2. 처리 완료된 사건 수 (정수, 처리상태 == "처리완료")
    completed_cases = sum(1 for r in reports if r.get('처리상태') == '처리완료')

    # 1-3. 평균 처리기간 (정수, 처리기간_일 결측치 제외 후 평균 반올림)
    duration_values = []
    for r in reports:
        raw_val = r.get('처리기간_일', '')
        if raw_val is not None:
            val_str = str(raw_val).strip()
            if val_str:
                try:
                    duration_values.append(float(val_str))
                except ValueError:
                    pass

    if duration_values:
        # 반올림하여 정수 변환
        avg_duration = round(sum(duration_values) / len(duration_values))
    else:
        avg_duration = 0

    # 1-4. 신고유형별 사건 수 (표 형태)
    type_counter = Counter(r.get('신고유형', '기타').strip() for r in reports if r.get('신고유형'))
    # 빈도순 정렬
    type_counts = sorted(type_counter.items(), key=lambda x: x[1], reverse=True)

    # 2. 청렴교육_현황 분석
    edus = read_csv_safely(edu_csv_path)

    # 2-1. 기관유형별 평균 이수율 (표 형태, 교육이수율 결측치 제외)
    edu_rates_by_type = defaultdict(list)
    for e in edus:
        org_type = (e.get('기관유형') or '').strip()
        raw_rate = e.get('교육이수율', '')
        if org_type and raw_rate is not None:
            rate_str = str(raw_rate).strip()
            if rate_str:
                try:
                    edu_rates_by_type[org_type].append(float(rate_str))
                except ValueError:
                    pass

    avg_edu_rates = []
    for org_type, rates in edu_rates_by_type.items():
        if rates:
            avg_rate = round(sum(rates) / len(rates), 2)
            avg_edu_rates.append((org_type, avg_rate, len(rates)))

    # 평균 이수율 높은 순 정렬
    avg_edu_rates.sort(key=lambda x: x[1], reverse=True)

    # 3. 콘솔 출력 (요구된 형식 준수)
    print(f"[OK] 신고 {total_cases}건 분석 -> {output_csv_path.name}")
    print(f"  총 사건: {total_cases}건 / 처리 완료: {completed_cases}건 / 평균 처리: {avg_duration}일\n")

    print("[신고유형별 사건 수]")
    print(f"{'신고유형':<14} {'사건 수':>8}")
    print("-" * 25)
    for report_type, count in type_counts:
        print(f"{report_type:<14} {count:>7}건")
    print("-" * 25)
    print(f"{'합계':<14} {total_cases:>7}건\n")

    print("[기관유형별 평균 이수율]")
    print(f"{'기관유형':<14} {'평균 이수율':>12} {'대상 기관':>10}")
    print("-" * 40)
    for org_type, avg_rate, org_count in avg_edu_rates:
        print(f"{org_type:<14} {avg_rate:>11.2f}% {org_count:>8}개")
    print("-" * 40)

    # 4. 결과_요약.csv 파일 생성 (utf-8-sig 인코딩으로 엑셀 호환 보장)
    with open(output_csv_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)

        # 섹션 1: 주요 요약 지표
        writer.writerow(["[1. 주요 요약 지표]"])
        writer.writerow(["항목", "출력값", "단위"])
        writer.writerow(["총 신고 사건 수", total_cases, "건"])
        writer.writerow(["처리 완료된 사건 수", completed_cases, "건"])
        writer.writerow(["평균 처리기간", avg_duration, "일"])
        writer.writerow([])

        # 섹션 2: 신고유형별 사건 수
        writer.writerow(["[2. 신고유형별 사건 수]"])
        writer.writerow(["신고유형", "사건 수(건)"])
        for report_type, count in type_counts:
            writer.writerow([report_type, count])
        writer.writerow(["합계", total_cases])
        writer.writerow([])

        # 섹션 3: 기관유형별 평균 이수율
        writer.writerow(["[3. 기관유형별 평균 이수율]"])
        writer.writerow(["기관유형", "평균 이수율(%)", "대상 기관수(개)"])
        for org_type, avg_rate, org_count in avg_edu_rates:
            writer.writerow([org_type, avg_rate, org_count])

    return output_csv_path


if __name__ == '__main__':
    analyze_data()
