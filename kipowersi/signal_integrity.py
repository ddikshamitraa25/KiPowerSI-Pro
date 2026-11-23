"""
KiPowerSI Pro - Transmission Line & Signal Integrity Engine
============================================================
This module calculates high-speed signal integrity parameters for PCB trace geometries.

Key Engineering Formulas:
-------------------------
1. Surface Microstrip Characteristic Impedance (Z0):
       Z0 = [ 87 / sqrt(er + 1.41) ] * ln( 5.98 * h / (0.8 * w + t) )

2. Internal Stripline Characteristic Impedance (Z0):
       Z0 = [ 60 / sqrt(er) ] * ln( 1.9 * B / (0.8 * w + t) )

3. Propagation Delay (t_pd):
       t_pd = 3.333 * sqrt( 0.475 * er + 0.67 )  [ns/m]

4. Parasitic Capacitance (C) and Inductance (L):
       C = t_pd / Z0  [pF/m]
       L = t_pd * Z0  [nH/m]

5. Reflection Coefficient (Gamma):
       Gamma = (Z_load - Z0) / (Z_load + Z0)

6. Capacitive Crosstalk Coupling Factor (Kc):
       Kc = 1 / [ 1 + (s / h)^2 ]
"""

import math
from typing import Dict, List, Tuple
from .graph_extractor import NetGraph, Edge


class SIResult:
    """
    Data container holding Signal Integrity transmission line parasitics.
    """
    def __init__(self, net_name: str):
        self.net_name = net_name
        self.char_impedance_z0: float = 50.0            # Characteristic impedance (Ohms)
        self.propagation_delay_ps_mm: float = 6.8       # Propagation delay (ps/mm)
        self.total_capacitance_pf: float = 0.0          # Net parasitic capacitance (pF)
        self.total_inductance_nh: float = 0.0           # Net parasitic inductance (nH)
        self.reflection_coefficient_gamma: float = 0.0  # Reflection coefficient Gamma
        self.crosstalk_kc: float = 0.05                 # Crosstalk coupling coefficient
        self.status: str = "MATCHED"                    # Impedance match status ('MATCHED' or 'MISMATCHED')


class SignalIntegrityEngine:
    """
    Transmission line parameter calculator for high-speed PCB nets.
    """
    def __init__(self, er: float = 4.3, substrate_height_mm: float = 1.0, copper_thickness_um: float = 35.0):
        self.er = er                                    # Relative permittivity of dielectric (FR4 = 4.3)
        self.h = substrate_height_mm                    # Substrate dielectric height (mm)
        self.t = copper_thickness_um / 1000.0           # Copper thickness (mm)

    def analyze_net(self, net_graph: NetGraph, target_z0: float = 50.0, load_z: float = 50.0) -> SIResult:
        """
        Calculates characteristic impedance Z0, propagation delay, parasitic L/C,
        and reflection coefficient for the trace segments in net_graph.
        """
        result = SIResult(net_graph.net_name)

        if not net_graph.edges:
            return result

        # Step 1: Calculate total trace length and average track width
        total_len_mm = sum(edge.length for edge in net_graph.edges if edge.edge_type == "track")
        if total_len_mm <= 0:
            total_len_mm = 10.0

        avg_w = sum(edge.width * edge.length for edge in net_graph.edges if edge.edge_type == "track") / total_len_mm
        avg_w = max(0.05, avg_w)

        # Step 2: Determine if track is Surface Microstrip or Internal Stripline
        first_layer = net_graph.edges[0].layer.lower()
        is_stripline = "in" in first_layer or "inner" in first_layer

        if is_stripline:
            # Stripline formula
            B = self.h * 2.0  # Total dielectric height between ground planes
            denom = 0.8 * avg_w + self.t
            z0 = (60.0 / math.sqrt(self.er)) * math.log(max(1.1, (1.9 * B) / denom))
            t_pd_ns_m = 3.333 * math.sqrt(self.er)
        else:
            # Surface Microstrip formula (IPC-2141 standard)
            denom = 0.8 * avg_w + self.t
            z0 = (87.0 / math.sqrt(self.er + 1.41)) * math.log(max(1.1, (5.98 * self.h) / denom))
            t_pd_ns_m = 3.333 * math.sqrt(0.475 * self.er + 0.67)

        # Convert propagation delay from ns/m to ps/mm (1 ns/m = 1 ps/mm)
        t_pd_ps_mm = t_pd_ns_m

        # Step 3: Per-unit length C (pF/mm) and L (nH/mm)
        c_p_mm = (t_pd_ns_m * 1e-9) / z0 * 1e12 / 1000.0  # pF/mm
        l_p_mm = (t_pd_ns_m * 1e-9) * z0 * 1e9 / 1000.0   # nH/mm

        total_c_pf = c_p_mm * total_len_mm
        total_l_nh = l_p_mm * total_len_mm

        # Step 4: Reflection Coefficient Gamma = (Z_load - Z0) / (Z_load + Z0)
        gamma = (load_z - z0) / (load_z + z0) if (load_z + z0) != 0 else 0.0

        # Step 5: Crosstalk coupling factor for standard 3W trace separation rule (separation = 2 * width)
        sep_mm = 2.0 * avg_w
        crosstalk_kc = 1.0 / (1.0 + (sep_mm / self.h)**2)

        result.char_impedance_z0 = z0
        result.propagation_delay_ps_mm = t_pd_ps_mm
        result.total_capacitance_pf = total_c_pf
        result.total_inductance_nh = total_l_nh
        result.reflection_coefficient_gamma = gamma
        result.crosstalk_kc = crosstalk_kc

        # Impedance tolerance check (±10% of target)
        z0_dev = abs(z0 - target_z0) / target_z0
        result.status = "MATCHED" if z0_dev <= 0.10 else "MISMATCHED"

        return result
