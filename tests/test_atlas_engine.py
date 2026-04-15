import unittest

from engine.atlas_engine import answer_atlas_question


class AtlasEngineTests(unittest.TestCase):
    def test_board_question_resolves_domain_and_followups(self):
        response = answer_atlas_question(
            "board",
            "Why is the score low on this board?",
            context={
                "score": 42,
                "posture": "This board is at risk.",
                "dominant_domain": "Power Integrity",
                "risk_sources": [
                    {
                        "id": "risk-1",
                        "domain": "power integrity",
                        "category": "power_integrity",
                        "severity": "high",
                        "message": "Power rail is too narrow",
                        "components": ["U1"],
                        "nets": ["VCC"],
                    }
                ],
            },
            history=[],
        )

        self.assertEqual(response["intent"], "score")
        self.assertTrue(response["follow_ups"])
        self.assertIn("Power", response["detail"])

    def test_project_follow_up_uses_history_intent(self):
        response = answer_atlas_question(
            "project",
            "go deeper",
            context={
                "health_score": 61,
                "trend_summary": "Workspace trend is mixed.",
                "trusted_focus_items": [{"category": "Layout", "message": "Layout repeats"}],
            },
            history=[{"role": "assistant", "intent": "workspace_momentum", "copy": "Previous answer"}],
        )

        self.assertEqual(response["intent"], "workspace_momentum")
        self.assertIn("Atlas", response["detail"])

    def test_compare_question_resolves_approval(self):
        response = answer_atlas_question(
            "compare",
            "Can I approve this revision?",
            context={
                "signoff_note": "This revision is not ready for approval.",
                "focus_sources": [{"id": "compare-1", "label": "USB regression", "components": ["U1"], "nets": ["USB_DP"]}],
            },
            history=[],
        )

        self.assertEqual(response["intent"], "approval")
        self.assertEqual(response["title"], "Approval Readiness")
        self.assertTrue(response["citations"])

    def test_board_question_can_explain_signoff_and_physics_context(self):
        response = answer_atlas_question(
            "board",
            "Am I signoff ready and what is the model saying?",
            context={
                "score": 64,
                "release_note": "Board is not yet ready for signoff.",
                "signoff_gate": {
                    "decision": "needs_validation",
                    "label": "Needs Validation",
                    "summary": "Board is not yet ready for signoff.",
                    "release_score": 58,
                    "blockers": ["Estimated IR drop peaks at 88.0 mV."],
                    "next_checks": ["Measure the worst power rail under load."],
                },
                "parser_confidence": {"score": 81, "component_count": 12, "trace_count": 28, "outline_count": 4},
                "physics_summary": {
                    "signal_models": [{"net_name": "CLK", "impedance_ohms": 73.9, "mismatch_pct": 47.9, "delay_ps": 694.6}],
                    "power_models": [{"net_name": "VBUS", "voltage_drop_mv": 88.0, "current_density_a_per_mm2": 17.4}],
                    "summary": {"worst_impedance_mismatch_pct": 47.9, "worst_voltage_drop_mv": 88.0},
                    "assumptions": {"dielectric_er": 4.2, "dielectric_height_mm": 0.18},
                },
                "risk_sources": [{"severity": "high", "message": "Power bottleneck", "domain": "power integrity"}],
            },
            history=[],
        )

        self.assertEqual(response["intent"], "signoff")
        self.assertIn("release score", response["detail"].lower())
        self.assertIn("parser confidence", response["detail"].lower())

        physics_response = answer_atlas_question(
            "board",
            "What is the physics model saying?",
            context={
                "physics_summary": {
                    "signal_models": [{"net_name": "CLK", "impedance_ohms": 73.9, "mismatch_pct": 47.9, "delay_ps": 694.6}],
                    "power_models": [{"net_name": "VBUS", "voltage_drop_mv": 88.0, "current_density_a_per_mm2": 17.4}],
                    "summary": {"worst_impedance_mismatch_pct": 47.9, "worst_voltage_drop_mv": 88.0},
                    "assumptions": {"dielectric_er": 4.2, "dielectric_height_mm": 0.18},
                },
                "risk_sources": [{"severity": "high", "message": "Power bottleneck", "domain": "power integrity"}],
            },
            history=[],
        )
        self.assertEqual(physics_response["intent"], "physics")
        self.assertIn("modeled", physics_response["answer"].lower())

    def test_board_question_can_explain_stackup_and_subsystems(self):
        stackup_response = answer_atlas_question(
            "board",
            "What does the stackup look like?",
            context={
                "stackup_summary": {
                    "style": "two_layer",
                    "layer_count": 2,
                    "reference_coverage_pct": 30,
                    "concerns": ["Two-layer stackup limits return-path containment on fast nets."],
                },
                "risk_sources": [{"message": "Return path weak", "severity": "high", "domain": "signal integrity"}],
            },
            history=[],
        )
        self.assertEqual(stackup_response["intent"], "stackup")
        self.assertIn("two layer", stackup_response["answer"].lower())

        subsystem_response = answer_atlas_question(
            "board",
            "How are the subsystems interacting?",
            context={
                "subsystem_summary": {
                    "dominant_subsystem": "Power",
                    "summary": "Dominant subsystem pressure is Power.",
                    "interaction_risks": [{"message": "Power and analog subsystems may need tighter isolation review."}],
                },
                "risk_sources": [{"message": "Analog noise risk", "severity": "medium", "domain": "power integrity"}],
            },
            history=[],
        )
        self.assertEqual(subsystem_response["intent"], "subsystem")
        self.assertIn("dominant subsystem pressure", subsystem_response["answer"].lower())


if __name__ == "__main__":
    unittest.main()
