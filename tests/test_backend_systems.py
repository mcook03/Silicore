import os
import tempfile
import unittest
from uuid import uuid4

from engine.atlas_tools import compare_latest_runs, open_high_confidence_findings
from engine.db import get_connection, list_audit_events, list_review_decisions
from engine.evaluation_backend import evaluate_fixture_suite
from engine.gerber_parser import parse_gerber_file
from engine.subsystem_classifier import classify_pcb_subsystems
from engine.parser import parse_structured_board_file
from engine.project_store import create_project, update_project_review_status
from engine.user_store import create_user


class BackendSystemsTests(unittest.TestCase):
    def test_subsystem_classifier_finds_power_and_clocking(self):
        pcb = parse_structured_board_file("fixtures/power_board_good.kicad_pcb.txt") if os.path.exists("fixtures/power_board_good.kicad_pcb.txt") else None
        if pcb is None:
            pcb = parse_structured_board_file("fixtures/legacy_power_board.brd")
        summary = classify_pcb_subsystems(pcb)
        self.assertIn("subsystems", summary)
        self.assertTrue(summary["dominant_subsystem"])

    def test_gerber_parser_extracts_geometry(self):
        with tempfile.NamedTemporaryFile("w", suffix=".gbr", delete=False) as handle:
            handle.write("%TF.FileFunction,Copper,L1,Top*%\n")
            handle.write("X000000Y000000D02*\n")
            handle.write("X010000Y000000D01*\n")
            handle.write("X010000Y010000D01*\n")
            path = handle.name
        try:
            pcb = parse_gerber_file(path)
            self.assertGreater(len(pcb.traces), 0)
        finally:
            os.remove(path)

    def test_evaluation_backend_returns_summary(self):
        result = evaluate_fixture_suite()
        self.assertIn("fixture_count", result)
        self.assertIn("boards", result)

    def test_atlas_tools_summaries_work(self):
        compare = compare_latest_runs(
            {
                "run_summaries": [
                    {"name": "revA", "score": 58, "risk_count": 10, "created_at": "2026-04-01 00:00:00 UTC"},
                    {"name": "revB", "score": 73, "risk_count": 6, "created_at": "2026-04-02 00:00:00 UTC"},
                ]
            }
        )
        self.assertEqual(compare["status"], "ready")

        findings = open_high_confidence_findings(
            {
                "risk_sources": [
                    {"domain": "power", "confidence": 0.92, "message": "Weak decoupling", "components": ["U1"], "nets": ["VIN"]},
                    {"domain": "signal", "confidence": 0.45, "message": "Long route", "components": ["U2"], "nets": ["CLK"]},
                ]
            },
            domain="power",
        )
        self.assertEqual(findings["count"], 1)

    def test_review_and_audit_records_are_queryable(self):
        suffix = str(uuid4())[:8]
        owner = create_user("Lead Owner", f"lead-owner-{suffix}@example.com", "password123")
        project = create_project("Governance Workspace", owner=owner)
        update_project_review_status(project["project_id"], "ready_for_signoff")
        reviews = list_review_decisions(project_id=project["project_id"])
        self.assertGreaterEqual(len(reviews), 1)
        audit_events = list_audit_events(limit=20)
        self.assertTrue(any(event["event_type"] == "project.review_status_updated" for event in audit_events))


if __name__ == "__main__":
    unittest.main()
