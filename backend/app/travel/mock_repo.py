import json
import os

from .constants import MOCK_DIR, NEED_TO_FILE, NEED_TO_OPTIONS_KEY


def load_mock(filename: str) -> list:
    try:
        path = os.path.join(MOCK_DIR, filename)
        with open(path, encoding="utf-8") as file:
            data = json.load(file)
            return data if isinstance(data, list) else []
    except Exception as exc:
        print(f"[WARN] Не удалось загрузить {filename}: {exc}")
        return []


def fetch_options(req: dict) -> dict:
    needs = req.get("needs", [])
    options = {}

    for need in needs:
        filename = NEED_TO_FILE.get(need)
        options_key = NEED_TO_OPTIONS_KEY.get(need)

        if filename and options_key:
            options[options_key] = load_mock(filename)

    return options
