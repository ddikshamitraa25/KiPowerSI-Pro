# KiPowerSI Pro: KiCad 9 Plugin
## Intelligent Power Distribution Network (PDN), DC IR-Drop & Trace Thermal Parasitics Analyzer

[![KiCad 9 Compatible](https://img.shields.io/badge/KiCad-9.0%2B-blue.svg)](https://www.kicad.org/)
[![Python Version](https://img.shields.io/badge/Python-3.8%20%7C%203.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-green.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests Status](https://img.shields.io/badge/Tests-Passing%20(7%2F7)-brightgreen.svg)](#-automated-unit-testing)

---

##  Internship Submission Details
- **Program**: IIT Bombay FOSSEE eSim Semester Long Internship (Autumn 2026)
- **Task Category**: Task 6 - KiCad Plugin Development (CSE & Electronics Integration)
- **Target EDA Platform**: KiCad 9.0+ (`pcbnew` Python ActionPlugin System)
- **Submission Email**: `contact-esim@fossee.in`
- **Email Subject**: `eSim Semester Long Internship - Autumn 2026 Submission Task 6`

---

## 👨‍💻 Executive Summary & Problem Motivation

Modern Printed Circuit Board (PCB) designs feature high-density integrated circuits (FPGA, MCU, SoC) operating at low core voltages ($1.0\text{V} - 3.3\text{V}$) and drawing high transient currents. At these operational levels, even minor copper trace resistances introduce significant voltage drops (**DC IR-Drop**) and localized trace heating (**Joule Heating** $I^2R$), leading to signal instability, unexpected resets, and thermal degradation.

Commercial co-simulation tools (such as Ansys SIwave or Cadence Sigrity) are proprietary and prohibitively expensive for academic institutions and open-source hardware developers.

**KiPowerSI Pro** bridges **Computer Science** (Graph Algorithms, Finite Difference Nodal Linear Matrix Solvers, Geometric Parsing) and **Electronics Engineering** (IPC-2221 Trace Thermal Equations, Transmission Line Parasitics, Ohm's Nodal Analysis) into a clean, automated **KiCad 9 Action Plugin**.

---

##  Key Features & Module Overview

| Feature | Engineering & CS Description | Relevant File |
| :--- | :--- | :--- |
| **Spatial Net Connectivity Graph Extraction** | Automatically parses track segments, via barrels, copper zones, and pads into a topological directed net graph $G=(V,E)$. Merges co-located endpoints within epsilon spatial tolerance. | [`graph_extractor.py`](kipowersi/graph_extractor.py) |
| **2D Nodal Linear Resistance Matrix Solver** | Assembles the global nodal conductance matrix $\mathbf{G} \cdot \mathbf{V} = \mathbf{I}$ using Kirchhoff's Current Law (KCL). Computes exact node potentials, branch currents, and current densities ($J$ in $\text{A/mm}^2$). | [`ir_drop_solver.py`](kipowersi/ir_drop_solver.py) |
| **IPC-2221 Trace Thermal Hotspot Engine** | Calculates steady-state trace temperature rise ($\Delta T$) using standard empirical IPC-2221 formulas for internal and external copper layers. Identifies thermal bottlenecks. | [`thermal_engine.py`](kipowersi/thermal_engine.py) |
| **Transmission Line Signal Integrity (SI) Engine** | Estimates Surface Microstrip and Internal Stripline characteristic impedance ($Z_0$), propagation delay ($t_{pd}$), per-unit length $L, C$, and capacitive crosstalk factor ($K_C$). | [`signal_integrity.py`](kipowersi/signal_integrity.py) |
| **Automated PDN & SI DRC Rule Engine** | Flags nets exceeding IR-drop limits ($>3\%$), current density limits ($>30\text{ A/mm}^2$), thermal rise limits ($>15\text{°C}$), and impedance mismatches ($Z_0 \neq 50\Omega$). | [`drc_rules.py`](kipowersi/drc_rules.py) |
| **Interactive HTML Report & SVG Layout Exporter** | Generates self-contained interactive HTML dashboards with embedded CSS, color-coded vector SVG layout thermal heatmaps, and tabular CSV spreadsheet exports. | [`report_generator.py`](kipowersi/report_generator.py) |
| **Dual Execution Interface (KiCad 9 + Headless CLI)** | Integrates directly into KiCad 9 PCB Editor via wxPython modal dialog, with full standalone Tkinter GUI and CLI fallback for headless testing. | [`gui.py`](kipowersi/gui.py) / [`plugin.py`](kipowersi/plugin.py) |

---

## 🔀 System Architecture & Process Flowcharts

### High-Level System Workflow

```
+-----------------------------------------------------------------------------------+
|                              KiCad 9 PCB Editor                                   |
|                        (pcbnew Python Action Plugin API)                          |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                        1. Spatial Board Net Graph Extractor                       |
|           Parses TRACK, VIA, PAD, ZONE into Topological Graph G = (V, E)           |
+-----------------------------------------------------------------------------------+
                                         |
            +----------------------------+----------------------------+
            |                            |                            |
            v                            v                            v
+------------------------+  +------------------------+  +---------------------------+
| 2. 2D Nodal IR-Drop    |  | 3. IPC-2221 Trace      |  | 4. Transmission Line      |
|    Matrix Solver       |  |    Thermal Engine      |  |    Signal Integrity (SI)  |
|    (G * V = I)         |  |    (Joule Heat ΔT)     |  |    (Z0, L, C, Kc)          |
+------------------------+  +------------------------+  +---------------------------+
            |                            |                            |
            +----------------------------+----------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                      5. Automated PDN & SI DRC Rule Engine                        |
|        (Evaluates IR-drop %, Current Density A/mm², ΔT °C, Z0 impedance)          |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                   6. Interactive Presentation & Exporter Pipeline                 |
|   - Native wxPython KiCad Modal Window / Standalone Tkinter GUI                   |
|   - Scalable Vector SVG Layout Heatmap (Green=Safe, Amber=Warning, Red=Critical)  |
|   - Self-Contained Interactive HTML Dashboard & CSV Spreadsheet Export            |
+-----------------------------------------------------------------------------------+
```

---

##  Mathematical & Electronics Foundations

### 1. Temperature-Corrected Copper Resistance
The electrical resistance $R$ of a trace segment of length $L$, width $w$, and copper thickness $t$ is calculated as:
$$R = \rho(T) \cdot \frac{L}{w \cdot t}$$

Where temperature-adjusted resistivity $\rho(T)$ is given by:
$$\rho(T) = \rho_{20} \cdot [1 + \alpha (T_{ambient} - 20^\circ\text{C})]$$

- $\rho_{20} = 1.72 \times 10^{-8}\ \Omega\cdot\text{m}$ (Annealed copper resistivity at 20°C)
- $\alpha = 0.00393 / ^\circ\text{C}$ (Temperature coefficient of resistance)

---

### 2. Nodal Conductance System Solvers ($\mathbf{G} \cdot \mathbf{V} = \mathbf{I}$)
Applying Kirchhoff's Current Law at each node $i$:
$$\sum_{j \in N(i)} g_{ij} (V_i - V_j) = I_{ext, i}$$

Where branch conductance $g_{ij} = \frac{1}{R_{ij}}$. Assembling into linear system form:
$$\mathbf{G} \cdot \mathbf{V} = \mathbf{I}$$

Boundary conditions fix the VRM source pad voltage to $V_{source}$ (e.g., $5.0\text{V}$), and matrix inversion yields all internal node potentials $\mathbf{V}$.

---

### 3. IPC-2221 Trace Thermal Heating Formula
Trace temperature rise ($\Delta T$ in $\text{°C}$) under RMS current load is evaluated using empirical IPC-2221 equations:
$$\Delta T = \left( \frac{I_{RMS}}{k \cdot A^{0.725}} \right)^{\frac{1}{0.44}}$$

- $I_{RMS}$ is branch current in Amperes.
- $A$ is trace cross-sectional area in $\text{mil}^2$ ($1\text{ mm}^2 = 1550\text{ mil}^2$).
- $k = 0.048$ for external surface copper layers (F.Cu, B.Cu).
- $k = 0.024$ for internal copper layers (In1.Cu, In2.Cu).

---

### 4. Surface Microstrip Transmission Line Impedance ($Z_0$)
For a surface trace of width $w$ routed over a ground plane at height $h$ with dielectric constant $\varepsilon_r$:
$$Z_0 = \frac{87}{\sqrt{\varepsilon_r + 1.41}} \cdot \ln \left( \frac{5.98 \cdot h}{0.8 \cdot w + t} \right) \quad [\Omega]$$

Propagation delay ($t_{pd}$):
$$t_{pd} = 3.333 \cdot \sqrt{0.475 \cdot \varepsilon_r + 0.67} \quad [\text{ns/m}]$$

---

##  Repository Deliverables & Structure

```
KiCad Plugin Development/
├── README.md                  # Comprehensive Overview, Mathematical Theory & Guide
├── DESIGN_DOCUMENT.md         # Detailed Software Architecture & Math Derivation
├── PROPOSAL.md                # Formal Proposal for IIT Bombay FOSSEE Selection
├── INSTALL.md                 # Step-by-Step Installation Manual for Windows, Linux, macOS
├── LICENSE                    # MIT Open Source License
├── requirements.txt           # Python Project Dependencies
├── setup.py                   # Standard Setuptools Package Installer
├── .gitignore                 # Git ignore rules for bytecode & outputs
├── kipowersi/                 # Core Python Package
│   ├── __init__.py            # Package Init & ActionPlugin Auto-Loader
│   ├── plugin.py              # KiCad 9 pcbnew.ActionPlugin & CLI Entrypoint
│   ├── gui.py                 # wxPython KiCad Dialog & Standalone Tkinter GUI
│   ├── graph_extractor.py     # KiCad Board Parser & Layout Net Graph Extractor
│   ├── ir_drop_solver.py      # 2D Nodal Resistance Mesh Solver (G * V = I)
│   ├── thermal_engine.py      # IPC-2221 Trace Heating & Thermal Hotspot Engine
│   ├── signal_integrity.py    # Microstrip/Stripline Impedance Z0 & Crosstalk Engine
│   ├── drc_rules.py           # Automated PDN & SI DRC Rule Checker
│   └── report_generator.py   # HTML Report, SVG Vector Heatmap, & CSV Exporter
├── sample_board/              # Test KiCad 9 PCB Project File
│   ├── test_power_board.kicad_pcb # PCB layout with power rails (+5V, +3V3, GND)
│   └── test_power_board.kicad_pro # KiCad 9 project file
└── tests/                     # Self-Contained Automated Unit Test Suite
    ├── test_graph_extractor.py
    ├── test_ir_drop_solver.py
    ├── test_thermal_engine.py
    ├── test_signal_integrity.py
    ├── test_drc_rules.py
    └── test_report_generator.py
```

---

## 🛠️ Step-by-Step Installation & Usage Guide

### Option 1: Native KiCad 9 Plugin Mode

1. Locate your KiCad 9 scripting plugins folder:
   - **Windows**: `%APPDATA%\kicad\9.0\scripting\plugins\`
   - **Linux**: `~/.local/share/kicad/9.0/scripting/plugins/`
   - **macOS**: `~/Library/Preferences/kicad/9.0/scripting/plugins/`

2. Copy the [`kipowersi`](kipowersi/) directory into the plugins folder.

3. Launch **KiCad 9 PCB Editor** -> Go to **Tools -> External Plugins -> Refresh Plugins**. Click **KiPowerSI Pro** to open the modal UI window.

---

### Option 2: Standalone CLI / GUI Mode

You can run **KiPowerSI Pro** outside of KiCad using standard Python:

```bash
# 1. Run CLI analysis on the provided sample board
python -m kipowersi.plugin --board sample_board/test_power_board.kicad_pcb --net +5V --voltage 5.0 --current 2.0

# 2. Launch Standalone Tkinter GUI
python -m kipowersi.gui
```

---

## 🧪 Automated Unit Testing

The project features a self-contained unit test suite in [`tests/`](tests/) requiring zero external testing packages.

Run the test suite:
```bash
python -m unittest discover -s tests -v
```

Expected Terminal Output:
```text
test_drc_rules_evaluation (test_drc_rules.TestDRCRules.test_drc_rules_evaluation) ... ok
test_extract_from_sample_file (test_graph_extractor.TestGraphExtractor.test_extract_from_sample_file) ... ok
test_synthetic_graph_building (test_graph_extractor.TestGraphExtractor.test_synthetic_graph_building) ... ok
test_ir_drop_solver_accuracy (test_ir_drop_solver.TestIRDropSolver.test_ir_drop_solver_accuracy) ... ok
test_report_generator (test_report_generator.TestReportGenerator.test_report_generator) ... ok
test_signal_integrity_microstrip (test_signal_integrity.TestSignalIntegrity.test_signal_integrity_microstrip) ... ok
test_thermal_engine_calculations (test_thermal_engine.TestThermalEngine.test_thermal_engine_calculations) ... ok

----------------------------------------------------------------------
Ran 7 tests in 0.270s

OK
```

---

## 📜 License & Contact

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for details.

Designed and developed for the **FOSSEE eSim Team at IIT Bombay**.  
**Submission Email**: `contact-esim@fossee.in`  
**Subject**: `eSim Semester Long Internship - Autumn 2026 Submission Task 6`
