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
            if os.path.isdir(path):
                shutil.rmtree(path, ignore_errors=True)
            elif os.path.exists(path):
                os.remove(path)

    def _make_tempdir(self, prefix):
        path = tempfile.mkdtemp(prefix=prefix, dir="/tmp")
        self.tempdirs.append(path)
        return path

    def _make_tempfile(self, suffix, content):
        fd, path = tempfile.mkstemp(suffix=suffix, dir="/tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            file.write(content)
        self.tempdirs.append(path)
        return path

    def test_single_analysis_writes_manifest_and_rule_transparency(self):
        output_dir = self._make_tempdir("silicore_single_test_")
        result = run_single_analysis_from_path(
            "fixtures/mixed_signal_noise_board.kicad_pcb",
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
        with open(result["report_md_path"], "r", encoding="utf-8") as file:
            report_markdown = file.read()
        first_risk = analysis["risks"][0]

        self.assertEqual(manifest["run_type"], "single")
        self.assertEqual(len(manifest["artifacts"]), 3)
        self.assertIn(".kicad_pcb", manifest["parser_capabilities"])
        self.assertTrue(first_risk.get("trigger_condition"))
        self.assertTrue(first_risk.get("threshold_label"))
        self.assertTrue(first_risk.get("observed_label"))
        self.assertIn("Review Readiness", report_markdown)
        self.assertIn("Traceability:", report_markdown)

    def test_project_analysis_writes_manifest_and_ranked_boards(self):
        output_dir = self._make_tempdir("silicore_project_test_")
        result = analyze_project_paths(
            [
                "fixtures/high_speed_pair_bad.kicad_pcb",
                "fixtures/mixed_signal_noise_board.kicad_pcb",
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
        with open(result["summary_md_path"], "r", encoding="utf-8") as file:
            project_report = file.read()

        self.assertEqual(manifest["run_type"], "project")
        self.assertEqual(len(manifest["artifacts"]), 3)
        self.assertGreaterEqual(len(project_summary["boards"]), 2)
        self.assertEqual(project_summary["boards"][0]["rank"], 1)
        self.assertIn("Review Readiness", project_report)
        self.assertIn("Traceability:", project_report)

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

    def test_severely_penalized_boards_use_soft_floor_instead_of_zero(self):
        result = run_single_analysis_from_path(
            "fixtures/high_speed_pair_bad.kicad_pcb",
            config=self.config,
        )

        explanation = result.get("score_explanation") or {}
        self.assertGreater(result["score"], 0)
        self.assertEqual(explanation.get("floor_mode"), "soft_floor")
        self.assertGreater(explanation.get("overflow_penalty_raw_10", 0), 0)

    def test_single_analysis_includes_physics_integrity_summary(self):
        result = run_single_analysis_from_path(
            "fixtures/high_speed_pair_bad.kicad_pcb",
            config=self.config,
        )

        physics_summary = result.get("physics_summary") or {}
        self.assertTrue(physics_summary.get("enabled"))
        self.assertIn("signal_models", physics_summary)
        self.assertIn("power_models", physics_summary)
        self.assertGreaterEqual(len(physics_summary.get("signal_models") or []), 1)
        self.assertGreaterEqual(len(physics_summary.get("risks") or []), 1)

    def test_single_analysis_includes_cam_summary_for_directory_bundle(self):
        result = run_single_analysis_from_path(
            "fixtures/gerber_cam_vendor_incomplete",
            config=self.config,
        )

        cam_summary = result.get("cam_summary") or {}
        self.assertTrue(cam_summary.get("active"))
        self.assertEqual(cam_summary.get("source_format"), "gerber_cam")
        self.assertTrue(cam_summary.get("missing_signals"))
        self.assertTrue(cam_summary.get("remediation_steps"))

    def test_single_analysis_accepts_kicad_schematic_inputs(self):
        schematic_content = """
(kicad_sch (version 20230121) (generator eeschema)
  (lib_symbols
    (symbol "Device:R"
      (property "Reference" "R" (at 0 2.54 0) (effects (font (size 1.27 1.27))))
      (property "Value" "R" (at 0 -2.54 0) (effects (font (size 1.27 1.27))))
      (symbol "R_0_1"
        (pin passive line (at -2.54 0 0) (length 2.54)
          (name "~" (effects (font (size 1.27 1.27))))
          (number "1" (effects (font (size 1.27 1.27))))
        )
        (pin passive line (at 2.54 0 180) (length 2.54)
          (name "~" (effects (font (size 1.27 1.27))))
          (number "2" (effects (font (size 1.27 1.27))))
        )
      )
    )
  )
  (symbol (lib_id "Device:R") (at 10 10 0) (unit 1)
    (property "Reference" "R1" (at 10 12 0) (effects (font (size 1.27 1.27))))
    (property "Value" "10k" (at 10 8 0) (effects (font (size 1.27 1.27))))
    (pin "1" (uuid a1))
    (pin "2" (uuid a2))
  )
  (wire (pts (xy 5 10) (xy 7.46 10)) (stroke (width 0) (type default)) (uuid w1))
  (wire (pts (xy 12.54 10) (xy 15 10)) (stroke (width 0) (type default)) (uuid w2))
  (label "VIN" (at 5 10 0) (effects (font (size 1.27 1.27))))
  (hierarchical_label "VOUT" (shape output) (at 15 10 0) (effects (font (size 1.27 1.27))))
)
""".strip()
        input_path = self._make_tempfile(".kicad_sch", schematic_content)
        output_dir = self._make_tempdir("silicore_schematic_test_")

        result = run_single_analysis_from_path(
            input_path,
            config=self.config,
            output_dir=output_dir,
        )

        self.assertEqual(result["filename"], os.path.basename(input_path))
        self.assertIn("board_summary", result)
        self.assertEqual(result["board_summary"]["component_count"], 1)
        self.assertGreaterEqual(result["board_summary"]["net_count"], 2)

        manifest_path = os.path.join(output_dir, "export_manifest.json")
        with open(manifest_path, "r", encoding="utf-8") as file:
            manifest = json.load(file)

        self.assertIn(".kicad_sch", manifest["parser_capabilities"])
        self.assertEqual(manifest["parser_capabilities"][".kicad_sch"]["status"], "supported")

    def test_single_analysis_accepts_kicad_module_inputs(self):
        module_content = """
(module TestPad (layer F.Cu)
  (fp_text reference REF** (at 0 -3) (layer F.SilkS) (effects (font (size 1 1) (thickness 0.15))))
  (fp_text value TestPad (at 0 3) (layer F.Fab) (effects (font (size 1 1) (thickness 0.15))))
  (fp_line (start -1 -1) (end 1 -1) (layer F.CrtYd) (width 0.05))
  (pad 1 smd rect (at -1 0) (size 1.5 1.2) (layers F.Cu F.Paste F.Mask))
  (pad 2 smd rect (at 1 0) (size 1.5 1.2) (layers F.Cu F.Paste F.Mask))
)
""".strip()
        input_path = self._make_tempfile(".kicad_mod", module_content)
        output_dir = self._make_tempdir("silicore_module_test_")

        result = run_single_analysis_from_path(
            input_path,
            config=self.config,
            output_dir=output_dir,
        )

        self.assertEqual(result["filename"], os.path.basename(input_path))
        self.assertEqual(result["board_summary"]["component_count"], 1)

        manifest_path = os.path.join(output_dir, "export_manifest.json")
        with open(manifest_path, "r", encoding="utf-8") as file:
            manifest = json.load(file)

        self.assertIn(".kicad_mod", manifest["parser_capabilities"])
        self.assertEqual(manifest["parser_capabilities"][".kicad_mod"]["status"], "supported")

    def test_single_analysis_accepts_kicad_project_inputs(self):
        tempdir = self._make_tempdir("silicore_project_input_")
        pro_path = os.path.join(tempdir, "demo.pro")
        pcb_path = os.path.join(tempdir, "demo.kicad_pcb")
        with open(pro_path, "w", encoding="utf-8") as file:
            file.write("last_client=kicad\n[general]\nversion=1\n[pcbnew]\nCopperLayerCount=2\nBoardThickness=1.6\n")
        with open(pcb_path, "w", encoding="utf-8") as file:
            file.write("""
(kicad_pcb
  (layers (0 "F.Cu" signal) (31 "B.Cu" signal))
  (net 0 "")
  (net 1 "GND")
  (footprint "custom:R" (layer "F.Cu") (at 10 10) (property "Reference" "R1") (property "Value" "10k")
    (pad 1 smd rect (at 0 0) (size 1 1) (layers "F.Cu") (net 1 "GND"))
  )
)
""".strip())

        output_dir = self._make_tempdir("silicore_project_test_")
        result = run_single_analysis_from_path(
            pro_path,
            config=self.config,
            output_dir=output_dir,
        )

        self.assertEqual(result["filename"], "demo.pro")
        self.assertEqual(result["board_summary"]["component_count"], 1)

        manifest_path = os.path.join(output_dir, "export_manifest.json")
        with open(manifest_path, "r", encoding="utf-8") as file:
            manifest = json.load(file)

        self.assertIn(".pro", manifest["parser_capabilities"])
        self.assertEqual(manifest["parser_capabilities"][".pro"]["status"], "supported")


if __name__ == "__main__":
    unittest.main()
