import json
import requests

def load_data(url):
    print(f"Downloading data from {url}...")
    # Тут буде логіка завантаження
    return True

if __name__ == "__main__":
    DATA_URL = "https://data.gov.ua/dataset/59ecf2ab-47a1-4fae-a63c-fe5007d68130/resource/beb48fcd-7682-441b-af03-cde8805e76b6"
    load_data(DATA_URL)