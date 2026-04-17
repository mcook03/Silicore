import json
import io
import unittest
from uuid import uuid4

from app import app
from engine.db import get_connection
from engine.user_store import create_user


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

    def test_health_routes_render(self):
        live = self.client.get("/health/live")
        self.assertEqual(live.status_code, 200)
        self.assertEqual(live.get_json()["status"], "ok")

        ready = self.client.get("/health/ready")
        self.assertEqual(ready.status_code, 200)
        self.assertIn("database", ready.get_json())
        self.assertIn("database_runtime", ready.get_json())
        self.assertIn("jobs", ready.get_json())

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
        self.assertIn("Formal Review Decisions", page)
        self.assertIn("Assignments & Mentions", page)
        self.assertIn("Release Gates", page)
        self.assertIn("Nexus Runtime Snapshot", page)
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
        self.assertIn("Request Reset", page)
        self.assertIn("Reset Password", page)
        self.assertIn("Verify Email", page)
        self.assertIn("Verify MFA", page)

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

    def test_atlas_stream_route_returns_final_payload(self):
        response = self.client.post(
            "/atlas/query/stream",
            json={
                "page_type": "board",
                "prompt": "What should I fix first?",
                "thread_key": "stream-test-thread",
                "context": {
                    "dominant_domain": "Signal Integrity",
                    "risk_sources": [{"message": "Differential pair mismatch", "severity": "high", "domain": "signal integrity"}],
                },
                "history": [],
            },
        )
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn('"type": "status"', body)
        self.assertIn('"type": "final"', body)

    def test_atlas_agent_runs_route_returns_payload(self):
        response = self.client.get("/atlas/agent-runs?thread_key=stream-test-thread")
        self.assertEqual(response.status_code, 200)
        self.assertIn("runs", response.get_json())

    def test_atlas_action_route_returns_job_payload(self):
        response = self.client.post(
            "/atlas/action",
            json={
                "action_name": "generate_signoff_packet",
                "context": {
                    "board_name": "Demo Board",
                    "release_note": "Needs one more validation pass.",
                    "top_actions": [{"label": "Tighten decoupling loop"}],
                    "validation_plan": ["Probe the input rail under load."],
                },
            },
        )
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertIn("job", payload)
        self.assertIn("result", payload)
        self.assertIn("summary", payload["result"])

    def test_atlas_signoff_action_route_returns_gate_payload(self):
        response = self.client.post(
            "/atlas/action",
            json={
                "action_name": "evaluate_signoff_gate",
                "context": {
                    "score": 58,
                    "risks": [{"severity": "critical", "message": "Critical fault"}],
                    "parser_confidence": {"score": 68},
                    "physics_summary": {"summary": {"worst_voltage_drop_mv": 88.0, "worst_impedance_mismatch_pct": 24.0}, "risks": [{"severity": "high"}]},
                    "score_explanation": {"overflow_penalty": 2.0},
                },
            },
        )
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertIn("job", payload)
        self.assertIn("result", payload)
        self.assertIn("decision", payload["result"])

    def test_atlas_parser_trust_action_route_returns_payload(self):
        response = self.client.post(
            "/atlas/action",
            json={
                "action_name": "inspect_parser_trust",
                "context": {
                    "parser_confidence": {"score": 78},
                    "cam_summary": {
                        "active": True,
                        "readiness_score": 64,
                        "trust_call": "package_incomplete",
                        "missing_signals": ["Missing drill data"],
                    },
                },
            },
        )
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertIn("job", payload)
        self.assertIn("result", payload)
        self.assertIn("trust_call", payload["result"])

    def test_evaluation_route_returns_fixture_summary(self):
        with self.client.session_transaction() as session:
            session.clear()
        response = self.client.get("/admin/evaluation")
        self.assertEqual(response.status_code, 403)

    def test_admin_routes_allow_lead_or_admin_session(self):
        suffix = str(uuid4())[:8]
        user = create_user("Lead Reviewer", f"lead-reviewer-{suffix}@example.com", "password123")
        connection = get_connection()
        try:
            connection.execute("UPDATE users SET role = ? WHERE user_id = ?", ("admin", user["user_id"]))
            connection.commit()
        finally:
            connection.close()

        with self.client.session_transaction() as session:
            session["user_id"] = user["user_id"]

        evaluation_response = self.client.get("/admin/evaluation")
        self.assertEqual(evaluation_response.status_code, 200)
        payload = evaluation_response.get_json()
        self.assertIn("fixture_count", payload)
        self.assertIn("boards", payload)
        self.assertIn("history_summary", payload)

        audit_response = self.client.get("/admin/audit")
        self.assertEqual(audit_response.status_code, 200)
        audit_payload = audit_response.get_json()
        self.assertIn("events", audit_payload)

        worker_status_response = self.client.get("/worker/status")
        self.assertEqual(worker_status_response.status_code, 200)
        self.assertIn("running", worker_status_response.get_json())

        runtime_response = self.client.get("/runtime/meta")
        self.assertEqual(runtime_response.status_code, 200)
        self.assertIn("runtime", runtime_response.get_json())
        self.assertIn("jobs", runtime_response.get_json())

        ops_response = self.client.get("/nexus-ops")
        self.assertEqual(ops_response.status_code, 200)
        self.assertIn("Nexus Runtime", ops_response.get_data(as_text=True))
        self.assertIn("Calibration History", ops_response.get_data(as_text=True))
        self.assertIn("External Validation Lane", ops_response.get_data(as_text=True))
        self.assertIn("Integration Registry", ops_response.get_data(as_text=True))

    def test_nexus_ops_external_validation_route_records_external_run(self):
        suffix = str(uuid4())[:8]
        user = create_user("Ops Lead", f"ops-lead-{suffix}@example.com", "password123")
        connection = get_connection()
        try:
            connection.execute("UPDATE users SET role = ? WHERE user_id = ?", ("admin", user["user_id"]))
            connection.commit()
        finally:
            connection.close()

        with self.client.session_transaction() as session:
            session["user_id"] = user["user_id"]

        with open("fixtures/altium_ascii_external.pcbdocascii", "rb") as handle:
            file_bytes = handle.read()
        payload = {
            "label": "Outside Altium Export",
            "validation_files": (
                io.BytesIO(file_bytes),
                "altium_ascii_external.pcbdocascii",
            ),
        }
        response = self.client.post(
            "/nexus-ops/external-validation",
            data=payload,
            content_type="multipart/form-data",
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        page = response.get_data(as_text=True)
        self.assertIn("External validation completed", page)
        self.assertIn("External Validation History", page)

    def test_project_review_decision_route_records_summary(self):
        suffix = str(uuid4())[:8]
        user = create_user("Workspace Lead", f"workspace-lead-{suffix}@example.com", "password123")
        connection = get_connection()
        try:
            connection.execute("UPDATE users SET role = ? WHERE user_id = ?", ("lead", user["user_id"]))
            connection.execute(
                "UPDATE projects SET owner_user_id = ?, owner_name = ?, owner_email = ? WHERE project_id = ?",
                (user["user_id"], user["name"], user["email"], "ec66c9f0"),
            )
            connection.commit()
        finally:
            connection.close()

        with self.client.session_transaction() as session:
            session["user_id"] = user["user_id"]

        response = self.client.post(
            "/projects/ec66c9f0/reviews",
            data={
                "status": "approved",
                "summary": "Review gate passed after the latest rerun collapsed the top layout driver.",
                "run_id": self.project["runs"][-1]["run_id"],
            },
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        page = response.get_data(as_text=True)
        self.assertIn("Review decision recorded.", page)
        self.assertIn("Review gate passed after the latest rerun collapsed the top layout driver.", page)

    def test_project_assignment_and_release_gate_routes_record_entries(self):
        suffix = str(uuid4())[:8]
        user = create_user("Workspace Lead B", f"workspace-lead-b-{suffix}@example.com", "password123")
        connection = get_connection()
        try:
            connection.execute("UPDATE users SET role = ? WHERE user_id = ?", ("lead", user["user_id"]))
            connection.execute(
                "UPDATE projects SET owner_user_id = ?, owner_name = ?, owner_email = ? WHERE project_id = ?",
                (user["user_id"], user["name"], user["email"], "ec66c9f0"),
            )
            connection.commit()
        finally:
            connection.close()

        with self.client.session_transaction() as session:
            session["user_id"] = user["user_id"]

        assignment_response = self.client.post(
            "/projects/ec66c9f0/assignments",
            data={
                "title": "Validate the dominant layout driver",
                "body": "Capture evidence before signoff.",
                "priority": "high",
            },
            follow_redirects=True,
        )
        self.assertEqual(assignment_response.status_code, 200)
        self.assertIn("Workspace assignment created.", assignment_response.get_data(as_text=True))

        gate_response = self.client.post(
            "/projects/ec66c9f0/release-gates",
            data={
                "title": "Gate for latest rerun",
                "run_id": self.project["runs"][-1]["run_id"],
                "required_approvals": "1",
            },
            follow_redirects=True,
        )
        self.assertEqual(gate_response.status_code, 200)
        page = gate_response.get_data(as_text=True)
        self.assertIn("Release gate created.", page)
        self.assertIn("Gate for latest rerun", page)


if __name__ == "__main__":
    unittest.main()
