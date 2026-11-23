import unittest
import os
import tempfile
from kipowersi.graph_extractor import BoardGraphExtractor, NetGraph
from kipowersi.ir_drop_solver import IRDropSolver
from kipowersi.thermal_engine import ThermalEngine
from kipowersi.signal_integrity import SignalIntegrityEngine
from kipowersi.drc_rules import PDNDRCRuleChecker
from kipowersi.report_generator import ReportGenerator

class TestReportGenerator(unittest.TestCase):
    def test_report_generator(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            extractor = BoardGraphExtractor()
            graph = NetGraph("+5V")
            extractor._populate_fallback_synthetic_graph(graph)

            solver = IRDropSolver()
            solver_res = solver.solve(graph, source_node_id=0, load_specs={3: 2.0}, source_voltage=5.0)

            thermal = ThermalEngine()
            thermal_res = thermal.calculate(graph, solver_res)

            si = SignalIntegrityEngine()
            si_res = si.analyze_net(graph)

            drc = PDNDRCRuleChecker()
            drc_res = drc.evaluate(graph, solver_res, thermal_res, si_res)

            report_gen = ReportGenerator(output_dir=tmp_dir)
            html_path = report_gen.generate_all(graph, solver_res, thermal_res, si_res, drc_res)

            self.assertTrue(os.path.exists(html_path))
            self.assertTrue(os.path.exists(os.path.join(tmp_dir, "+5V_heatmap.svg")))
            self.assertTrue(os.path.exists(os.path.join(tmp_dir, "+5V_summary.csv")))

            with open(html_path, "r", encoding="utf-8") as f:
                html_text = f.read()
                self.assertIn("KiPowerSI Pro", html_text)
                self.assertIn("+5V", html_text)

if __name__ == "__main__":
    unittest.main()
