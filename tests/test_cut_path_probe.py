import os
import sys
import tempfile
import unittest

BCNC_DIR = os.path.join(os.path.dirname(__file__), "..", "bCNC")
sys.path.insert(0, BCNC_DIR)
sys.path.insert(0, os.path.join(BCNC_DIR, "lib"))

from CNC import Block, CNC, GCode, Probe


class CutPathProbeTest(unittest.TestCase):
    def setUp(self):
        CNC.vars["wx"] = 0.0
        CNC.vars["wy"] = 0.0
        CNC.vars["wz"] = 0.0
        CNC.vars["safe"] = 3.0
        CNC.vars["prbcmd"] = "G38.2"
        CNC.vars["prbfeed"] = 10.0

    def test_points_follow_only_enabled_spindle_cutting_moves(self):
        gcode = GCode()
        header = Block("Header")
        header.extend(["G90", "G0 X-5 Y0", "M3"])
        cutting = Block("Cutting")
        cutting.extend([
            "G1 X15 Y0 F100",
            "M5",
            "G1 X0 Y5",
            "M4",
            "G0 X0 Y10",
            "G1 Z-1",
        ])
        disabled = Block("Disabled")
        disabled.extend(["M3", "G1 X10 Y10"])
        disabled.enable = False
        gcode.blocks = [header, cutting, disabled]

        points = gcode.cuttingProbePoints(0, 10, 0, 10, 5, 5)

        self.assertEqual(points, [(0.0, 0.0), (5.0, 0.0), (10.0, 0.0),
                                  (0.0, 10.0)])

    def test_sparse_scan_probes_only_requested_targets(self):
        probe = Probe()
        probe.xmin = 0.0
        probe.xmax = 10.0
        probe.ymin = 0.0
        probe.ymax = 10.0
        probe.xn = 3
        probe.yn = 3
        probe.xstep()
        probe.ystep()

        lines = probe.scan([(1.0, 2.0), (8.0, 9.0)])

        moves = [line for line in lines if line.startswith("G0X")]
        commands = [line for line in lines if line.startswith("G38.2")]
        self.assertEqual(moves, [
            "G0X1.0000Y2.0000",
            "G0X8.0000Y9.0000",
            "G0X1.0000Y2.0000",
        ])
        self.assertEqual(len(commands), 2)
        self.assertEqual(probe.mode, "scattered")
        self.assertEqual(probe.targets, [(1.0, 2.0), (8.0, 9.0)])

    def test_arc_targets_respect_probe_resolution(self):
        gcode = GCode()
        block = Block("Circle")
        block.extend([
            "G90",
            "G0 X10 Y0",
            "M3",
            "G2 X10 Y0 I-10 J0",
        ])
        gcode.blocks = [block]

        points = gcode.cuttingProbePoints(-10, 10, -10, 10, 5, 5)

        self.assertGreaterEqual(len(points), 12)
        self.assertLessEqual(len(points), 35)
        for x, y in points:
            self.assertAlmostEqual(x * x + y * y, 100.0, places=3)

    def test_sparse_points_interpolate_and_round_trip(self):
        probe = Probe()
        probe.xmin = 0.0
        probe.xmax = 10.0
        probe.ymin = 0.0
        probe.ymax = 10.0
        probe.xn = 3
        probe.yn = 3
        probe.xstep()
        probe.ystep()
        probe.scan([(0.0, 0.0), (10.0, 0.0), (10.0, 10.0)])
        probe.add(0.0, 0.0, 1.0)
        probe.add(10.0, 0.0, 2.0)
        probe.add(10.0, 10.0, 3.0)

        self.assertEqual(probe.interpolate(10.0, 0.0), 2.0)
        self.assertAlmostEqual(probe.interpolate(2.0, 4.0), 1.6)
        self.assertFalse(probe.start)

        handle, filename = tempfile.mkstemp(suffix=".probe")
        os.close(handle)
        try:
            probe.save(filename)
            loaded = Probe()
            loaded.load(filename)
        finally:
            os.unlink(filename)

        self.assertEqual(loaded.mode, "scattered")
        self.assertEqual(loaded.targets, probe.targets)
        self.assertEqual(loaded.points, probe.points)
        self.assertEqual(loaded.interpolate(10.0, 10.0), 3.0)


if __name__ == "__main__":
    unittest.main()
