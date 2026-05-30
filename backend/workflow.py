import asyncio
import json
import os
import sys


sys.path.insert(0, os.path.dirname(__file__))

MOCK_DIR = os.path.join(os.path.dirname(__file__), "..", "mock_data")

try:
    from dotenv import load_dotenv

    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
except ImportError:
    pass

from app.travel.assembler import assemble_plan
from app.travel.checklist_generator import default_family_checklist, generate_checklist
from app.travel.evaluator import compute_total, evaluate_plan
from app.travel.llm import extract_trip_request, select_options, suggest_next_trip
from app.travel.mock_repo import fetch_options, load_mock
from app.travel.router import router
from app.travel.runner import emit, normalize_family_members, run_workflow, validate_and_fill_defaults
from app.travel.utils import safe_json_parse


if __name__ == "__main__":
    TEST_QUERIES = [
        "хочу с семьёй в Астану на выходные, бюджет 150к",
        "в Астану завтра вдвоём",
        "Астана 3 ночи семья бюджет 80000",
    ]

    async def test():
        for query in TEST_QUERIES:
            print("\n" + "=" * 60)
            print(f"ЗАПРОС: {query}")
            print("=" * 60)
            plan = await run_workflow(query)
            print("\nРЕЗУЛЬТАТ:")
            print(json.dumps(plan, ensure_ascii=False, indent=2))

    asyncio.run(test())
