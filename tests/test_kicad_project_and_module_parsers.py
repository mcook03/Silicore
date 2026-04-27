import os
import shutil
import tempfile
import unittest

from engine.kicad_module_parser import parse_kicad_module_file
from engine.kicad_project_parser import parse_kicad_project_file


PROJECT_FILE = """
last_client=kicad
[general]
version=1
[pcbnew]
CopperLayerCount=2
BoardThickness=1.6
""".strip()

PCB_FILE = """
(kicad_pcb
  (layers
    (0 "F.Cu" signal)
    (31 "B.Cu" signal)
  )
  (net 0 "")
  (net 1 "GND")
  (footprint "custom:R"
    (layer "F.Cu")
    (at 10 10)
    (property "Reference" "R1")
    (property "Value" "10k")
    (pad 1 smd rect (at 0 0) (size 1 1) (layers "F.Cu") (net 1 "GND"))
  )
)
""".strip()

MODULE_FILE = """
(module TestPad (layer F.Cu) (tedit 55EC0594)
  (descr "Test module")
  (fp_text reference REF** (at 0 -3) (layer F.SilkS)
    (effects (font (size 1 1) (thickness 0.15)))
  )
  (fp_text value TestPad (at 0 3) (layer F.Fab)
    (effects (font (size 1 1) (thickness 0.15)))
  )
  (fp_line (start -1 -1) (end 1 -1) (layer F.CrtYd) (width 0.05))
  (fp_line (start 1 -1) (end 1 1) (layer F.CrtYd) (width 0.05))
  (pad 1 smd rect (at -1 0) (size 1.5 1.2) (layers F.Cu F.Paste F.Mask))
  (pad 2 smd rect (at 1 0) (size 1.5 1.2) (layers F.Cu F.Paste F.Mask))
)
""".strip()


class KiCadProjectAndModuleParserTests(unittest.TestCase):
    def test_project_parser_resolves_companion_pcb(self):
        tempdir = tempfile.mkdtemp(prefix="silicore_project_parser_", dir="/tmp")
        try:
            pro_path = os.path.join(tempdir, "demo.pro")
            pcb_path = os.path.join(tempdir, "demo.kicad_pcb")
            with open(pro_path, "w", encoding="utf-8") as file:
                file.write(PROJECT_FILE)
            with open(pcb_path, "w", encoding="utf-8") as file:
                file.write(PCB_FILE)

            pcb = parse_kicad_project_file(pro_path)
        finally:
            shutil.rmtree(tempdir, ignore_errors=True)

        self.assertEqual(pcb.source_format, "kicad_project")
        self.assertEqual(pcb.filename, "demo.pro")
        self.assertEqual(len(pcb.components), 1)
        self.assertEqual(pcb.metadata["project"]["companion_kind"], "pcb")
        self.assertEqual(pcb.metadata["project"]["copper_layer_count"], 2)

    def test_module_parser_builds_single_component_with_pads(self):
        fd, path = tempfile.mkstemp(suffix=".kicad_mod")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as file:
                file.write(MODULE_FILE)
            pcb = parse_kicad_module_file(path)
        finally:
            if os.path.exists(path):
                os.remove(path)

        self.assertEqual(pcb.source_format, "kicad_footprint")
        self.assertEqual(len(pcb.components), 1)
        self.assertEqual(len(pcb.components[0].pads), 2)
        self.assertEqual(pcb.metadata["footprint"]["pad_count"], 2)


if __name__ == "__main__":
    unittest.main()
