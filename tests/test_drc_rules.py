import unittest
from kipowersi.graph_extractor import BoardGraphExtractor, NetGraph
from kipowersi.ir_drop_solver import IRDropSolver
from kipowersi.thermal_engine import ThermalEngine
from kipowersi.signal_integrity import SignalIntegrityEngine
from kipowersi.drc_rules import PDNDRCRuleChecker

class TestDRCRules(unittest.TestCase):
    def test_drc_rules_evaluation(self):
        extractor = BoardGraphExtractor()
        graph = NetGraph("+5V")
        extractor._populate_fallback_synthetic_graph(graph)

        solver = IRDropSolver()
        solver_res = solver.solve(graph, source_node_id=0, load_specs={3: 5.0}, source_voltage=5.0)

        thermal = ThermalEngine()
        thermal_res = thermal.calculate(graph, solver_res)

        si = SignalIntegrityEngine()
        si_res = si.analyze_net(graph)

        drc = PDNDRCRuleChecker(max_voltage_drop_pct=1.0) # Strict drop limit
        drc_res = drc.evaluate(graph, solver_res, thermal_res, si_res)

        self.assertGreater(len(drc_res.violations), 0)
        self.assertFalse(drc_res.passed)

if __name__ == "__main__":
    unittest.main()
