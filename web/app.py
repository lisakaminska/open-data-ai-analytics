import os
import sqlite3
import json
import pandas as pd
from flask import Flask, render_template, jsonify
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

DB_PATH    = os.getenv('DB_PATH',    '/db/analytics.db')
PLOTS_PATH = os.getenv('PLOTS_PATH', '/plots')


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def db_ready():
    return os.path.exists(DB_PATH)


@app.route('/')
def index():
    ready = db_ready()
    return render_template('index.html', db_ready=ready)


@app.route('/data')
def data_page():
    if not db_ready():
        return render_template('error.html', message="База даних ще не готова. Зачекайте кілька секунд.")
    conn = get_db()
    rows = conn.execute('SELECT * FROM persons LIMIT 50').fetchall()
    conn.close()
    return render_template('data.html', rows=rows)


@app.route('/quality')
def quality_page():
    if not db_ready():
        return render_template('error.html', message="База даних ще не готова.")
    try:
        conn = get_db()
        rows = conn.execute('SELECT key, value FROM quality_report').fetchall()
        conn.close()
        report = {r['key']: json.loads(r['value']) for r in rows}
    except Exception as e:
        report = {"error": str(e)}
    return render_template('quality.html', report=report)


@app.route('/research')
def research_page():
    if not db_ready():
        return render_template('error.html', message="База даних ще не готова.")
    try:
        conn = get_db()
        rows = conn.execute('SELECT key, value FROM research_report').fetchall()
        conn.close()
        report = {r['key']: json.loads(r['value']) for r in rows}
    except Exception as e:
        report = {"error": str(e)}
    return render_template('research.html', report=report)


@app.route('/visualizations')
def visualizations_page():
    plots = []
    if os.path.exists(PLOTS_PATH):
        for f in os.listdir(PLOTS_PATH):
            if f.endswith('.png'):
                plots.append(f)
    return render_template('visualizations.html', plots=plots)


@app.route('/plots/<filename>')
def serve_plot(filename):
    from flask import send_from_directory
    return send_from_directory(PLOTS_PATH, filename)


@app.route('/healthz')
def health():
    return jsonify({"status": "ok", "db_ready": db_ready()})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
