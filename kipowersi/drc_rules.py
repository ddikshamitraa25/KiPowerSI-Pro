"""
KiPowerSI Pro - Automated PDN & Signal Integrity DRC Rule Engine
=================================================================
Evaluates numerical outputs from DC IR-drop solver, thermal engine, and SI engine
against configurable engineering DRC constraints:
1. Max DC IR-Drop (%)
2. Max Current Density (A/mm^2)
3. Max Trace Temperature Rise (°C)
4. Via Current Capacity (A)
5. Characteristic Impedance Match Tolerance (%)
"""

from typing import List, Dict
from .graph_extractor import NetGraph
from .ir_drop_solver import SolverResult
from .thermal_engine import ThermalResult
from .signal_integrity import SIResult


class DRCViolation:
    """
    Represents a single DRC rule failure or warning log entry.
    """
    def __init__(self, severity: str, rule_name: str, message: str, 
                 element_id: str, value_str: str, threshold_str: str):
        self.severity = severity        # "ERROR", "WARNING", "INFO"
        self.rule_name = rule_name
        self.message = message
        self.element_id = element_id
        self.value_str = value_str
        self.threshold_str = threshold_str

    def __repr__(self):
        return f"[{self.severity}] {self.rule_name}: {self.message} (Target: {self.threshold_str}, Found: {self.value_str})"


class DRCResult:
    """
    Aggregates all DRC violations and overall pass/fail compliance status.
    """
    def __init__(self):
        self.violations: List[DRCViolation] = []
        self.passed: bool = True
        self.error_count: int = 0
        self.warning_count: int = 0

    def add_violation(self, severity: str, rule_name: str, message: str, 
                      element_id: str, value_str: str, threshold_str: str):
        v = DRCViolation(severity, rule_name, message, element_id, value_str, threshold_str)
        self.violations.append(v)
        if severity == "ERROR":
            self.passed = False
            self.error_count += 1
        elif severity == "WARNING":
            self.warning_count += 1


class PDNDRCRuleChecker:
    """
    Rule evaluator applying power delivery & signal integrity constraints.
    """
    def __init__(
        self,
        max_voltage_drop_pct: float = 3.0,
        max_current_density_a_mm2: float = 30.0,
        max_temp_rise_c: float = 15.0,
        max_via_current_a: float = 1.5,
        target_z0_ohm: float = 50.0,
        max_z0_tolerance_pct: float = 10.0
    ):
        self.max_voltage_drop_pct = max_voltage_drop_pct
        self.max_current_density_a_mm2 = max_current_density_a_mm2
        self.max_temp_rise_c = max_temp_rise_c
        self.max_via_current_a = max_via_current_a
        self.target_z0_ohm = target_z0_ohm
        self.max_z0_tolerance_pct = max_z0_tolerance_pct

    def evaluate(self, net_graph: NetGraph, solver_res: SolverResult, 
                 thermal_res: ThermalResult, si_res: SIResult) -> DRCResult:
        """
        Evaluates simulation results against all active DRC rules.
        """
        drc = DRCResult()

        # Rule 1: DC IR-Drop Limit Check (default max 3.0%)
        if solver_res.percentage_voltage_drop > self.max_voltage_drop_pct:
            drc.add_violation(
                severity="ERROR",
                rule_name="Excessive IR-Drop",
                message=f"Net '{net_graph.net_name}' exceeds maximum allowed DC voltage drop limit.",
                element_id=f"Node_{solver_res.worst_node_id}",
                value_str=f"{solver_res.percentage_voltage_drop:.2f}% ({solver_res.max_voltage_drop:.3f} V drop)",
                threshold_str=f"<= {self.max_voltage_drop_pct:.1f}%"
            )

        # Rule 2: Current Density Bottleneck Check (default max 30 A/mm^2)
        for edge_id, j_val in solver_res.edge_current_densities.items():
            if j_val > self.max_current_density_a_mm2:
                drc.add_violation(
                    severity="ERROR",
                    rule_name="High Current Density Bottleneck",
                    message=f"Trace segment edge {edge_id} carries excessive current density.",
                    element_id=f"Edge_{edge_id}",
                    value_str=f"{j_val:.2f} A/mm^2",
                    threshold_str=f"<= {self.max_current_density_a_mm2:.1f} A/mm^2"
                )

        # Rule 3: IPC-2221 Trace Thermal Rise Check (default max 15.0°C)
        for edge_id, dt_val in thermal_res.edge_temp_rise.items():
            if dt_val > self.max_temp_rise_c:
                severity = "ERROR" if dt_val > (self.max_temp_rise_c * 1.5) else "WARNING"
                drc.add_violation(
                    severity=severity,
                    rule_name="IPC-2221 Trace Thermal Hotspot",
                    message=f"Trace segment edge {edge_id} temperature rise is too high.",
                    element_id=f"Edge_{edge_id}",
                    value_str=f"+{dt_val:.1f} °C (Final: {thermal_res.edge_final_temp[edge_id]:.1f} °C)",
                    threshold_str=f"<= +{self.max_temp_rise_c:.1f} °C"
                )

        # Rule 4: Via Barrel Current Capacity Overload Check (default max 1.5A per via)
        for edge in net_graph.edges:
            if edge.edge_type == "via":
                curr = solver_res.edge_currents.get(edge.edge_id, 0.0)
                if curr > self.max_via_current_a:
                    drc.add_violation(
                        severity="WARNING",
                        rule_name="Via Current Overload",
                        message=f"Via edge {edge.edge_id} exceeds recommended single via current rating.",
                        element_id=f"Via_Edge_{edge.edge_id}",
                        value_str=f"{curr:.2f} A",
                        threshold_str=f"<= {self.max_via_current_a:.1f} A"
                    )

        # Rule 5: Signal Integrity Impedance Match Check
        z0 = si_res.char_impedance_z0
        dev_pct = (abs(z0 - self.target_z0_ohm) / self.target_z0_ohm) * 100.0
        if dev_pct > self.max_z0_tolerance_pct:
            drc.add_violation(
                severity="WARNING",
                rule_name="Impedance Mismatch",
                message=f"Characteristic impedance Z0 deviates from target {self.target_z0_ohm} Ohm.",
                element_id=f"Net_{net_graph.net_name}",
                value_str=f"{z0:.1f} Ohm ({dev_pct:.1f}% dev)",
                threshold_str=f"{self.target_z0_ohm:.0f} Ohm +/- {self.max_z0_tolerance_pct:.0f}%"
            )

        return drc
