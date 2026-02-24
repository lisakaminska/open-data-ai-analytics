import pandas as pd
import json
import base64
import io
from PIL import Image
import numpy as np

def analyze_image_properties(b64_string):
    """Декодує зображення та повертає його метадані."""
    try:
        # Декодування з Base64
        img_data = base64.b64decode(b64_string)
        img = Image.open(io.BytesIO(img_data))

        width, height = img.size
        format_type = img.format

        # Перетворюємо в ч/б для аналізу чіткості
        img_gray = img.convert('L')
        img_array = np.array(img_gray)

        # Високе значення = багато деталей, низьке = розмите або пусте фото
        sharpness_score = np.var(img_array)

        return width, height, format_type, sharpness_score
    except Exception:
        return None, None, None, None


def conduct_research(file_path):
    print(f"CV-дослідження датасету МВС")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        df = pd.DataFrame(data)
        print(f"Завантажено записів: {len(df)}")

        # Застосовуємо аналіз до кожного фото
        print("Аналіз зображення за допомогою CV")
        analysis_results = df['PHOTOIDBASE64ENCODE'].apply(analyze_image_properties)

        # Розпаковуємо результати у нові колонки
        df[['width', 'height', 'format', 'sharpness']] = pd.DataFrame(analysis_results.tolist(), index=df.index)

        # Аналіз роздільної здатності
        df['pixels'] = df['width'] * df['height']
        print("\nСтатистика роздільної здатності (пікселів):")
        print(df['pixels'].describe())

        # Розподіл форматів
        print("\nРозподіл форматів файлів:")
        print(df['format'].value_counts())

        # Виявлення низькоякісних фото
        # Гіпотеза: якщо роздільна здатність менше 200x200, Face ID працюватиме погано
        low_res = df[(df['width'] < 200) | (df['height'] < 200)]
        print(f"\nКількість фото з низькою роздільною здатністю : {len(low_res)}")

        # Аналіз чіткості
        print("\nСередній показник деталізації :", df['sharpness'].mean())
        blurry_photos = df[df['sharpness'] < 100]
        print(f"Кількість потенційно розмитих або однотонних фото: {len(blurry_photos)}")

    except Exception as e:
        print(f"Помилка аналізу: {e}")


if __name__ == "__main__":
    PATH = "C:/Users/Elizabeth/Downloads/mvswantedperson_photo_297.json"
    conduct_research(PATH)
