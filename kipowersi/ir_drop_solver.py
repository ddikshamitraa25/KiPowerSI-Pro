"""
KiPowerSI Pro - DC Nodal IR-Drop & Current Density Solver
=========================================================
This module formulates and solves the system of linear equations G * V = I 
derived from applying Kirchhoff's Current Law (KCL) to a 2D copper net graph.

Mathematical Formulation:
-------------------------
For a network of N nodes:
    G * V = I

Where:
    G = Symmetric N x N nodal conductance matrix
        G[i][i] = sum of all branch conductances connected to node i
        G[i][j] = -1 * (conductance between node i and node j)
    V = Vector of unknown nodal potentials [V0, V1, ..., VN-1] (Volts)
    I = Vector of net injected/drawn nodal currents [I0, I1, ..., IN-1] (Amperes)

Boundary Conditions:
    - Fixed potential source node (VRM): V[source_node] = V_source
    - Specified load current sinks: I[load_node] = -I_load
"""

import math
from typing import Dict, List, Tuple
from .graph_extractor import NetGraph, Node, Edge


class SolverResult:
    """
    Data container holding all numerical outputs from the DC IR-Drop simulation.
    """
    def __init__(self, net_name: str, source_voltage: float, total_current: float):
        self.net_name = net_name
        self.source_voltage = source_voltage            # Source operating voltage (V)
        self.total_current = total_current              # Total drawn load current (A)
        self.node_voltages: Dict[int, float] = {}       # node_id -> Potential (V)
        self.edge_currents: Dict[int, float] = {}       # edge_id -> Branch Current (A)
        self.edge_current_densities: Dict[int, float] = {} # edge_id -> Current Density (A/mm^2)
        self.edge_power_dissipation: Dict[int, float] = {} # edge_id -> Joule Power (Watts)
        self.max_voltage_drop: float = 0.0              # Maximum voltage drop (V)
        self.percentage_voltage_drop: float = 0.0       # Maximum voltage drop (%)
        self.total_loop_resistance: float = 0.0         # Total equivalent net resistance (Ohms)
        self.worst_node_id: int = 0                     # Node ID suffering maximum drop
        self.max_current_density: float = 0.0           # Peak current density across layout (A/mm^2)
        self.worst_edge_id: int = 0                     # Edge ID carrying peak current density


