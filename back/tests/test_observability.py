import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.infrastructure.observability import MetricsMiddleware, router as observability_router


class ObservabilityTests(unittest.TestCase):
    def setUp(self):
        self.app = FastAPI()
        self.app.add_middleware(MetricsMiddleware)
        self.app.include_router(observability_router)

        @self.app.get("/ping")
        def ping():
            return {"ok": True}

        self.client = TestClient(self.app)

    def test_metrics_endpoint_exposes_prometheus_text(self):
        self.client.get("/ping")
        resp = self.client.get("/metrics")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("sqlagent_http_requests_total", resp.text)


if __name__ == "__main__":
    unittest.main()