import unittest
from kipowersi.graph_extractor import BoardGraphExtractor, NetGraph
from kipowersi.ir_drop_solver import IRDropSolver
from kipowersi.thermal_engine import ThermalEngine

class TestThermalEngine(unittest.TestCase):
    def test_thermal_engine_calculations(self):
        extractor = BoardGraphExtractor()
        graph = NetGraph("+5V")
        extractor._populate_fallback_synthetic_graph(graph)

        solver = IRDropSolver(ambient_temp_c=25.0)
        solver_res = solver.solve(graph, source_node_id=0, load_specs={3: 3.0}, source_voltage=5.0)

        thermal = ThermalEngine(ambient_temp_c=25.0)
        thermal_res = thermal.calculate(graph, solver_res)

        self.assertEqual(thermal_res.ambient_temp_c, 25.0)
        self.assertGreater(thermal_res.max_temp_rise, 0.0)
        self.assertGreater(thermal_res.total_power_loss_watts, 0.0)
        self.assertEqual(len(thermal_res.edge_hotspot_status), len(graph.edges))

if __name__ == "__main__":
    unittest.main()
