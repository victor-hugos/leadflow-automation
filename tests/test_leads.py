import os
import shutil
import unittest
from uuid import uuid4
from pathlib import Path

import app.database.connection as db_connection
from app.main import app
from fastapi.testclient import TestClient


class LeadFlowApiTests(unittest.TestCase):
    def setUp(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        data_root = project_root / "data"
        data_root.mkdir(parents=True, exist_ok=True)

        self.temp_dir_path = (data_root / f"test_db_{uuid4().hex}").resolve()
        self.temp_dir_path.mkdir(parents=True, exist_ok=True)
        self.original_data_dir = db_connection.DATA_DIR
        self.original_db_path = db_connection.DB_PATH
        self.original_webhook_url = os.environ.get("LEAD_WEBHOOK_URL")

        db_connection.DATA_DIR = self.temp_dir_path
        db_connection.DB_PATH = db_connection.DATA_DIR / "leadflow_test.db"
        os.environ.pop("LEAD_WEBHOOK_URL", None)

        self.client_context = TestClient(app)
        self.client = self.client_context.__enter__()

    def tearDown(self) -> None:
        self.client_context.__exit__(None, None, None)

        db_connection.DATA_DIR = self.original_data_dir
        db_connection.DB_PATH = self.original_db_path

        if self.original_webhook_url is None:
            os.environ.pop("LEAD_WEBHOOK_URL", None)
        else:
            os.environ["LEAD_WEBHOOK_URL"] = self.original_webhook_url

        shutil.rmtree(self.temp_dir_path, ignore_errors=True)

    def test_valid_lead_returns_200_with_score_and_priority(self) -> None:
        payload = {
            "name": "Maria Silva",
            "email": "maria.valid@empresa.com",
            "phone": "11999990000",
            "company": "Empresa X",
            "role": "Gestora",
            "source": "api",
        }

        response = self.client.post("/leads", json=payload)
        body = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertIn("score", body["data"])
        self.assertIn("priority", body["data"])

    def test_duplicate_lead_returns_409(self) -> None:
        payload = {
            "name": "Lead Dup",
            "email": "dup@empresa.com",
            "phone": "11999990000",
            "company": "Empresa Dup",
            "role": "Analista",
            "source": "api",
        }

        first = self.client.post("/leads", json=payload)
        second = self.client.post("/leads", json=payload)

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 409)
        self.assertEqual(second.json()["message"], "Duplicate lead detected")

    def test_score_high_returns_high_priority(self) -> None:
        payload = {
            "name": "High Score",
            "email": "high@empresa.com",
            "phone": "11999990000",
            "company": "Empresa High",
            "role": "Manager",
            "source": "api",
        }

        response = self.client.post("/leads", json=payload)
        body = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(body["data"]["priority"], "high")
        self.assertGreaterEqual(body["data"]["score"], 41)

    def test_get_leads_returns_data_list(self) -> None:
        payload = {
            "name": "List Test",
            "email": "list@empresa.com",
            "phone": "11999990000",
            "company": "Empresa List",
            "role": "Ops",
            "source": "api",
        }
        self.client.post("/leads", json=payload)

        response = self.client.get("/leads")
        body = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertIn("data", body)
        self.assertIsInstance(body["data"], list)

    def test_webhook_failure_keeps_saved_lead(self) -> None:
        os.environ["LEAD_WEBHOOK_URL"] = "http://127.0.0.1:9999/webhook"
        payload = {
            "name": "Webhook Fail",
            "email": "webhook.fail@empresa.com",
            "phone": "11999990000",
            "company": "Empresa Hook",
            "role": "Engineer",
            "source": "api",
        }

        response = self.client.post("/leads", json=payload)
        body = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(body["webhook_status"], "failed")

        list_response = self.client.get("/leads")
        leads = list_response.json()["data"]
        saved_emails = [lead["email"] for lead in leads]
        self.assertIn(payload["email"], saved_emails)


if __name__ == "__main__":
    unittest.main()
