import os
import sys
import argparse

# Try loading pcbnew (KiCad 9 Python API)
try:
    import pcbnew  # type: ignore
    KICAD_AVAILABLE = True
except ImportError:
    KICAD_AVAILABLE = False
    # Mock ActionPlugin base class for standalone execution
    class _ActionPluginMock:
        def register(self): pass
        def defaults(self): pass
        def Run(self): pass

    class _PcbnewMock:
        ActionPlugin = _ActionPluginMock
        @staticmethod
        def GetBoard(): return None

    pcbnew = _PcbnewMock()  # type: ignore

from .gui import launch_gui, run_analysis_pipeline

class KiPowerSIActionPlugin(pcbnew.ActionPlugin):
    """KiCad 9 ActionPlugin implementation for KiPowerSI Pro."""

    def defaults(self):
        self.name = "KiPowerSI Pro: PDN & Thermal Analyzer"
        self.category = "Power & Signal Integrity"
        self.description = "Automated Power Distribution Network (PDN) DC IR-Drop, IPC-2221 Trace Thermal Hotspot, and Transmission Line SI Analyzer for KiCad 9."
        self.show_toolbar_button = True
        self.icon_file_name = os.path.join(os.path.dirname(__file__), "icon.png")

    def Run(self):
        """Executed when user clicks the KiPowerSI icon or menu entry in KiCad 9 PCB Editor."""
        board = pcbnew.GetBoard() if KICAD_AVAILABLE else None
        launch_gui(board_obj=board)


def main_cli():
    """Command Line Interface for running KiPowerSI outside KiCad."""
    parser = argparse.ArgumentParser(description="KiPowerSI Pro: KiCad 9 PDN, IR-Drop & Thermal Analyzer CLI")
    parser.add_argument("--board", type=str, help="Path to .kicad_pcb board file", default=None)
    parser.add_argument("--net", type=str, help="Target net name (e.g., +5V, +3V3, GND)", default="+5V")
    parser.add_argument("--voltage", type=float, help="Source operating voltage (V)", default=5.0)
    parser.add_argument("--current", type=float, help="Total drawn load current (A)", default=2.0)
    parser.add_argument("--temp", type=float, help="Ambient temperature (°C)", default=25.0)
    parser.add_argument("--copper-um", type=float, help="Copper thickness in um (35um = 1oz)", default=35.0)
    parser.add_argument("--output-dir", type=str, help="Output directory for reports", default="analysis_reports")
    parser.add_argument("--gui", action="store_true", help="Launch standalone GUI dialog")

    args = parser.parse_args()

    if args.gui:
        launch_gui(board_filepath=args.board)
    else:
        print("================================================================")
        print("KiPowerSI Pro: Intelligent KiCad 9 PDN & Thermal Analyzer Engine")
        print("================================================================")
        print(f"Target Net:            {args.net}")
        print(f"Board File:            {args.board if args.board else 'Synthetic Sample Net'}")
        print(f"Source Voltage:        {args.voltage} V")
        print(f"Total Load Current:    {args.current} A")
        print(f"Ambient Temperature:   {args.temp} °C")
        print("----------------------------------------------------------------")

        solver_res, thermal_res, si_res, drc_res, html_path = run_analysis_pipeline(
            board_filepath=args.board,
            net_name=args.net,
            source_voltage=args.voltage,
            load_current=args.current,
            ambient_temp_c=args.temp,
            copper_thickness_um=args.copper_um,
            output_dir=args.output_dir
        )

        print("\n--- ANALYSIS RESULTS SUMMARY ---")
        print(f"Max DC Voltage Drop:    {solver_res.percentage_voltage_drop:.2f}% ({solver_res.max_voltage_drop:.4f} V drop)")
        print(f"Worst Node ID:          {solver_res.worst_node_id}")
        print(f"Total Loop Resistance:  {solver_res.total_loop_resistance * 1000.0:.2f} mOhm")
        print(f"Max Current Density:    {solver_res.max_current_density:.2f} A/mm^2")
        print(f"Max Temperature Rise:   +{thermal_res.max_temp_rise:.1f} °C (Final: {thermal_res.ambient_temp_c + thermal_res.max_temp_rise:.1f} °C)")
        print(f"Total Power Loss:       {thermal_res.total_power_loss_watts * 1000.0:.2f} mW")
        print(f"Impedance (Z0):         {si_res.char_impedance_z0:.1f} Ohm ({si_res.status})")
        print(f"Propagation Delay:      {si_res.propagation_delay_ps_mm:.2f} ps/mm")
        print(f"Crosstalk Factor (Kc):  {si_res.crosstalk_kc:.3f}")
        print("----------------------------------------------------------------")
        print(f"DRC Status:             {'PASSED [100% Compliant]' if drc_res.passed else 'VIOLATIONS DETECTED'}")
        print(f"Violations Found:       {len(drc_res.violations)} (Errors: {drc_res.error_count}, Warnings: {drc_res.warning_count})")
        for v in drc_res.violations:
            print(f"  - {v}")
        print("----------------------------------------------------------------")
        print(f"Interactive HTML Report: {os.path.abspath(html_path)}")
        print("================================================================\n")


if __name__ == "__main__":
    main_cli()
