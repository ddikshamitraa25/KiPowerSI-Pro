import unittest
from kipowersi.graph_extractor import BoardGraphExtractor, NetGraph
from kipowersi.signal_integrity import SignalIntegrityEngine

class TestSignalIntegrity(unittest.TestCase):
    def test_signal_integrity_microstrip(self):
        extractor = BoardGraphExtractor()
        graph = NetGraph("CLK_50MHz")
        extractor._populate_fallback_synthetic_graph(graph)

        si_engine = SignalIntegrityEngine(er=4.3, substrate_height_mm=1.0)
        si_res = si_engine.analyze_net(graph, target_z0=50.0)

        self.assertTrue(30.0 < si_res.char_impedance_z0 < 150.0)
        self.assertGreater(si_res.propagation_delay_ps_mm, 0.0)
        self.assertGreater(si_res.total_capacitance_pf, 0.0)
        self.assertGreater(si_res.total_inductance_nh, 0.0)

if __name__ == "__main__":
    unittest.main()
