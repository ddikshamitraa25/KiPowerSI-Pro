# Installation & Execution Guide: KiPowerSI Pro (KiCad 9 Plugin)

This document provides step-by-step instructions for installing, configuring, running, and testing the **KiPowerSI Pro** plugin on KiCad 9 for Windows, Linux, and macOS.

---

## 1. System Requirements

- **KiCad Version**: KiCad 9.0 or higher
- **Python Version**: Python 3.8+ (included automatically with KiCad installation)
- **Supported Operating Systems**:
  - Windows 10 / 11 (64-bit)
  - Ubuntu 20.04 / 22.04 / 24.04 LTS & Debian-based Linux
  - macOS Monterey / Ventura / Sonoma / Sequoia

---

## 2. Option A: Installing inside KiCad 9 (Action Plugin Mode)

### Step 1: Locate KiCad 9 Scripting Plugins Directory

Depending on your Operating System, copy the `kipowersi` plugin folder into the corresponding KiCad 9 plugins directory:

#### **Windows**:
```cmd
%APPDATA%\kicad\9.0\scripting\plugins\
```
*(Path typically expands to: `C:\Users\<Username>\AppData\Roaming\kicad\9.0\scripting\plugins\`) *

#### **Linux**:
```bash
~/.local/share/kicad/9.0/scripting/plugins/
# or
~/.config/kicad/9.0/scripting/plugins/
```

#### **macOS**:
```bash
~/Library/Preferences/kicad/9.0/scripting/plugins/
# or
~/Library/Application Support/kicad/9.0/scripting/plugins/
```

---

### Step 2: Copy Plugin Files

Extract or copy the project files into the plugins directory such that the structure is:

```
plugins/
└── kipowersi/
    ├── __init__.py
    ├── plugin.py
    ├── gui.py
    ├── graph_extractor.py
    ├── ir_drop_solver.py
    ├── thermal_engine.py
    ├── signal_integrity.py
    ├── drc_rules.py
    └── report_generator.py
```

---

### Step 3: Enable Plugin in KiCad 9 PCB Editor

1. Open **KiCad 9**.
2. Open any PCB layout (`.kicad_pcb` file) or load the provided sample board (`sample_board/test_power_board.kicad_pcb`).
3. In the top toolbar, go to:  
   **Tools -> External Plugins -> Refresh Plugins**
4. You will now see **KiPowerSI Pro: PDN & Thermal Analyzer** listed under **Tools -> External Plugins**.
5. Click on **KiPowerSI Pro** or click its icon in the top Action Plugin toolbar to launch the interactive analysis dialog.

---

## 3. Option B: Running in Standalone GUI / CLI Mode

You can also run and evaluate **KiPowerSI Pro** as an independent application outside of KiCad. This is ideal for quick testing, batch processing, or environments where KiCad UI is not active.

### Step 1: Install Python Dependencies

Open terminal/command prompt in the project root folder and run:

```bash
pip install -r requirements.txt
```

### Step 2: Launch Standalone GUI

Run the standalone Tkinter interface:

```bash
python -m kipowersi.gui
```

### Step 3: Run Analysis via CLI on Sample Board

Run analysis directly against a `.kicad_pcb` file via command line:

```bash
python -m kipowersi.plugin --board sample_board/test_power_board.kicad_pcb --net +5V --voltage 5.0 --current 2.0
```

---

## 4. Running the Automated Test Suite

To execute the unit tests and verify all solver engines:

```bash
pytest tests/ -v
```

Expected output:
```text
tests/test_graph_extractor.py :: test_extract_graph PASSED
tests/test_ir_drop_solver.py :: test_solver_accuracy PASSED
tests/test_thermal_engine.py :: test_ipc2221_thermal PASSED
tests/test_signal_integrity.py :: test_microstrip_impedance PASSED
tests/test_drc_rules.py :: test_drc_checks PASSED
tests/test_report_generator.py :: test_html_export PASSED
```

---

## 5. Troubleshooting & FAQ

Q1: **The plugin icon does not appear in KiCad 9.**  
*Solution*: Ensure you placed the `kipowersi` directory inside the KiCad `9.0` scripting plugins folder (not `8.0` or `7.0`). Go to *Tools -> External Plugins -> Refresh Plugins*.

Q2: **`ModuleNotFoundError: No module named 'numpy'` in KiCad's Python console.**  
*Solution*: KiCad 9 includes standard library packages. KiPowerSI Pro features pure Python fallback math routines when numpy is not available, but installing numpy/scipy into KiCad's bundled Python environment improves solver speed for ultra-large boards.

Q3: **Can I run this on custom PCB boards?**  
*Solution*: Yes! Simply open your project in KiCad 9 PCB Editor and trigger the plugin. It automatically detects all net names (e.g., `+5V`, `+3V3`, `GND`, `VCC`) present on your board.
