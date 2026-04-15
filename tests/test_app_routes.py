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

    def test_history_detail_includes_export_center_and_transparency(self):
        response = self.client.get("/history/project_20260410_234649_970160")

        self.assertEqual(response.status_code, 200)
        page = response.get_data(as_text=True)
        self.assertIn("Export Center", page)
        self.assertIn("Score Explainability", page)
        self.assertIn("Detailed Findings", page)


if __name__ == "__main__":
    unittest.main()
