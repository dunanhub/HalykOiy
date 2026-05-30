import importlib
import os
import sys
import types
import unittest


BACKEND_DIR = os.path.dirname(os.path.dirname(__file__))
PROJECT_DIR = os.path.dirname(BACKEND_DIR)

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)


class _Route:
    def __init__(self, path):
        self.path = path


APIWebSocketRoute = type("APIWebSocketRoute", (), {"__init__": lambda self, path: setattr(self, "path", path)})


class _Router:
    def __init__(self, *args, **kwargs):
        self.routes = []

    def get(self, path, *args, **kwargs):
        return self._decorator(path)

    def post(self, path, *args, **kwargs):
        return self._decorator(path)

    def websocket(self, path, *args, **kwargs):
        def decorator(func):
            self.routes.append(APIWebSocketRoute(path))
            return func

        return decorator

    def _decorator(self, path):
        def decorator(func):
            self.routes.append(_Route(path))
            return func

        return decorator


class _FastAPI(_Router):
    def add_middleware(self, *args, **kwargs):
        return None

    def include_router(self, router):
        self.routes.extend(getattr(router, "routes", []))


def _install_dependency_stubs():
    if "anthropic" not in sys.modules:
        anthropic = types.ModuleType("anthropic")
        anthropic.Anthropic = lambda *args, **kwargs: object()
        sys.modules["anthropic"] = anthropic

    if "fastapi" not in sys.modules:
        fastapi = types.ModuleType("fastapi")
        fastapi.FastAPI = _FastAPI
        fastapi.APIRouter = _Router
        fastapi.WebSocket = object
        sys.modules["fastapi"] = fastapi

        middleware = types.ModuleType("fastapi.middleware")
        cors = types.ModuleType("fastapi.middleware.cors")
        cors.CORSMiddleware = object
        sys.modules["fastapi.middleware"] = middleware
        sys.modules["fastapi.middleware.cors"] = cors


_install_dependency_stubs()


