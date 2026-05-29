import unittest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.application import inventory_controller
from app.application.dependencies import get_current_user


class MockRepo:
    def __init__(self):
        self._company = type("C", (), {"id": "comp1", "ai_enabled": False, "owner_email": "owner@example.com"})

    def get_company(self, company_id, user_email=None):
        # return company only if user is member or no user provided
        if user_email is None:
            return self._company
        # simple member check: owner@example.com is the owner
        if user_email in ("owner@example.com", "member@example.com"):
            return self._company
        return None

    def update_company_ai_enabled(self, company_id, enabled, actor_email=None):
        if actor_email != self._company.owner_email:
            raise ValueError("Only company owner can change AI settings")
        self._company.ai_enabled = bool(enabled)
        return self._company


class CompanyAIOptInTestCase(unittest.TestCase):
    def setUp(self):
        self.app = FastAPI()
        self.app.include_router(inventory_controller.router)

        async def _fake_user_owner():
            return "owner@example.com"

        self.app.dependency_overrides[get_current_user] = _fake_user_owner

        self.client = TestClient(self.app)

        # Patch repository used by controller
        self._orig_repo = inventory_controller.inventory_service.repository
        inventory_controller.inventory_service.repository = MockRepo()

    def tearDown(self):
        inventory_controller.inventory_service.repository = self._orig_repo

    def test_get_company_ai(self):
        resp = self.client.get("/api/v1/companies/comp1/ai")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("ai_enabled", data)

    def test_set_company_ai_by_owner(self):
        payload = {"enabled": True}
        resp = self.client.post("/api/v1/companies/comp1/ai", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get("ai_enabled"))

    def test_set_company_ai_by_non_owner_forbidden(self):
        # override auth to non-owner
        async def _fake_user_nonowner():
            return "member@example.com"

        self.app.dependency_overrides[get_current_user] = _fake_user_nonowner
        # member is allowed to access but repo only allows owner to toggle
        payload = {"enabled": True}
        resp = self.client.post("/api/v1/companies/comp1/ai", json=payload)
        self.assertEqual(resp.status_code, 403)


if __name__ == '__main__':
    unittest.main()
