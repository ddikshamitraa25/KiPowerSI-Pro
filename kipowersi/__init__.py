"""
KiPowerSI Pro: Intelligent Power Distribution Network (PDN), IR-Drop & Thermal Parasitics Analyzer for KiCad 9
"""

__version__ = "1.0.0"
__author__ = "Anurag Thakur"

from .graph_extractor import BoardGraphExtractor, NetGraph
from .ir_drop_solver import IRDropSolver, SolverResult
from .thermal_engine import ThermalEngine, ThermalResult
from .signal_integrity import SignalIntegrityEngine, SIResult
from .drc_rules import PDNDRCRuleChecker, DRCResult
from .report_generator import ReportGenerator

try:
    from .plugin import KiPowerSIActionPlugin
    plugin_instance = KiPowerSIActionPlugin()
    plugin_instance.register()
except Exception as e:
    # Graceful fallback when running in standalone mode outside of KiCad pcbnew
    pass
