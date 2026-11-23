import unittest
from kipowersi.graph_extractor import BoardGraphExtractor, NetGraph
from kipowersi.ir_drop_solver import IRDropSolver

class TestIRDropSolver(unittest.TestCase):
    def test_ir_drop_solver_accuracy(self):
        extractor = BoardGraphExtractor()
        graph = NetGraph("+5V")
        extractor._populate_fallback_synthetic_graph(graph)

        solver = IRDropSolver(ambient_temp_c=25.0)
        # Source at Node 0 (5.0V), Load drawn at Node 3 (2.0A)
        res = solver.solve(graph, source_node_id=0, load_specs={3: 2.0}, source_voltage=5.0)

        self.assertAlmostEqual(res.source_voltage, 5.0, places=4)
        self.assertAlmostEqual(res.node_voltages[0], 5.0, places=4)
        self.assertLess(res.node_voltages[3], 5.0)
        self.assertGreater(res.max_voltage_drop, 0.0)
        self.assertGreater(res.percentage_voltage_drop, 0.0)
        self.assertGreater(res.max_current_density, 0.0)

if __name__ == "__main__":
    unittest.main()
