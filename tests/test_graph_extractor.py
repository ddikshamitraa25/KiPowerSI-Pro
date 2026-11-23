import unittest
import os
from kipowersi.graph_extractor import BoardGraphExtractor, NetGraph

class TestGraphExtractor(unittest.TestCase):
    def test_synthetic_graph_building(self):
        extractor = BoardGraphExtractor()
        graph = NetGraph("+5V")
        extractor._populate_fallback_synthetic_graph(graph)

        self.assertEqual(len(graph.nodes), 5)
        self.assertEqual(len(graph.edges), 4)
        self.assertEqual(graph.nodes[0].component_ref, "J1_VRM")
        self.assertEqual(graph.nodes[3].component_ref, "U1_MCU")

    def test_extract_from_sample_file(self):
        sample_file = os.path.join(os.path.dirname(__file__), "..", "sample_board", "test_power_board.kicad_pcb")
        extractor = BoardGraphExtractor()
        graph = extractor.extract_from_file(sample_file, "+5V")

        self.assertGreater(len(graph.nodes), 0)
        self.assertGreater(len(graph.edges), 0)

if __name__ == "__main__":
    unittest.main()
