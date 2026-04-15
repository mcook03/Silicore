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


if __name__ == "__main__":
    unittest.main()
