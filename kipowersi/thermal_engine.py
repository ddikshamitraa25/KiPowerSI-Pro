"""
KiPowerSI Pro - IPC-2221 Trace Thermal Hotspot Engine
=====================================================
This module evaluates steady-state trace temperature rise (Delta T) caused by Joule heating.
It implements empirical thermal equations from IPC-2221A ("Generic Standard on Printed Board Design").

IPC-2221 Thermal Standard Equations:
------------------------------------
    I = k * (Delta_T)^0.44 * (Area_mil2)^0.725

Solving for Temperature Rise (Delta_T):
    Delta_T = [ I / (k * Area_mil2^0.725) ]^(1 / 0.44)

Where:
    I           = RMS Branch Current (Amperes)
    Area_mil2   = Trace cross-sectional area in square mils (1 mm^2 = 1550 mil^2)
    k           = Thermal derating constant:
                  k = 0.048 for External Layers (F.Cu, B.Cu - direct convection)
                  k = 0.024 for Internal Layers (In1.Cu, In2.Cu - encapsulated in FR4)
"""

import math
from typing import Dict, List, Tuple
from .graph_extractor import NetGraph, Edge
from .ir_drop_solver import SolverResult


class ThermalResult:
    """
    Data container holding trace temperature rise and thermal hotspot classifications.
    """
    def __init__(self, ambient_temp_c: float):
        self.ambient_temp_c = ambient_temp_c
        self.edge_temp_rise: Dict[int, float] = {}      # edge_id -> Delta_T (°C)
        self.edge_final_temp: Dict[int, float] = {}     # edge_id -> Final Temperature (°C)
        self.edge_hotspot_status: Dict[int, str] = {}   # edge_id -> "SAFE", "WARNING", "CRITICAL"
        self.max_temp_rise: float = 0.0                 # Peak temperature rise across board (°C)
        self.hottest_edge_id: int = 0                   # Edge ID of peak thermal hotspot
        self.total_power_loss_watts: float = 0.0        # Total net copper power dissipation (Watts)


class ThermalEngine:
    """
    Thermal calculation engine implementing IPC-2221 standard heating formulas.
    """
    def __init__(self, ambient_temp_c: float = 25.0, warning_temp_rise: float = 10.0, critical_temp_rise: float = 30.0):
        self.ambient_temp_c = ambient_temp_c
        self.warning_temp_rise = warning_temp_rise     # Threshold for thermal warning (10°C)
        self.critical_temp_rise = critical_temp_rise   # Threshold for critical hotspot (30°C)

    def calculate(self, net_graph: NetGraph, solver_result: SolverResult) -> ThermalResult:
        """
        Calculates trace temperature rise for every branch edge in net_graph.
        """
        result = ThermalResult(self.ambient_temp_c)
        max_dt = 0.0
        hottest_e = 0
        total_p = 0.0

        for edge in net_graph.edges:
            current_a = solver_result.edge_currents.get(edge.edge_id, 0.0)
            power_w = solver_result.edge_power_dissipation.get(edge.edge_id, 0.0)
            total_p += power_w

            # Step 1: Select IPC-2221 k factor based on layer position
            is_internal = "in" in edge.layer.lower() or "inner" in edge.layer.lower()
            k_factor = 0.024 if is_internal else 0.048  # IPC-2221 constants

            # Step 2: Convert cross-sectional area from mm^2 to mil^2 (1 mm^2 = 1550 mil^2)
            area_mm2 = edge.cross_section_area_mm2
            area_mil2 = area_mm2 * 1550.0

            # Step 3: Evaluate IPC-2221 temperature rise equation
            if current_a <= 1e-6 or area_mil2 <= 0:
                delta_t = 0.0
            else:
                try:
                    denominator = k_factor * (area_mil2 ** 0.725)
                    if denominator > 0:
                        val = current_a / denominator
                        delta_t = val ** (1.0 / 0.44)  # 1 / 0.44 = 2.2727...
                    else:
                        delta_t = 0.0
                except (OverflowError, ValueError):
                    delta_t = 999.0  # Thermal runaway safeguard limit

            final_temp = self.ambient_temp_c + delta_t

            if delta_t > max_dt:
                max_dt = delta_t
                hottest_e = edge.edge_id

            # Step 4: Classify thermal status
            if delta_t >= self.critical_temp_rise:
                status = "CRITICAL"
            elif delta_t >= self.warning_temp_rise:
                status = "WARNING"
            else:
                status = "SAFE"

            result.edge_temp_rise[edge.edge_id] = delta_t
            result.edge_final_temp[edge.edge_id] = final_temp
            result.edge_hotspot_status[edge.edge_id] = status

        result.max_temp_rise = max_dt
        result.hottest_edge_id = hottest_e
        result.total_power_loss_watts = total_p

        return result
