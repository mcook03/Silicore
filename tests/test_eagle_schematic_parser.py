import os
import tempfile
import unittest

from engine.eagle_schematic_parser import parse_eagle_schematic_file


EAGLE_SCHEMATIC = """<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE eagle SYSTEM "eagle.dtd">
<eagle version="7.7.0">
  <drawing>
    <schematic>
      <parts>
        <part name="R1" library="rcl" deviceset="R-US_" device="" value="10k"/>
        <part name="C1" library="rcl" deviceset="C-US" device="" value="0.1uF"/>
      </parts>
      <sheets>
        <sheet>
          <instances>
            <instance part="R1" gate="G$1" x="10.16" y="20.32"/>
            <instance part="C1" gate="G$1" x="30.48" y="20.32"/>
          </instances>
          <nets>
            <net name="VIN" class="0">
              <segment>
                <pinref part="R1" gate="G$1" pin="1"/>
                <wire x1="5.08" y1="20.32" x2="10.16" y2="20.32" width="0.1524" layer="91"/>
                <label x="5.08" y="20.32" size="1.6764" layer="95"/>
              </segment>
            </net>
            <net name="VOUT" class="0">
              <segment>
                <pinref part="R1" gate="G$1" pin="2"/>
                <pinref part="C1" gate="G$1" pin="1"/>
                <wire x1="10.16" y1="20.32" x2="30.48" y2="20.32" width="0.1524" layer="91"/>
              </segment>
            </net>
          </nets>
        </sheet>
      </sheets>
    </schematic>
  </drawing>
</eagle>
"""


class EagleSchematicParserTests(unittest.TestCase):
    def test_parser_builds_components_nets_and_wires(self):
        fd, path = tempfile.mkstemp(suffix=".sch")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as file:
                file.write(EAGLE_SCHEMATIC)
            pcb = parse_eagle_schematic_file(path)
        finally:
            os.remove(path)

        self.assertEqual(pcb.source_format, "eagle_schematic")
        self.assertEqual(len(pcb.components), 2)
        self.assertGreaterEqual(len(pcb.nets), 2)
        self.assertGreaterEqual(len(pcb.traces), 2)
        self.assertEqual(pcb.metadata["parser"]["kind"], "eagle_schematic")


if __name__ == "__main__":
    unittest.main()