class IRDropSolver:
    """
    Engine implementing DC Nodal Analysis for arbitrary 2D PCB trace topologies.
    """
    def __init__(self, ambient_temp_c: float = 25.0):
        self.ambient_temp_c = ambient_temp_c

    def solve(self, net_graph: NetGraph, source_node_id: int, 
              load_specs: Dict[int, float], source_voltage: float = 5.0) -> SolverResult:
        """
        Solves the nodal conductance matrix system G * V = I.

        Parameters:
            net_graph: Topological NetGraph containing nodes and edges.
            source_node_id: Node ID representing the voltage source regulator pad.
            load_specs: Mapping of load node IDs to drawn current in Amperes {node_id: current_A}.
            source_voltage: Operating voltage at the source regulator pad (Volts).
        """
        nodes = list(net_graph.nodes.values())
        N = len(nodes)

        if N == 0:
            raise ValueError("NetGraph contains no nodes to solve.")

        # Map node IDs to 0-based matrix index [0 .. N-1]
        node_id_to_idx = {node.node_id: i for i, node in enumerate(nodes)}
        idx_to_node_id = {i: node.node_id for i, node in enumerate(nodes)}

        if source_node_id not in node_id_to_idx:
            source_node_id = nodes[0].node_id

        src_idx = node_id_to_idx[source_node_id]

        # Step 1: Compute temperature-adjusted electrical resistance for every edge
        edge_resistances = {}
        for edge in net_graph.edges:
            R = edge.calculate_resistance(self.ambient_temp_c)
            edge_resistances[edge.edge_id] = max(R, 1e-7)  # Prevent divide-by-zero

        # Step 2: Initialize N x N Conductance Matrix G and N x 1 Current Vector I
        G = [[0.0] * N for _ in range(N)]
        I_vec = [0.0] * N

        # Step 3: Populate injected and drawn currents
        total_load_current = sum(load_specs.values())
        if total_load_current <= 0:
            total_load_current = 1.0  # Default 1 Amp load if unassigned

        for n_id, i_val in load_specs.items():
            if n_id in node_id_to_idx:
                # Drawn current leaves the node (negative sign)
                I_vec[node_id_to_idx[n_id]] -= abs(i_val)

        # Injected current enters at source node (positive sign)
        I_vec[src_idx] += total_load_current

        # Step 4: Assemble Conductance Matrix G
        for edge in net_graph.edges:
            i = node_id_to_idx[edge.start_node.node_id]
            j = node_id_to_idx[edge.end_node.node_id]
            g_ij = 1.0 / edge_resistances[edge.edge_id]  # Conductance g = 1 / R

            G[i][i] += g_ij
            G[j][j] += g_ij
            G[i][j] -= g_ij
            G[j][i] -= g_ij

        # Step 5: Enforce Source Node Boundary Condition (Fixed Voltage V[src] = V_source)
        for j in range(N):
            G[src_idx][j] = 0.0
        G[src_idx][src_idx] = 1.0
        I_vec[src_idx] = source_voltage

        # Step 6: Solve Linear System G * V = I
        V_sol = self._solve_linear_system(G, I_vec)

        # Step 7: Post-Process Results (Voltage Drops, Branch Currents, Power Loss)
        result = SolverResult(net_graph.net_name, source_voltage, total_load_current)
        min_v = source_voltage
        worst_n = source_node_id

        for i, v_val in enumerate(V_sol):
            n_id = idx_to_node_id[i]
            result.node_voltages[n_id] = v_val
            if v_val < min_v:
                min_v = v_val
                worst_n = n_id

        # Calculate IR-drop metrics
        result.max_voltage_drop = source_voltage - min_v
        result.percentage_voltage_drop = (result.max_voltage_drop / source_voltage) * 100.0 if source_voltage > 0 else 0.0
        result.worst_node_id = worst_n
        result.total_loop_resistance = result.max_voltage_drop / total_load_current if total_load_current > 0 else 0.0

        # Calculate branch currents, current densities, and power dissipation
        max_j = 0.0
        worst_e = 0
        for edge in net_graph.edges:
            v1 = result.node_voltages[edge.start_node.node_id]
            v2 = result.node_voltages[edge.end_node.node_id]
            v_diff = abs(v1 - v2)
            R = edge_resistances[edge.edge_id]
            
            # Ohm's Law: I = delta_V / R
            i_branch = v_diff / R
            
            # Joule Heating Power: P = I^2 * R
            power_w = (i_branch ** 2) * R
            
            # Current Density: J = I / Area (A/mm^2)
            area_mm2 = edge.cross_section_area_mm2
            j_density = i_branch / area_mm2 if area_mm2 > 0 else 0.0

            result.edge_currents[edge.edge_id] = i_branch
            result.edge_current_densities[edge.edge_id] = j_density
            result.edge_power_dissipation[edge.edge_id] = power_w

            if j_density > max_j:
                max_j = j_density
                worst_e = edge.edge_id

        result.max_current_density = max_j
        result.worst_edge_id = worst_e

        return result

    def _solve_linear_system(self, A: List[List[float]], b: List[float]) -> List[float]:
        """
        Solves linear system A * x = b using NumPy if installed, 
        or a pure Python Gaussian Elimination solver with partial pivoting.
        """
        try:
            import numpy as np
            A_np = np.array(A, dtype=float)
            b_np = np.array(b, dtype=float)
            v_sol = np.linalg.solve(A_np, b_np)
            return v_sol.tolist()
        except Exception:
            # Fallback: Pure Python Gaussian Elimination with Partial Pivoting
            n = len(b)
            M = [row[:] + [b[i]] for i, row in enumerate(A)]

            for i in range(n):
                # Partial pivoting for numerical stability
                max_row = max(range(i, n), key=lambda r: abs(M[r][i]))
                if abs(M[max_row][i]) < 1e-12:
                    continue
                M[i], M[max_row] = M[max_row], M[i]

                # Row reduction
                for r in range(i + 1, n):
                    factor = M[r][i] / M[i][i]
                    for c in range(i, n + 1):
                        M[r][c] -= factor * M[i][c]

            # Back substitution
            x = [0.0] * n
            for i in range(n - 1, -1, -1):
                if abs(M[i][i]) < 1e-12:
                    x[i] = 0.0
                else:
                    sum_ax = sum(M[i][j] * x[j] for j in range(i + 1, n))
                    x[i] = (M[i][n] - sum_ax) / M[i][i]
            return x
