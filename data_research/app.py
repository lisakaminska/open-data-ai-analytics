import os
import sqlite3
import json
import pandas as pd
import numpy as np
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
    raise RuntimeError(f"DB not found: {path}")


def conduct_research():
    logger.info("=== data_research: starting ===")
    wait_for_db(DB_PATH)
    os.makedirs(REPORTS_PATH, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql('SELECT * FROM persons', conn)
    conn.close()

    numeric_cols = ['width', 'height', 'size_kb', 'aspect_ratio', 'pixels']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    report = {}

    # Basic statistics
    stats = df[numeric_cols].describe().round(2)
    report["basic_statistics"] = stats.to_dict()

    # Format distribution
    report["format_distribution"] = df['format'].value_counts().to_dict()

    # Aspect ratio analysis
    report["aspect_ratio_analysis"] = {
        "mean":   round(float(df['aspect_ratio'].mean()), 4),
        "std":    round(float(df['aspect_ratio'].std()),  4),
        "portrait_34_pct": round(float((df['aspect_ratio'].between(0.74, 0.76)).sum() / len(df) * 100), 2)
    }

    # Resolution analysis
    report["resolution_analysis"] = {
        "mean_pixels":   int(df['pixels'].mean()),
        "median_pixels": int(df['pixels'].median()),
        "low_res_count": int((df['pixels'] < 200*200).sum()),
        "low_res_pct":   round(float((df['pixels'] < 200*200).sum() / len(df) * 100), 2),
        "high_res_count": int((df['pixels'] > 1_000_000).sum())
    }

    # File size analysis
    report["file_size_analysis"] = {
        "mean_kb":   round(float(df['size_kb'].mean()), 2),
        "median_kb": round(float(df['size_kb'].median()), 2),
        "max_kb":    round(float(df['size_kb'].max()), 2),
        "min_kb":    round(float(df['size_kb'].min()), 2)
    }

    # Top 5 largest photos
    top5 = df.nlargest(5, 'pixels')[['id', 'pixels', 'width', 'height', 'format']].copy()
    report["top5_largest"] = top5.to_dict(orient='records')

    # AI readiness
    ai_ready = df[(df['pixels'] >= 200*200) & (df['format'].isin(['JPEG', 'PNG']))]
    report["ai_readiness"] = {
        "ai_ready_count": int(len(ai_ready)),
        "ai_ready_pct":   round(float(len(ai_ready) / len(df) * 100), 2)
    }

    # Total
    report["total_records"] = int(len(df))

    # Save JSON report
    report_path = os.path.join(REPORTS_PATH, 'research_report.json')
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2, default=str)
    logger.info(f"Research report saved to {report_path}")

    # Save to DB
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS research_report (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    conn.execute('DELETE FROM research_report')
    for k, v in report.items():
        conn.execute('INSERT INTO research_report VALUES (?, ?)',
                     (k, json.dumps(v, ensure_ascii=False, default=str)))
    conn.commit()
    conn.close()
    logger.info("Research results saved to DB")
    logger.info("=== data_research: done ===")


if __name__ == '__main__':
    conduct_research()
