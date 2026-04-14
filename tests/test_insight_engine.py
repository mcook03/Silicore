import unittest

from engine.insight_engine import generate_comparison_insights


class InsightEngineClusteringTests(unittest.TestCase):
    def test_spacing_findings_cluster_by_pattern_not_literal_message(self):
        comparison = {
            "old_score": 7.2,
            "new_score": 5.8,
            "old_risks": [],
            "new_risks": [
                {
                    "rule_id": "spacing",
                    "category": "layout",
                    "severity": "high",
                    "message": "U1 and C1 are too close (1.41 units)",
                    "recommendation": "Increase spacing between these components.",
                    "components": ["U1", "C1"],
                    "metrics": {"distance": 1.41, "threshold": 3.0},
                },
                {
                    "rule_id": "spacing",
                    "category": "layout",
                    "severity": "high",
                    "message": "U2 and C2 are too close (1.00 units)",
                    "recommendation": "Increase spacing between these components.",
                    "components": ["U2", "C2"],
                    "metrics": {"distance": 1.0, "threshold": 3.0},
                },
                {
                    "rule_id": "spacing",
                    "category": "layout",
                    "severity": "high",
                    "message": "Q1 and D1 are too close (2.00 units)",
                    "recommendation": "Increase spacing between these components.",
                    "components": ["Q1", "D1"],
                    "metrics": {"distance": 2.0, "threshold": 3.0},
                },
            ],
        }

        insights = generate_comparison_insights(comparison)
        clusters = insights["clustered_added_risks"]

        self.assertEqual(len(clusters), 1)
        self.assertEqual(clusters[0]["count"], 3)
        self.assertEqual(clusters[0]["pattern_type"], "spacing")
        self.assertIn("1.0 to 2.0", clusters[0]["summary"])
        self.assertEqual(insights["noise_reduction_summary"]["suppressed_count"], 2)

    def test_recommendations_prioritize_systemic_issue_family(self):
        comparison = {
            "old_score": 8.1,
            "new_score": 6.0,
            "old_risks": [],
            "new_risks": [
                {
                    "rule_id": "spacing",
                    "category": "layout",
                    "severity": "high",
                    "message": "U1 and C1 are too close (1.41 units)",
                    "recommendation": "Increase spacing between these components.",
                    "components": ["U1", "C1"],
                    "metrics": {"distance": 1.41, "threshold": 3.0},
                },
                {
                    "rule_id": "spacing",
                    "category": "layout",
                    "severity": "high",
                    "message": "U2 and C2 are too close (1.10 units)",
                    "recommendation": "Increase spacing between these components.",
                    "components": ["U2", "C2"],
                    "metrics": {"distance": 1.1, "threshold": 3.0},
                },
                {
                    "rule_id": "thermal",
                    "category": "thermal",
                    "severity": "medium",
                    "message": "U1 and C1 may create a thermal hotspot (1.41 units apart)",
                    "recommendation": "Review local thermal management.",
                    "components": ["U1", "C1"],
                    "metrics": {"distance": 1.41, "threshold": 4.0},
                },
            ],
        }

        insights = generate_comparison_insights(comparison)
        recommendations = insights["recommendations"]

        self.assertGreaterEqual(len(recommendations), 1)
        self.assertEqual(recommendations[0]["type"], "systemic_cluster_focus")
        self.assertIn("clustering", recommendations[0]["reason"])
        self.assertEqual(recommendations[0]["priority"], "high")


if __name__ == "__main__":
    unittest.main()
