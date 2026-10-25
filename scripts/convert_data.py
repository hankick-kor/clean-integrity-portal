import csv
import json
import os

def convert_csv_to_json(csv_path, json_path):
    # Try utf-8-sig, utf-8, cp949
    encodings = ['utf-8-sig', 'utf-8', 'cp949']
    rows = None
    for enc in encodings:
        try:
            with open(csv_path, 'r', encoding=enc) as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                print(f"Successfully read {csv_path} with {enc}, count: {len(rows)}")
                break
        except Exception:
            continue
    
    if rows is None:
        raise ValueError(f"Failed to read {csv_path}")

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
    print(f"Saved {json_path}")

if __name__ == '__main__':
    convert_csv_to_json('청렴신고_사건데이터.csv', '청렴신고_사건데이터.json')
    convert_csv_to_json('청렴교육_현황.csv', '청렴교육_현황.json')
