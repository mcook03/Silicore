import unittest
from uuid import uuid4

from engine.db import list_atlas_messages, persist_atlas_exchange
from engine.project_store import add_project_note, add_project_member, add_run_to_project, create_project, get_project
from engine.user_store import create_user, get_user_by_email


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


if __name__ == "__main__":
    unittest.main()
