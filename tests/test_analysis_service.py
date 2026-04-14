import json
import os
import shutil
import tempfile
import unittest

from engine.config_loader import load_config
from engine.services.analysis_service import analyze_project_paths, run_single_analysis_from_path


class AnalysisServiceExportTests(unittest.TestCase):
    def setUp(self):
        self.config = load_config("custom_config.json")
        self.tempdirs = []

    def tearDown(self):
        for path in self.tempdirs:
            shutil.rmtree(path, ignore_errors=True)

    def _make_tempdir(self, prefix):
        path = tempfile.mkdtemp(prefix=prefix, dir="/tmp")
        self.tempdirs.append(path)
        return path

    def test_single_analysis_writes_manifest_and_rule_transparency(self):
        output_dir = self._make_tempdir("silicore_single_test_")
        result = run_single_analysis_from_path(
            "fixtures/power_board_bad.kicad_pcb",
            config=self.config,
            output_dir=output_dir,
        )

        manifest_path = os.path.join(output_dir, "export_manifest.json")
        analysis_path = os.path.join(output_dir, "single_analysis.json")

        self.assertTrue(os.path.exists(manifest_path))
        self.assertTrue(os.path.exists(analysis_path))
        self.assertTrue(os.path.exists(result["report_html_path"]))

        with open(manifest_path, "r", encoding="utf-8") as file:
            manifest = json.load(file)
        with open(analysis_path, "r", encoding="utf-8") as file:
            analysis = json.load(file)
        first_risk = analysis["risks"][0]

        self.assertEqual(manifest["run_type"], "single")
        self.assertEqual(len(manifest["artifacts"]), 3)
        self.assertIn(".kicad_pcb", manifest["parser_capabilities"])
        self.assertTrue(first_risk.get("trigger_condition"))
        self.assertTrue(first_risk.get("threshold_label"))
        self.assertTrue(first_risk.get("observed_label"))

    def test_project_analysis_writes_manifest_and_ranked_boards(self):
        output_dir = self._make_tempdir("silicore_project_test_")
        result = analyze_project_paths(
            [
                "fixtures/power_board_good.kicad_pcb",
                "fixtures/power_board_bad.kicad_pcb",
            ],
            config=self.config,
            output_dir=output_dir,
        )

        manifest_path = os.path.join(output_dir, "export_manifest.json")
        project_path = os.path.join(output_dir, "project_summary.json")

        self.assertTrue(os.path.exists(manifest_path))
        self.assertTrue(os.path.exists(project_path))
        self.assertTrue(os.path.exists(result["summary_html_path"]))

        with open(manifest_path, "r", encoding="utf-8") as file:
            manifest = json.load(file)
        with open(project_path, "r", encoding="utf-8") as file:
            project_summary = json.load(file)

        self.assertEqual(manifest["run_type"], "project")
        self.assertEqual(len(manifest["artifacts"]), 3)
        self.assertGreaterEqual(len(project_summary["boards"]), 2)
        self.assertEqual(project_summary["boards"][0]["rank"], 1)

    def test_single_analysis_accepts_config_path_and_supports_brd_inputs(self):
        output_dir = self._make_tempdir("silicore_brd_test_")
        result = run_single_analysis_from_path(
            "fixtures/legacy_power_board.brd",
            config="custom_config.json",
            output_dir=output_dir,
        )

        manifest_path = os.path.join(output_dir, "export_manifest.json")

        self.assertTrue(os.path.exists(manifest_path))
        self.assertEqual(result["filename"], "legacy_power_board.brd")
        self.assertGreater(len(result["risks"]), 0)
        self.assertIn("board_summary", result)
        self.assertEqual(result["board_summary"]["component_count"], 8)

        with open(manifest_path, "r", encoding="utf-8") as file:
            manifest = json.load(file)

        self.assertIn(".brd", manifest["parser_capabilities"])
        self.assertEqual(manifest["parser_capabilities"][".brd"]["status"], "supported")


if __name__ == "__main__":
    unittest.main()
