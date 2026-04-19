import os
import tempfile
import unittest
from uuid import uuid4
import zipfile

from engine.atlas_tools import compare_latest_runs, evaluate_signoff_readiness, inspect_parser_trust, open_high_confidence_findings
from engine.config_loader import load_config
from engine.db import get_connection, list_audit_events, list_evaluation_runs, list_integration_configs, list_review_decisions, upsert_integration_config
from engine.email_service import send_identity_email
from engine.evaluation_backend import evaluate_external_suite, evaluate_fixture_suite, summarize_evaluation_history
from engine.gerber_parser import parse_gerber_directory, parse_gerber_file
from engine.job_store import claim_jobs, create_job, get_job
from engine.job_runner import _handle_job_failure, process_queued_jobs
from engine.org_store import accept_organization_invitation, create_organization, create_organization_invitation
from engine.altium_ascii_parser import parse_altium_ascii_file
from engine.rule_runner import run_analysis
from engine.stackup_model import derive_stackup_summary
from engine.subsystem_classifier import classify_pcb_subsystems
from engine.parser import parse_pcb_file, parse_structured_board_file
from engine.project_store import create_project, update_project_review_status
from engine.user_store import create_password_reset_token, create_user, reset_password_with_token


class BackendSystemsTests(unittest.TestCase):
    def test_subsystem_classifier_finds_power_and_clocking(self):
        pcb = parse_structured_board_file("fixtures/power_board_good.kicad_pcb.txt") if os.path.exists("fixtures/power_board_good.kicad_pcb.txt") else None
        if pcb is None:
            pcb = parse_structured_board_file("fixtures/legacy_power_board.brd")
        summary = classify_pcb_subsystems(pcb)
        self.assertIn("subsystems", summary)
        self.assertTrue(summary["dominant_subsystem"])
        self.assertIn("interaction_risks", summary)

    def test_stackup_model_and_altium_ascii_parser_work(self):
        with tempfile.NamedTemporaryFile("w", suffix=".pcbdocascii", delete=False) as handle:
            handle.write("RECORD=COMPONENT|Designator=U1|Comment=MCU|X=10|Y=10|Layer=TopLayer\n")
            handle.write("RECORD=PAD|Name=1|Net=CLK|X=10|Y=10|Layer=TopLayer\n")
            handle.write("RECORD=TRACK|Net=CLK|X1=10|Y1=10|X2=30|Y2=10|Width=0.15|Layer=TopLayer\n")
            handle.write("RECORD=VIA|Net=CLK|X=20|Y=10|HoleSize=0.3|Size=0.6\n")
            path = handle.name
        try:
            pcb = parse_altium_ascii_file(path)
            summary = derive_stackup_summary(pcb, board_type="high_speed")
            self.assertGreaterEqual(len(pcb.traces), 1)
            self.assertIn("style", summary)
            self.assertIn("reference_coverage_pct", summary)
        finally:
            os.remove(path)

    def test_external_style_altium_ascii_fixture_parses_regions_outline_and_vias(self):
        pcb = parse_altium_ascii_file("fixtures/altium_ascii_external.pcbdocascii")
        self.assertEqual(pcb.source_format, "altium_ascii")
        self.assertGreaterEqual(len(pcb.components), 2)
        self.assertGreaterEqual(len(pcb.traces), 2)
        self.assertGreaterEqual(len(pcb.vias), 1)
        self.assertGreaterEqual(len(pcb.zones), 1)
        self.assertGreaterEqual(len(pcb.outline_segments), 4)

    def test_gerber_parser_extracts_geometry(self):
        with tempfile.NamedTemporaryFile("w", suffix=".gbr", delete=False) as handle:
            handle.write("%TF.FileFunction,Copper,L1,Top*%\n")
            handle.write("%MOMM*%\n")
            handle.write("%FSLAX24Y24*%\n")
            handle.write("%ADD10C,0.2000*%\n")
            handle.write("D10*\n")
            handle.write("X000000Y000000D02*\n")
            handle.write("X010000Y000000D01*\n")
            handle.write("X010000Y010000D01*\n")
            handle.write("X005000Y005000D03*\n")
            handle.write("M02*\n")
            path = handle.name
        try:
            pcb = parse_gerber_file(path)
            self.assertGreater(len(pcb.traces), 0)
            self.assertGreater(len(pcb.zones), 0)
            self.assertIn("geometry_capabilities", pcb.metadata)
        finally:
            os.remove(path)

    def test_gerber_directory_and_archive_parser_extracts_cam_bundle(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            top = os.path.join(temp_dir, "board.gtl")
            outline = os.path.join(temp_dir, "board.gko")
            drill = os.path.join(temp_dir, "board.drl")
            with open(top, "w", encoding="utf-8") as handle:
                handle.write("%TF.FileFunction,Copper,L1,Top*%\n%MOMM*%\n%FSLAX24Y24*%\n%ADD10C,0.2500*%\nD10*\n")
                handle.write("X000000Y000000D02*\nX020000Y000000D01*\nX020000Y020000D01*\nM02*\n")
            with open(outline, "w", encoding="utf-8") as handle:
                handle.write("%TF.FileFunction,Profile,NP*%\n%MOMM*%\n%FSLAX24Y24*%\n%ADD10C,0.1000*%\nD10*\n")
                handle.write("X000000Y000000D02*\nX020000Y000000D01*\nX020000Y020000D01*\nX000000Y020000D01*\nX000000Y000000D01*\nM02*\n")
            with open(drill, "w", encoding="utf-8") as handle:
                handle.write("M48\nMETRIC,TZ\nT01C0.300\n%\nT01\nX005000Y005000\nX015000Y015000\nM30\n")

            pcb = parse_gerber_directory(temp_dir)
            self.assertGreater(len(pcb.traces), 0)
            self.assertGreater(len(pcb.outline_segments), 0)
            self.assertGreater(len(pcb.vias), 0)
            self.assertEqual(pcb.source_format, "gerber_cam")
            self.assertEqual(pcb.metadata["cam"]["layer_file_count"], 3)

            archive_path = os.path.join(temp_dir, "bundle.zip")
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.write(top, arcname="board.gtl")
                archive.write(outline, arcname="board.gko")
                archive.write(drill, arcname="board.drl")
            archive_pcb = parse_gerber_file(archive_path)
            self.assertGreater(len(archive_pcb.traces), 0)
            self.assertEqual(archive_pcb.metadata["cam"]["bundle_type"], "archive")

    def test_repo_gerber_cam_fixture_is_parsed_as_complete_bundle(self):
        pcb = parse_pcb_file("fixtures/gerber_cam_job")
        self.assertEqual(pcb.source_format, "gerber_cam")
        self.assertGreater(len(pcb.traces), 0)
        self.assertGreater(len(pcb.outline_segments), 0)
        self.assertGreater(len(pcb.vias), 0)

        result = run_analysis(pcb, load_config("custom_config.json"))
        bundle_risks = [risk for risk in result["risks"] if risk.get("rule_id", "").startswith("cam_bundle")]
        self.assertFalse(bundle_risks, f"Expected no CAM bundle risks for complete fixture, got {bundle_risks}")

    def test_alt_named_gerber_cam_fixture_is_parsed_as_complete_bundle(self):
        pcb = parse_pcb_file("fixtures/gerber_cam_alt_naming")
        self.assertEqual(pcb.source_format, "gerber_cam")
        self.assertGreater(len(pcb.traces), 0)
        self.assertGreater(len(pcb.outline_segments), 0)
        self.assertGreater(len(pcb.vias), 0)

        result = run_analysis(pcb, load_config("custom_config.json"))
        bundle_risks = [risk for risk in result["risks"] if risk.get("rule_id", "").startswith("cam_bundle")]
        self.assertFalse(bundle_risks, f"Expected no CAM bundle risks for alt-named fixture, got {bundle_risks}")

    def test_sparse_gerber_fixture_triggers_cam_bundle_findings(self):
        pcb = parse_pcb_file("fixtures/gerber_cam_sparse")
        result = run_analysis(pcb, load_config("custom_config.json"))
        bundle_risks = [risk for risk in result["risks"] if risk.get("rule_id", "").startswith("cam_bundle")]
        self.assertTrue(bundle_risks)

    def test_missing_drill_gerber_fixture_triggers_drill_bundle_finding(self):
        pcb = parse_pcb_file("fixtures/gerber_cam_missing_drill")
        result = run_analysis(pcb, load_config("custom_config.json"))
        bundle_risks = [risk for risk in result["risks"] if risk.get("rule_id", "").startswith("cam_bundle_drill")]
        self.assertTrue(bundle_risks)

    def test_vendor_style_gerber_fixture_is_parsed_as_complete_bundle(self):
        pcb = parse_pcb_file("fixtures/gerber_cam_vendor_complete")
        self.assertEqual(pcb.source_format, "gerber_cam")
        self.assertGreater(len(pcb.traces), 0)
        self.assertGreater(len(pcb.outline_segments), 0)
        self.assertGreater(len(pcb.vias), 0)

        result = run_analysis(pcb, load_config("custom_config.json"))
        bundle_risks = [risk for risk in result["risks"] if risk.get("rule_id", "").startswith("cam_bundle")]
        self.assertFalse(bundle_risks, f"Expected no CAM bundle risks for vendor-style complete fixture, got {bundle_risks}")

    def test_vendor_style_incomplete_gerber_fixture_triggers_bundle_findings(self):
        pcb = parse_pcb_file("fixtures/gerber_cam_vendor_incomplete")
        result = run_analysis(pcb, load_config("custom_config.json"))
        bundle_risks = [risk for risk in result["risks"] if risk.get("rule_id", "").startswith("cam_bundle")]
        self.assertTrue(bundle_risks)

    def test_altium_style_gerber_extensions_are_recognized(self):
        pcb = parse_pcb_file("fixtures/gerber_cam_altium_style")
        self.assertEqual(pcb.source_format, "gerber_cam")
        self.assertGreater(len(pcb.outline_segments), 0)
        self.assertIn("Edge.Cuts", pcb.layers)
        self.assertIn("Top Paste", pcb.layers)

    def test_geometry_rule_uses_board_regions_for_clearance(self):
        pcb = parse_pcb_file("fixtures/high_voltage_spacing_board.kicad_pcb")
        result = run_analysis(pcb, load_config("custom_config.json"))
        geometry_risks = [risk for risk in result["risks"] if risk.get("rule_id") in {"cam_geometry", "cam_geometry_creepage"}]
        self.assertTrue(geometry_risks)

    def test_evaluation_backend_returns_summary(self):
        result = evaluate_fixture_suite()
        self.assertIn("fixture_count", result)
        self.assertIn("boards", result)
        self.assertIn("average_parser_confidence", result)
        self.assertIn("parser_health", result)
        self.assertIn("cam_health", result)
        self.assertIn("review_ready_bundles", result["cam_health"])
        self.assertIn("missing_signals", result["cam_health"])
        self.assertTrue(any((board.get("format") or "").startswith("gerber") or board.get("cam_bundle_type") for board in result["boards"]))
        history = list_evaluation_runs(limit=5)
        self.assertTrue(any(item["evaluation_id"] == result["evaluation_id"] for item in history if result.get("evaluation_id")))

    def test_external_evaluation_suite_records_external_scope(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            package_dir = os.path.join(temp_dir, "vendor_drop")
            os.makedirs(package_dir, exist_ok=True)
            for filename in ["top_cu.ger", "bot_cu.ger", "mech_profile.gm1", "nc_drill.drl"]:
                source = os.path.join("fixtures", "gerber_cam_vendor_complete", filename)
                with open(source, "rb") as src, open(os.path.join(package_dir, filename), "wb") as dst:
                    dst.write(src.read())

            result = evaluate_external_suite(temp_dir, label="Vendor Drop")
            self.assertEqual(result["scope"], "external")
            self.assertEqual(result["label"], "Vendor Drop")
            self.assertGreaterEqual(result["fixture_count"], 1)

            history = list_evaluation_runs(limit=10)
            self.assertTrue(any(item["scope"] == "external" for item in history))

    def test_external_evaluation_summary_includes_source_family_and_weakest_cases(self):
        result = evaluate_fixture_suite()
        self.assertIn("source_families", result["cam_health"])
        self.assertIn("weakest_boards", result["parser_health"])

    def test_evaluation_history_summary_reports_trends(self):
        evaluate_fixture_suite()
        summary = summarize_evaluation_history(limit=10)
        self.assertIn("history_count", summary)
        self.assertIn("fixture_runs", summary)
        self.assertIn("fixture_parser_confidence_trend", summary)

    def test_altium_parser_handles_alias_fields_and_units(self):
        with tempfile.NamedTemporaryFile("w", suffix=".pcbdocascii", delete=False) as handle:
            handle.write("RECORD=COMPONENT|RefDes=U9|Footprint=ADC|LocationX=10.0mm|LocationY=11.0mm|Layer=TopLayer\n")
            handle.write("RECORD=PADSTACK|ComponentRef=U9|Number=1|NetName=AIN|LocationX=10.0mm|LocationY=11.0mm|Diameter=0.8mm|HoleSize=0.3mm|Layer=TopLayer\n")
            handle.write("RECORD=TRACKARC|NetName=AIN|XStart=10.0mm|YStart=11.0mm|XEnd=18.0mm|YEnd=11.0mm|LineWidth=0.18mm|Layer=TopLayer\n")
            handle.write("RECORD=REGIONVERTEX|X=0mm|Y=0mm\n")
            handle.write("RECORD=REGIONVERTEX|X=4mm|Y=0mm\n")
            handle.write("RECORD=REGIONVERTEX|X=4mm|Y=4mm\n")
            handle.write("RECORD=ENDREGION|Layer=TopLayer|Net=GND\n")
            handle.write("RECORD=BOARDLINE|XStart=0mm|YStart=0mm|XEnd=10mm|YEnd=0mm\n")
            path = handle.name
        try:
            pcb = parse_altium_ascii_file(path)
            self.assertGreaterEqual(len(pcb.components), 1)
            self.assertGreaterEqual(len(pcb.traces), 1)
            self.assertGreaterEqual(len(pcb.zones), 1)
            self.assertGreaterEqual(len(pcb.outline_segments), 1)
        finally:
            os.remove(path)

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

        signoff = evaluate_signoff_readiness(
            {
                "score": 61,
                "risks": [{"severity": "high"}, {"severity": "critical"}],
                "parser_confidence": {"score": 74},
                "physics_summary": {"summary": {"worst_voltage_drop_mv": 82.0, "worst_impedance_mismatch_pct": 18.0}, "risks": [{"severity": "high"}]},
                "score_explanation": {"overflow_penalty": 0},
            }
        )
        self.assertEqual(signoff["status"], "ready")
        parser = inspect_parser_trust(
            {
                "parser_confidence": {"score": 82},
                "cam_summary": {
                    "active": True,
                    "readiness_score": 71,
                    "trust_call": "parser_watch",
                    "missing_signals": ["Missing drill data"],
                },
            }
        )
        self.assertEqual(parser["status"], "ready")
        self.assertEqual(parser["trust_call"], "parser_watch")

    def test_failed_job_is_requeued_when_attempts_remain(self):
        job = create_job("external_evaluation_suite", payload={"samples_dir": "missing-dir"}, max_attempts=2)
        job["attempt_count"] = 1
        processed = _handle_job_failure(job, ValueError("External evaluation samples directory is missing or unreadable."))
        self.assertEqual(processed["status"], "queued")
        refreshed = get_job(job["job_id"])
        self.assertEqual(refreshed["status"], "queued")
        self.assertEqual(refreshed["max_attempts"], 2)

    def test_review_and_audit_records_are_queryable(self):
        suffix = str(uuid4())[:8]
        owner = create_user("Lead Owner", f"lead-owner-{suffix}@example.com", "password123")
        project = create_project("Governance Workspace", owner=owner)
        update_project_review_status(project["project_id"], "ready_for_signoff")
        reviews = list_review_decisions(project_id=project["project_id"])
        self.assertGreaterEqual(len(reviews), 1)
        audit_events = list_audit_events(limit=20, event_type="project.review_status_updated")
        self.assertTrue(any(event["project_id"] == project["project_id"] for event in audit_events))

    def test_org_and_password_reset_flow(self):
        org = create_organization("Backend Test Org")
        user = create_user("Reset User", f"reset-{uuid4().hex[:8]}@example.com", "password123", organization_key=org["organization_key"])
        self.assertEqual(user["organization_key"], org["organization_key"])
        token_info = create_password_reset_token(user["email"])
        self.assertIsNotNone(token_info)
        self.assertTrue(reset_password_with_token(token_info["token"], "new-password"))
        invite = create_organization_invitation(org["organization_key"], f"invite-{uuid4().hex[:8]}@example.com")
        accepted = accept_organization_invitation(invite["token"], accepted_user_id=user["user_id"])
        self.assertEqual(accepted["organization_key"], org["organization_key"])

    def test_email_service_writes_outbox_when_smtp_is_not_configured(self):
        delivery = send_identity_email(
            f"notify-{uuid4().hex[:8]}@example.com",
            "verification",
            "token-123",
            context={"organization_name": "Silicore"},
        )
        self.assertIn(delivery["status"], {"queued", "sent"})

    def test_integration_registry_can_store_configs(self):
        config = upsert_integration_config("jira", "Program Jira", status="ready", config={"endpoint": "https://jira.example.com", "project_key": "HW"})
        self.assertEqual(config["integration_type"], "jira")
        integrations = list_integration_configs()
        self.assertTrue(any(item["integration_type"] == "jira" for item in integrations))

    def test_job_runner_processes_queued_signoff_packet(self):
        job = create_job("signoff_packet", payload={"context": {"board_name": "Queued Board", "release_note": "Ready after rerun."}})
        processed = process_queued_jobs(limit=5)
        self.assertTrue(any(item["job_id"] == job["job_id"] for item in processed))
        refreshed = get_job(job["job_id"])
        self.assertEqual(refreshed["status"], "completed")

    def test_job_claiming_marks_running_state(self):
        job = create_job("signoff_packet", payload={"context": {"board_name": "Claimed Board"}})
        claim_jobs("pytest-worker", limit=50, lease_seconds=90)
        matched = get_job(job["job_id"])
        self.assertIsNotNone(matched)
        self.assertEqual(matched["status"], "running")
        self.assertEqual(matched["claimed_by"], "pytest-worker")


if __name__ == "__main__":
    unittest.main()
