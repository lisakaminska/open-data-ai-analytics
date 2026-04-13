import os
import sqlite3
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

CSV_PATH = os.getenv('CSV_PATH', '/data/dataset.csv')
DB_PATH  = os.getenv('DB_PATH',  '/db/analytics.db')


def load_data():
    logger.info("=== data_load: starting ===")
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    if not os.path.exists(CSV_PATH):
        logger.error(f"CSV not found: {CSV_PATH}")
        raise FileNotFoundError(CSV_PATH)

    df = pd.read_csv(CSV_PATH)
    logger.info(f"Read {len(df)} rows from {CSV_PATH}")

    conn = sqlite3.connect(DB_PATH)

    # Create persons table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS persons (
            id           INTEGER,
            last_name    TEXT,
            first_name   TEXT,
            middle_name  TEXT,
            birth_date   TEXT,
            format       TEXT,
            width        INTEGER,
            height       INTEGER,
            size_kb      REAL,
            aspect_ratio REAL,
            pixels       INTEGER
        )
    ''')
    conn.execute('DELETE FROM persons')
    conn.commit()

    df.to_sql('persons', conn, if_exists='replace', index=False)
    count = pd.read_sql('SELECT COUNT(*) as cnt FROM persons', conn)['cnt'][0]
    logger.info(f"Loaded {count} rows into DB at {DB_PATH}")

    conn.close()
    logger.info("=== data_load: done ===")


if __name__ == '__main__':
    load_data()
