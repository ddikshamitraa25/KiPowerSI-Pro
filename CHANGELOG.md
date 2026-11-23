# Changelog

All notable changes to **KiPowerSI Pro** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-08-23

### Added
- **KiCad 9 Action Plugin Integration**: Full compatibility with KiCad 9 `pcbnew.ActionPlugin` framework.
- **Spatial Net Graph Extractor**: Parses tracks, vias, pads, and zones into topological directed graphs $G=(V,E)$.
- **2D Nodal IR-Drop Matrix Solver**: Formulates and solves Kirchhoff's nodal conductance system $\mathbf{G} \cdot \mathbf{V} = \mathbf{I}$.
- **IPC-2221 Trace Thermal Engine**: Computes steady-state trace temperature rise ($\Delta T$) and classifies hotspots.
- **Signal Integrity Engine**: Microstrip and Stripline characteristic impedance ($Z_0$), propagation delay ($t_{pd}$), parasitics ($L, C$), and capacitive crosstalk ($K_C$).
- **Automated DRC Rule Checker**: Flags voltage drops ($>3\%$), current density bottlenecks ($>30\text{ A/mm}^2$), and thermal rise ($>15\text{°C}$).
- **Interactive Presentation Pipeline**: Native wxPython KiCad dialog, standalone Tkinter GUI, vector SVG thermal heatmap layout exporter, and interactive HTML dashboard.
- **Automated Test Suite**: Zero-dependency `unittest` test suite covering all modules.
- **GitHub Actions CI/CD**: Automated multi-OS (Linux, Windows, macOS) and multi-Python matrix testing workflow.
