import os
import sqlite3
import json
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DB_PATH    = os.getenv('DB_PATH',    '/db/analytics.db')
PLOTS_PATH = os.getenv('PLOTS_PATH', '/plots')


def wait_for_db(path, retries=15, delay=3):
    import time
    for i in range(retries):
        if os.path.exists(path):
            return True
        logger.info(f"Waiting for DB ({i+1}/{retries})...")
        time.sleep(delay)
    raise RuntimeError(f"DB not found: {path}")


def build_charts():
    logger.info("=== visualization: starting ===")
    wait_for_db(DB_PATH)
    os.makedirs(PLOTS_PATH, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql('SELECT * FROM persons', conn)
    conn.close()

    numeric_cols = ['width', 'height', 'size_kb', 'aspect_ratio', 'pixels']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    plt.style.use('seaborn-v0_8-whitegrid')
    fig = plt.figure(figsize=(16, 12))
    fig.suptitle('Аналіз датасету МВС: Особи у розшуку', fontsize=16, fontweight='bold', y=0.98)
    gs = gridspec.GridSpec(2, 2, figure=fig, hspace=0.4, wspace=0.35)

    # 1 — Aspect Ratio Histogram
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.hist(df['aspect_ratio'].dropna(), bins=20, color='#6C63FF', edgecolor='white', alpha=0.85)
    ax1.axvline(x=0.75, color='red', linestyle='--', linewidth=2, label='Портрет 3:4')
    ax1.set_title('Розподіл співвідношення сторін (Aspect Ratio)', fontsize=11)
    ax1.set_xlabel('aspect_ratio')
    ax1.set_ylabel('Count')
    ax1.legend()
    logger.info("Chart 1: Aspect Ratio histogram done")

    # 2 — Width vs Height scatter
    ax2 = fig.add_subplot(gs[0, 1])
    colors = {'JPEG': '#FF6B6B', 'PNG': '#4ECDC4', 'BMP': '#45B7D1', 'GIF': '#96CEB4', 'Other': '#FFEAA7'}
    for fmt, grp in df.groupby('format'):
        color = colors.get(fmt, colors['Other'])
        ax2.scatter(grp['width'], grp['height'], label=fmt, color=color, alpha=0.75, s=60)
    ax2.set_title('Розподіл роздільної здатності (Width vs Height)', fontsize=11)
    ax2.set_xlabel('width (px)')
    ax2.set_ylabel('height (px)')
    ax2.legend(title='format', fontsize=8)
    logger.info("Chart 2: Scatter plot done")

    # 3 — File size boxplot by format
    ax3 = fig.add_subplot(gs[1, 0])
    formats = df['format'].unique().tolist()
    data_to_plot = [df[df['format'] == fmt]['size_kb'].dropna().values for fmt in formats]
    bp = ax3.boxplot(data_to_plot, labels=formats, patch_artist=True)
    box_colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7']
    for patch, color in zip(bp['boxes'], box_colors):
        patch.set_facecolor(color)
    ax3.set_title('Вага файлів за форматами (KB)', fontsize=11)
    ax3.set_xlabel('format')
    ax3.set_ylabel('size_kb')
    ax3.set_yscale('log')
    logger.info("Chart 3: Boxplot done")

    # 4 — Top 10 largest photos bar chart
    ax4 = fig.add_subplot(gs[1, 1])
    top10 = df.nlargest(10, 'pixels')[['id', 'pixels']].copy()
    top10['id_str'] = top10['id'].astype(str)
    bars = ax4.barh(top10['id_str'], top10['pixels'] / 1000, color='#6C63FF', alpha=0.8)
    ax4.set_title('Топ-10 найбільших фото (за пікселями)', fontsize=11)
    ax4.set_xlabel('Мегапікселі (тис. пікс.)')
    ax4.set_ylabel('ID')
    logger.info("Chart 4: Bar chart done")

    # Save
    chart_path = os.path.join(PLOTS_PATH, 'advanced_analytics.png')
    plt.savefig(chart_path, dpi=120, bbox_inches='tight', facecolor='white')
    plt.close()
    logger.info(f"Chart saved to {chart_path}")

    # Save format pie chart separately
    fig2, ax = plt.subplots(figsize=(7, 7))
    fmt_counts = df['format'].value_counts()
    ax.pie(fmt_counts.values, labels=fmt_counts.index, autopct='%1.1f%%',
           colors=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7'],
           startangle=90)
    ax.set_title('Розподіл форматів зображень', fontsize=14, fontweight='bold')
    pie_path = os.path.join(PLOTS_PATH, 'format_distribution.png')
    plt.savefig(pie_path, dpi=120, bbox_inches='tight', facecolor='white')
    plt.close()
    logger.info(f"Pie chart saved to {pie_path}")

    logger.info("=== visualization: done ===")


if __name__ == '__main__':
    build_charts()
