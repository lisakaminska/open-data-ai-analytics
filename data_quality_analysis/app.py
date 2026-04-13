import os
import sqlite3
import json
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DB_PATH      = os.getenv('DB_PATH',      '/db/analytics.db')
REPORTS_PATH = os.getenv('REPORTS_PATH', '/reports')


def wait_for_db(path, retries=10, delay=3):
    import time
    for i in range(retries):
        if os.path.exists(path):
            return True
        logger.info(f"Waiting for DB ({i+1}/{retries})...")
        time.sleep(delay)
    raise RuntimeError(f"DB not found after {retries} retries: {path}")


def analyze_quality():
    logger.info("=== data_quality_analysis: starting ===")
    wait_for_db(DB_PATH)
    os.makedirs(REPORTS_PATH, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql('SELECT * FROM persons', conn)
    conn.close()

    total = len(df)
    report = {
        "total_records": total,
        "missing_values": {},
        "duplicates": {},
        "type_checks": {},
        "value_checks": {}
    }

    # Missing values
    for col in df.columns:
        missing = int(df[col].isna().sum())
        report["missing_values"][col] = missing
    logger.info(f"Missing values: {report['missing_values']}")

    # Duplicates by ID
    dup_ids = int(df.duplicated(subset=['id']).sum())
    report["duplicates"]["by_id"] = dup_ids
    report["duplicates"]["fully_duplicate_rows"] = int(df.duplicated().sum())
    logger.info(f"Duplicates by ID: {dup_ids}")

    # Type checks
    report["type_checks"]["width_numeric"]  = bool(pd.to_numeric(df['width'],  errors='coerce').notna().all())
    report["type_checks"]["height_numeric"] = bool(pd.to_numeric(df['height'], errors='coerce').notna().all())
    report["type_checks"]["pixels_numeric"] = bool(pd.to_numeric(df['pixels'], errors='coerce').notna().all())

    # Value checks
    valid_formats = {'JPEG', 'PNG', 'BMP', 'GIF', 'MPO'}
    invalid_formats = df[~df['format'].isin(valid_formats)]
    report["value_checks"]["invalid_format_count"] = int(len(invalid_formats))
    report["value_checks"]["known_formats"] = df['format'].value_counts().to_dict()

    low_res = df[df['pixels'] < 200 * 200]
    report["value_checks"]["low_resolution_count"] = int(len(low_res))
    report["value_checks"]["low_resolution_pct"]   = round(len(low_res) / total * 100, 2)

    neg_dims = df[(df['width'] <= 0) | (df['height'] <= 0)]
    report["value_checks"]["negative_dimensions"] = int(len(neg_dims))

    # Save report
    report_path = os.path.join(REPORTS_PATH, 'quality_report.json')
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    logger.info(f"Quality report saved to {report_path}")

    # Save to DB
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS quality_report (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    conn.execute('DELETE FROM quality_report')
    for k, v in report.items():
        conn.execute('INSERT INTO quality_report VALUES (?, ?)', (k, json.dumps(v, ensure_ascii=False)))
    conn.commit()
    conn.close()
    logger.info("Quality results saved to DB")
    logger.info("=== data_quality_analysis: done ===")


if __name__ == '__main__':
    analyze_quality()
