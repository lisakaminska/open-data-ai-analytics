import pandas as pd
import json


def run_quality_check(file_path):
    print(f"Aналіз якості датасету:")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        df = pd.DataFrame(data)

        # 1. Загальна статистика
        print(f"Загальна кількість записів: {len(df)}")

        # 2. Перевірка ID
        unique_ids = df['ID'].nunique()
        print(f"Унікальних ID: {unique_ids}")
        if unique_ids < len(df):
            print(f"Знайдено {len(df) - unique_ids} дубльованих ID")

        # 3. Аналіз фото (Base64)
        if 'PHOTOIDBASE64ENCODE' in df.columns:
            # Мінімальна довжина рядка для фото зазвичай > 1000 символів
            avg_photo_len = df['PHOTOIDBASE64ENCODE'].str.len().mean()
            min_photo_len = df['PHOTOIDBASE64ENCODE'].str.len().min()
            print(f"Середня довжина рядка фото: {avg_photo_len:.0f} символів")
            print(f"Мінімальна довжина рядка фото: {min_photo_len} символів")

            # Перевірка на "биті" фото (занадто короткі)
            broken_photos = df[df['PHOTOIDBASE64ENCODE'].str.len() < 100]
            print(f"Кількість підозрілих (коротких) фото: {len(broken_photos)}")

        return df
    except Exception as e:
        print(f"Помилка при аналізі: {e}")

if __name__ == "__main__":
    run_quality_check("C:/Users/Elizabeth/Downloads/mvswantedperson_photo_297.json")
