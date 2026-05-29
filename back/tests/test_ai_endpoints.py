import unittest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.application import ai_controller
from app.application.dependencies import get_current_user


class MockRepo:
    def get_company(self, company_id, user_email=None):
        return True

    def execute_safe_select(self, company_id, sql, limit=200):
        return [{"id": "1", "sku": "S1", "name": "Widget"}]


class AIEndpointsTestCase(unittest.TestCase):
    def setUp(self):
        self.app = FastAPI()
        self.app.include_router(ai_controller.router)

        # Override auth dependency to avoid JWT validation in tests
        async def _fake_user():
            return "test@example.com"

        self.app.dependency_overrides[get_current_user] = _fake_user

        # Use TestClient
        self.client = TestClient(self.app)

        # Patch llm_service methods and repo
        self._orig_llm = ai_controller.llm_service
        ai_controller.llm_service = ai_controller.llm_service
        ai_controller.llm_service.repo = MockRepo()

    def tearDown(self):
        # restore
        ai_controller.llm_service = self._orig_llm

    def test_nl_query_returns_results(self):
        # Patch nl_to_sql to deterministic output
        def fake_nl(question, company_id, user_email):
            return {"sql": "SELECT id, sku, name FROM products LIMIT 1", "explanation": "ok", "confidence": 0.5}

        ai_controller.llm_service.nl_to_sql = fake_nl

        payload = {"company_id": "comp1", "question": "What products are low on stock?"}
        resp = self.client.post("/api/v1/ai/nl-query", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("sql", data)
        self.assertIn("results", data)
        self.assertEqual(len(data["results"]), 1)

    def test_sql_optimize_endpoint(self):
        # Patch optimize_sql
        def fake_opt(sql, company_id, user_email):
            return {"original": sql, "suggested_sql": "SELECT id FROM products", "explanation": "Optimized"}

        ai_controller.llm_service.optimize_sql = fake_opt

        payload = {"company_id": "comp1", "sql": "select * from products"}
        resp = self.client.post("/api/v1/ai/sql-optimize", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["suggested_sql"], "SELECT id FROM products")


if __name__ == '__main__':
    unittest.main()
