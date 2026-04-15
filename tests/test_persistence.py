import unittest
from uuid import uuid4

from engine.db import list_atlas_agent_runs, list_atlas_messages, persist_atlas_exchange
from engine.project_store import (
    add_project_note,
    add_project_member,
    add_run_to_project,
    create_project,
    create_project_assignment,
    create_release_gate,
    get_project,
    record_release_approval,
)
from engine.user_store import (
    begin_authentication,
    create_email_verification_token,
    create_user,
    get_user_by_email,
    verify_email_with_token,
)


class PersistenceTests(unittest.TestCase):
    def test_db_backed_user_and_project_flow(self):
        suffix = str(uuid4())[:8]
        owner = create_user("Atlas Owner", f"atlas-owner-{suffix}@example.com", "password123")
        member = create_user("Atlas Member", f"atlas-member-{suffix}@example.com", "password123")

        project = create_project("Persistence Workspace", "DB-backed workspace", owner=owner)
        self.assertIsNotNone(project)
        self.assertEqual(project["owner"]["user_id"], owner["user_id"])

        updated = add_project_member(project["project_id"], member)
        self.assertEqual(len(updated.get("team_members", [])), 1)

        updated = add_project_note(project["project_id"], "Atlas", "Review note stored in the database.")
        self.assertEqual(len(updated.get("collaboration_notes", [])), 1)

        updated = add_run_to_project(
            project["project_id"],
            {
                "run_id": f"db_run_{suffix}",
                "name": "DB-backed run",
                "run_type": "single",
                "created_at": "2026-04-15 12:00:00 UTC",
                "score": 72,
                "risk_count": 4,
                "critical_count": 1,
                "summary": "Persistent run summary",
                "path": "dashboard_runs/db_run",
                "risk_snapshot": [{"category": "layout", "severity": "high", "message": "Tight spacing"}],
                "category_summary": {"layout": 1},
            },
        )
        self.assertEqual(len(updated.get("runs", [])), 1)

        fetched = get_project(project["project_id"])
        self.assertEqual(fetched["runs"][0]["run_id"], f"db_run_{suffix}")
        self.assertEqual(get_user_by_email(owner["email"])["user_id"], owner["user_id"])

        updated = create_project_assignment(
            project["project_id"],
            "Probe the dominant rail",
            body="Capture transient evidence before the next rerun.",
            assignee=member,
            priority="high",
            created_by_user_id=owner["user_id"],
        )
        self.assertEqual(len(updated.get("assignments", [])), 1)

        updated = create_release_gate(
            project["project_id"],
            "Revision A release gate",
            run_id=f"db_run_{suffix}",
            required_approvals=1,
            created_by_user_id=owner["user_id"],
        )
        self.assertEqual(len(updated.get("release_gates", [])), 1)

        gate_id = updated["release_gates"][0]["gate_id"]
        updated = record_release_approval(
            project["project_id"],
            gate_id,
            reviewer_user_id=owner["user_id"],
            decision="approved",
            summary="Ready after validation.",
        )
        self.assertEqual(updated["release_gates"][0]["status"], "approved")

    def test_atlas_threads_persist_to_backend(self):
        thread_key = f"atlas-thread-{uuid4()}"
        messages = persist_atlas_exchange(
            thread_key=thread_key,
            page_type="board",
            context={"board_name": "Persistence Board", "run_id": "run-123"},
            prompt="What should I fix first?",
            answer_payload={
                "title": "Fix Priority",
                "answer": "Route cleanup comes first.",
                "detail": "This is the highest-confidence issue on the board.",
                "follow_ups": ["Show me the evidence"],
                "citations": [{"label": "Route issue", "target": "risk-1", "components": ["U1"], "nets": ["CLK"]}],
                "intent": "prioritization",
            },
        )
        self.assertEqual(len(messages), 2)
        persisted = list_atlas_messages(thread_key)
        self.assertEqual(len(persisted), 2)
        self.assertEqual(persisted[-1]["intent"], "prioritization")

    def test_user_verification_and_session_flow(self):
        suffix = str(uuid4())[:8]
        user = create_user("Verification User", f"verify-{suffix}@example.com", "password123", email_verified=False)
        token_info = create_email_verification_token(user["email"])
        self.assertTrue(verify_email_with_token(token_info["token"]))
        auth_result = begin_authentication(user["email"], "password123", ip_address="127.0.0.1", user_agent="pytest")
        self.assertEqual(auth_result["status"], "authenticated")
        self.assertIn("session", auth_result)

    def test_atlas_agent_runs_persist(self):
        thread_key = f"atlas-agent-thread-{uuid4()}"
        persist_atlas_exchange(
            thread_key=thread_key,
            page_type="board",
            context={"board_name": "Agent Board"},
            prompt="Am I signoff ready?",
            answer_payload={"title": "Signoff", "answer": "Validation pending.", "detail": "", "follow_ups": [], "citations": [], "intent": "signoff"},
        )
        from engine.db import persist_atlas_agent_run

        persist_atlas_agent_run(
            thread_key=thread_key,
            page_type="board",
            prompt="Am I signoff ready?",
            plan=[{"action_name": "evaluate_signoff_gate"}],
            results=[{"action_name": "evaluate_signoff_gate", "status": "completed"}],
            model_mode="deterministic_agent",
        )
        runs = list_atlas_agent_runs(thread_key)
        self.assertGreaterEqual(len(runs), 1)


if __name__ == "__main__":
    unittest.main()
