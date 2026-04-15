import json
import unittest

from app import app


class AppRouteSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = app.test_client()
        with open("dashboard_projects/ec66c9f0.json", "r", encoding="utf-8") as file:
            cls.project = json.load(file)

    def test_core_pages_render(self):
        for url in [
            "/",
            "/login",
            "/single-board",
            "/project-review",
            "/projects",
            "/projects/ec66c9f0",
            "/history",
            "/history/project_20260410_234649_970160",
        ]:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, url)

    def test_compare_route_renders_for_existing_project_runs(self):
        run_a = self.project["runs"][-2]["run_id"]
        run_b = self.project["runs"][-1]["run_id"]
        response = self.client.get(f"/projects/ec66c9f0/compare?run_a={run_a}&run_b={run_b}")

        self.assertEqual(response.status_code, 200)
        page = response.get_data(as_text=True)
        self.assertIn("Project Score Trend", page)
        self.assertIn("Category Shift Bar View", page)
        self.assertIn("Engineering Domain Shift", page)
        self.assertIn("Recurring Engineering Domains", page)
        self.assertIn("Revision Inspector", page)
        self.assertIn("Atlas Intelligence", page)
        self.assertIn("Fix-First Readout", page)

    def test_compare_route_recovers_when_run_ids_are_invalid(self):
        response = self.client.get("/projects/ec66c9f0/compare?run_a=missing_a&run_b=missing_b", follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        page = response.get_data(as_text=True)
        self.assertIn("Nexus Comparison", page)
        self.assertIn("Project Score Trend", page)

    def test_history_detail_includes_export_center_and_transparency(self):
        response = self.client.get("/history/project_20260410_234649_970160")

        self.assertEqual(response.status_code, 200)
        page = response.get_data(as_text=True)
        self.assertIn("Export Center", page)
        self.assertIn("Score Explainability", page)
        self.assertIn("Detailed Findings", page)
        self.assertIn("Review Readiness", page)

    def test_history_printable_page_renders(self):
        response = self.client.get("/history/project_20260410_234649_970160/print")

        self.assertEqual(response.status_code, 200)
        page = response.get_data(as_text=True)
        self.assertIn("Silicore Nexus Printable Review", page)
        self.assertIn("Save As PDF", page)

    def test_settings_page_includes_custom_profile_controls(self):
        response = self.client.get("/settings")

        self.assertEqual(response.status_code, 200)
        page = response.get_data(as_text=True)
        self.assertIn("Custom Profile Name", page)
        self.assertIn("Custom Project Profile", page)
        self.assertIn("Profile Architecture", page)
        self.assertIn("Review Pillars", page)

    def test_project_detail_includes_timeline_and_workspace_intelligence(self):
        response = self.client.get("/projects/ec66c9f0")

        self.assertEqual(response.status_code, 200)
        page = response.get_data(as_text=True)
        self.assertIn("Confidence Timeline", page)
        self.assertIn("Recurring Failure Pattern", page)
        self.assertIn("Silicore Nexus", page)
        self.assertIn("Atlas Intelligence", page)
        self.assertIn("Nexus Review Architecture", page)
        self.assertIn("Nexus Review Workflow", page)
        self.assertIn("Value Metrics", page)
        self.assertIn("Nexus Access", page)

    def test_single_board_page_includes_advanced_review_surfaces(self):
        response = self.client.get("/single-board")

        self.assertEqual(response.status_code, 200)
        page = response.get_data(as_text=True)
        self.assertIn("Atlas Intelligence", page)
        self.assertIn("Advanced Review Lenses", page)
        self.assertIn("Traceability & Signal Posture", page)

    def test_login_page_renders_account_forms(self):
        response = self.client.get("/login")

        self.assertEqual(response.status_code, 200)
        page = response.get_data(as_text=True)
        self.assertIn("Sign In", page)
        self.assertIn("Create Account", page)

    def test_atlas_query_route_returns_answer_payload(self):
        thread_key = "test-board-thread"
        response = self.client.post(
            "/atlas/query",
            json={
                "page_type": "board",
                "prompt": "What should I fix first?",
                "thread_key": thread_key,
                "context": {
                    "dominant_domain": "Signal Integrity",
                    "mission": "Focus first on signal integrity.",
                    "risk_sources": [
                        {
                            "id": "risk-1",
                            "domain": "signal integrity",
                            "category": "signal_integrity",
                            "severity": "high",
                            "message": "Differential pair mismatch",
                            "components": ["U1"],
                            "nets": ["USB_DP", "USB_DN"],
                        }
                    ],
                    "top_actions": [
                        {
                            "label": "Fix differential pair mismatch",
                            "components": ["U1"],
                            "nets": ["USB_DP", "USB_DN"],
                        }
                    ],
                },
                "history": [],
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertIn("title", payload)
        self.assertIn("answer", payload)
        self.assertIn("follow_ups", payload)
        self.assertIn("thread", payload)
        self.assertEqual(payload.get("thread_key"), thread_key)

        thread_response = self.client.get(f"/atlas/thread?thread_key={thread_key}")
        self.assertEqual(thread_response.status_code, 200)
        thread_payload = thread_response.get_json()
        self.assertGreaterEqual(len(thread_payload.get("messages", [])), 2)


if __name__ == "__main__":
    unittest.main()
