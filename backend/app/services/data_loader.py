import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]
MOCK_DATA_DIR = BASE_DIR / "mock_data"

def load_json(filename: str):
    file_path = MOCK_DATA_DIR / filename

    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)