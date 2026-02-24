import pandas as pd
import json
import matplotlib.pyplot as plt
import seaborn as sns
from PIL import Image
import base64
import io

def create_advanced_visualizations(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        df = pd.DataFrame(data)

        def get_img_metrics(b64):
            try:
                img_data = base64.b64decode(b64)
                img = Image.open(io.BytesIO(img_data))
                w, h = img.size
                return w, h, w / h
            except:
                return None, None, None

        df[['width', 'height', 'aspect_ratio']] = pd.DataFrame(
            df['PHOTOIDBASE64ENCODE'].apply(get_img_metrics).tolist(), index=df.index
        )
        df['size_kb'] = df['PHOTOIDBASE64ENCODE'].str.len() * 0.75 / 1024

        df['format'] = df['PHOTOIDBASE64ENCODE'].apply(
            lambda x: 'PNG' if 'iVBORw' in x[:10] else ('JPEG' if '/9j/' in x[:10] else 'Other')
        )

        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        plt.subplots_adjust(hspace=0.3)

        # 1: Співвідношення сторін
        sns.histplot(df['aspect_ratio'].dropna(), bins=50, ax=axes[0, 0], color='purple')
        axes[0, 0].set_title('Розподіл співвідношення сторін (Aspect Ratio)')
        axes[0, 0].axvline(0.75, color='red', linestyle='--', label='Портрет 3:4')
        axes[0, 0].legend()

        # 2: Співвідношення Ширини та Висоти
        sns.scatterplot(data=df, x='width', y='height', hue='format', alpha=0.5, ax=axes[0, 1])
        axes[0, 1].set_title('Розподіл роздільної здатності (Width vs Height)')

        # 3: Вага файлу в залежності від формату
        # Показує аномально важкі файли
        sns.boxplot(data=df, x='format', y='size_kb', ax=axes[1, 0], palette='Set2')
        axes[1, 0].set_yscale('log')  # Логарифмічна шкала, бо є дуже великі файли
        axes[1, 0].set_title('Вага файлів за форматами (Log scale)')

        # 4: Top 10 IDs за вагою
        top10 = df.nlargest(10, 'size_kb')
        sns.barplot(data=top10, x='size_kb', y='ID', ax=axes[1, 1], palette='Reds_r')
        axes[1, 1].set_title('Топ-10 найбільш деталізованих фото (за ID)')

        output_path = "reports/figures/advanced_analytics.png"
        plt.savefig(output_path)
        plt.show()

    except Exception as e:
        print(f"Помилка: {e}")


if __name__ == "__main__":
    create_advanced_visualizations("C:/Users/Elizabeth/Downloads/mvswantedperson_photo_297.json")
