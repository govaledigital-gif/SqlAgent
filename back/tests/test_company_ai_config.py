import unittest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.application import inventory_controller
from app.application.dependencies import get_current_user


class MockRepo:
    def __init__(self):
        self._company = type("C", (), {"id": "comp1", "ai_enabled": True, "owner_email": "owner@example.com", "ai_api_key": None, "ai_quota_per_hour": "0"})

    def get_company(self, company_id, user_email=None):
        if user_email is None:
            return self._company
        if user_email in ("owner@example.com", "member@example.com"):
            return self._company
        return None

    def update_company_ai_config(self, company_id, actor_email=None, ai_api_key=None, ai_quota_per_hour=None):
        if actor_email != self._company.owner_email:
            raise ValueError("Only company owner can change AI settings")
        if ai_api_key is not None:
            self._company.ai_api_key = ai_api_key
        if ai_quota_per_hour is not None:
            self._company.ai_quota_per_hour = str(ai_quota_per_hour)
        return self._company


class CompanyAIConfigTestCase(unittest.TestCase):
    def setUp(self):
        self.app = FastAPI()
        self.app.include_router(inventory_controller.router)

        async def _fake_user_owner():
            return "owner@example.com"

        self.app.dependency_overrides[get_current_user] = _fake_user_owner

        self.client = TestClient(self.app)

        self._orig_repo = inventory_controller.inventory_service.repository
        inventory_controller.inventory_service.repository = MockRepo()

    def tearDown(self):
        inventory_controller.inventory_service.repository = self._orig_repo

    def test_get_config(self):
        resp = self.client.get("/api/v1/companies/comp1/ai/config")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("ai_api_key", data)

    def test_set_config_by_owner(self):
        payload = {"ai_api_key": "sk_test", "ai_quota_per_hour": 100}
        resp = self.client.post("/api/v1/companies/comp1/ai/config", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data.get("ai_api_key"), "sk_test")

    def test_set_config_by_non_owner_forbidden(self):
        async def _fake_user_nonowner():
            return "member@example.com"

        # member is allowed to read but not to update in our repo
        self.app.dependency_overrides[get_current_user] = _fake_user_nonowner
        payload = {"ai_api_key": "sk_test", "ai_quota_per_hour": 50}
        resp = self.client.post("/api/v1/companies/comp1/ai/config", json=payload)
        self.assertEqual(resp.status_code, 403)


if __name__ == '__main__':
    unittest.main()