class WorkflowIntegrationTest(unittest.TestCase):
    def test_workflow_exports_run_workflow(self):
        workflow = importlib.import_module("workflow")

        self.assertTrue(callable(workflow.run_workflow))

    def test_workflow_mock_dir_points_to_project_mock_data(self):
        constants = importlib.import_module("app.travel.constants")
        expected_mock_dir = os.path.abspath(os.path.join(PROJECT_DIR, "mock_data"))

        self.assertEqual(os.path.abspath(constants.MOCK_DIR), expected_mock_dir)

        for filename in constants.NEED_TO_FILE.values():
            with self.subTest(filename=filename):
                self.assertTrue(os.path.exists(os.path.join(constants.MOCK_DIR, filename)))

    def test_fastapi_exposes_travel_websocket(self):
        app_module = importlib.import_module("app.main")
        websocket_paths = {
            route.path
            for route in app_module.app.routes
            if route.__class__.__name__ == "APIWebSocketRoute"
        }

        self.assertIn("/ws/travel", websocket_paths)

    def test_fallback_selection_builds_valid_mock_plan(self):
        constants = importlib.import_module("app.travel.constants")
        mock_repo = importlib.import_module("app.travel.mock_repo")
        runner = importlib.import_module("app.travel.runner")
        evaluator = importlib.import_module("app.travel.evaluator")

        req = dict(constants.DEFAULTS)
        req.update(
            {
                "to_city": "astana",
                "dates": "weekend",
                "budget": 150_000,
                "pax": 4,
                "nights": 2,
            }
        )

        options = mock_repo.fetch_options(req)
        selection = runner.fallback_select_options(req, options)
        ok, hint = evaluator.evaluate_plan(req, selection, options)

        self.assertTrue(ok, hint)

    def test_prefilter_limits_candidates_before_llm(self):
        constants = importlib.import_module("app.travel.constants")
        mock_repo = importlib.import_module("app.travel.mock_repo")
        prefilter = importlib.import_module("app.travel.prefilter")

        req = dict(constants.DEFAULTS)
        req.update(
            {
                "from_city": "алматы",
                "to_city": "Астана",
                "budget": 150_000,
                "pax": 4,
                "nights": 2,
                "family_members": [{"role": "ребёнок", "age": 8, "name": None}],
                "needs": ["flight", "hotel", "insurance", "restaurant", "pharmacy"],
            }
        )

        candidates = prefilter.prefilter_options(req, mock_repo.fetch_options(req))

        self.assertLessEqual(len(candidates["flights"]), 5)
        self.assertLessEqual(len(candidates["hotels"]), 5)
        self.assertLessEqual(len(candidates["insurance"]), 3)
        self.assertLessEqual(len(candidates["restaurants"]), 3)
        self.assertTrue(candidates["flights"])
        self.assertTrue(all(item["to"] == "NQZ" for item in candidates["flights"]))
        self.assertTrue(all(item["city"].lower() == "астана" for item in candidates["hotels"]))
        self.assertTrue(all(item["city"].lower() == "астана" for item in candidates["restaurants"]))
        self.assertTrue(candidates["pharmacy"])
        self.assertEqual(len(candidates["pharmacy"]), 1)
        self.assertEqual(candidates["pharmacy"][0]["id"], "kit_2")

    def test_clarifier_asks_before_fetch_when_budget_missing(self):
        clarifier = importlib.import_module("app.travel.clarifier")
        runner = importlib.import_module("app.travel.runner")

        req, error = runner.validate_and_fill_defaults(
            {
                "from_city": "Алматы",
                "to_city": "Астана",
                "dates": "выходные",
                "nights": None,
                "pax": 2,
                "family_members": [{"role": "взрослый", "age": None, "name": None}],
                "budget": None,
                "trip_type": "leisure",
                "needs": ["flight", "hotel"],
            }
        )
        clarification = clarifier.build_clarification(req)

        self.assertIsNone(error)
        self.assertEqual(clarification["status"], "need_clarification")
        self.assertIn("budget", clarification["missing_fields"])

    def test_family_prices_scale_with_pax_for_insurance_and_restaurant(self):
        evaluator = importlib.import_module("app.travel.evaluator")

        req = {"pax": 4, "nights": 2}
        insurance_item = {"price": 724}
        restaurant_item = {"avg_check": 6000}

        self.assertEqual(evaluator.price_for("insurance", insurance_item, req), 2896)
        self.assertEqual(evaluator.price_for("restaurant", restaurant_item, req), 24000)

    def test_edit_plan_swaps_activity_without_rebuilding_from_scratch(self):
        editor = importlib.import_module("app.travel.editor")

        existing_plan = {
            "plan_id": "plan-1",
            "trip": {
                "from": "Алматы",
                "to": "Актобе",
                "dates": "выходные",
                "nights": 2,
                "pax": 4,
                "type": "family_weekend",
            },
            "family_members": [
                {"role": "взрослый", "age": None, "name": None},
                {"role": "взрослый", "age": None, "name": None},
                {"role": "ребёнок", "age": 8, "name": None},
                {"role": "ребёнок", "age": 5, "name": None},
            ],
            "budget": 300000,
            "items": [
                {"category": "flight", "id": "flight_1", "price": 100000},
                {"category": "hotel", "id": "hotel_1", "price": 100000},
                {"category": "insurance", "id": "ins_1", "price": 2000},
                {"category": "travel_kit", "id": "kit_2", "price": 5500},
                {"category": "activity", "id": "activity_4", "title": "Каякинг на озере Актобе", "price": 0},
                {"category": "restaurant", "id": "rest_2", "price": 18000},
            ],
        }

        updated = editor.update_plan(existing_plan, "поменяй активность с каякинга на кино")
        activity_titles = [item.get("title", "") for item in updated["items"] if item.get("category") == "activity"]

        self.assertEqual(updated["trip"]["to"], "Актобе")
        self.assertEqual(updated["trip"]["pax"], 4)
        self.assertTrue(any("Кино" in title or "кино" in title for title in activity_titles))


if __name__ == "__main__":
    unittest.main()
