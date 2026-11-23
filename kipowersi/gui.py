import sys
import os
import webbrowser
from typing import Optional, Dict, Tuple

# Import solver modules
from .graph_extractor import BoardGraphExtractor, NetGraph
from .ir_drop_solver import IRDropSolver, SolverResult
from .thermal_engine import ThermalEngine, ThermalResult
from .signal_integrity import SignalIntegrityEngine, SIResult
from .drc_rules import PDNDRCRuleChecker, DRCResult
from .report_generator import ReportGenerator

def run_analysis_pipeline(
    board_obj=None,
    board_filepath: Optional[str] = None,
    net_name: str = "+5V",
    source_voltage: float = 5.0,
    load_current: float = 2.0,
    ambient_temp_c: float = 25.0,
    copper_thickness_um: float = 35.0,
    output_dir: str = "."
) -> Tuple[SolverResult, ThermalResult, SIResult, DRCResult, str]:
    """Runs full KiPowerSI analysis workflow and outputs generated HTML report path."""
    extractor = BoardGraphExtractor(copper_thickness_um=copper_thickness_um)

    if board_obj is not None:
        net_graph = extractor.extract_from_pcbnew(board_obj, net_name)
    elif board_filepath and os.path.exists(board_filepath):
        net_graph = extractor.extract_from_file(board_filepath, net_name)
    else:
        # Synthetic fallback test graph
        net_graph = NetGraph(net_name)
        extractor._populate_fallback_synthetic_graph(net_graph)

    # Find source node (VRM) and load nodes
    src_node_id = 0
    load_specs: Dict[int, float] = {}

    for n in net_graph.nodes.values():
        if "vrm" in n.component_ref.lower() or "j1" in n.component_ref.lower() or n.node_id == 0:
            src_node_id = n.node_id
        elif n.node_type == "pad":
            load_specs[n.node_id] = load_current / max(1, len(net_graph.nodes) - 1)

    if not load_specs and len(net_graph.nodes) > 1:
        last_node_id = max(net_graph.nodes.keys())
        load_specs[last_node_id] = load_current

    # Execute Solvers
    ir_solver = IRDropSolver(ambient_temp_c=ambient_temp_c)
    solver_res = ir_solver.solve(net_graph, src_node_id, load_specs, source_voltage)

    thermal_engine = ThermalEngine(ambient_temp_c=ambient_temp_c)
    thermal_res = thermal_engine.calculate(net_graph, solver_res)

    si_engine = SignalIntegrityEngine(copper_thickness_um=copper_thickness_um)
    si_res = si_engine.analyze_net(net_graph)

    drc_checker = PDNDRCRuleChecker()
    drc_res = drc_checker.evaluate(net_graph, solver_res, thermal_res, si_res)

    report_gen = ReportGenerator(output_dir=output_dir)
    html_path = report_gen.generate_all(net_graph, solver_res, thermal_res, si_res, drc_res)

    return solver_res, thermal_res, si_res, drc_res, html_path


class KiPowerSITkDialog:
    """Tkinter Standalone GUI Window Fallback."""

    def __init__(self, board_filepath: Optional[str] = None):
        import tkinter as tk
        from tkinter import ttk, messagebox

        self.tk = tk
        self.ttk = ttk
        self.messagebox = messagebox
        self.board_filepath = board_filepath

        self.root = tk.Tk()
        self.root.title("KiPowerSI Pro - Power & Signal Integrity Analyzer")
        self.root.geometry("520x480")
        self.root.resizable(False, False)

        self._build_ui()

    def _build_ui(self):
        ttk = self.ttk
        tk = self.tk

        frame = ttk.Frame(self.root, padding=20)
        frame.pack(fill="both", expand=True)

        title_lbl = ttk.Label(frame, text="KiPowerSI Pro Analysis Setup", font=("Helvetica", 14, "bold"))
        title_lbl.pack(anchor="w", pady=(0, 15))

        # Net Name Input
        net_lbl = ttk.Label(frame, text="Target Power/Signal Net Name:")
        net_lbl.pack(anchor="w")
        self.net_entry = ttk.Entry(frame)
        self.net_entry.insert(0, "+5V")
        self.net_entry.pack(fill="x", pady=(0, 10))

        # Source Voltage Input
        v_lbl = ttk.Label(frame, text="Source VRM Operating Voltage (Volts):")
        v_lbl.pack(anchor="w")
        self.v_entry = ttk.Entry(frame)
        self.v_entry.insert(0, "5.0")
        self.v_entry.pack(fill="x", pady=(0, 10))

        # Load Current Input
        i_lbl = ttk.Label(frame, text="Total Drawn Load Current (Amperes):")
        i_lbl.pack(anchor="w")
        self.i_entry = ttk.Entry(frame)
        self.i_entry.insert(0, "2.0")
        self.i_entry.pack(fill="x", pady=(0, 10))

        # Ambient Temp Input
        t_lbl = ttk.Label(frame, text="Ambient Operating Temperature (°C):")
        t_lbl.pack(anchor="w")
        self.t_entry = ttk.Entry(frame)
        self.t_entry.insert(0, "25.0")
        self.t_entry.pack(fill="x", pady=(0, 10))

        # Copper Thickness Choice
        cu_lbl = ttk.Label(frame, text="Layer Copper Foil Weight:")
        cu_lbl.pack(anchor="w")
        self.cu_combo = ttk.Combobox(frame, values=["1 oz (35 µm)", "2 oz (70 µm)", "0.5 oz (17.5 µm)"])
        self.cu_combo.current(0)
        self.cu_combo.pack(fill="x", pady=(0, 20))

        # Run Button
        run_btn = ttk.Button(frame, text="Run KiPowerSI Pro Analysis", command=self._on_run)
        run_btn.pack(fill="x", ipady=6)

    def _on_run(self):
        try:
            net_name = self.net_entry.get().strip()
            source_v = float(self.v_entry.get())
            load_i = float(self.i_entry.get())
            amb_t = float(self.t_entry.get())

            cu_str = self.cu_combo.get()
            cu_um = 70.0 if "2 oz" in cu_str else (17.5 if "0.5 oz" in cu_str else 35.0)

            solver_res, thermal_res, si_res, drc_res, html_path = run_analysis_pipeline(
                board_filepath=self.board_filepath,
                net_name=net_name,
                source_voltage=source_v,
                load_current=load_i,
                ambient_temp_c=amb_t,
                copper_thickness_um=cu_um,
                output_dir="analysis_reports"
            )

            webbrowser.open(os.path.abspath(html_path))
            self.messagebox.showinfo(
                "Analysis Complete",
                f"KiPowerSI Pro Analysis Complete!\n\n"
                f"Max IR-Drop: {solver_res.percentage_voltage_drop:.2f}%\n"
                f"Max Temp Rise: +{thermal_res.max_temp_rise:.1f} °C\n"
                f"DRC Status: {'PASSED' if drc_res.passed else 'VIOLATIONS DETECTED'}\n\n"
                f"Report opened in browser:\n{html_path}"
            )
        except Exception as e:
            self.messagebox.showerror("Execution Error", str(e))

    def show(self):
        self.root.mainloop()


def launch_gui(board_obj=None, board_filepath: Optional[str] = None):
    """Launches wxPython dialog inside KiCad, or Tkinter dialog standalone."""
    try:
        import wx  # type: ignore
        # wxPython KiCad 9 Native Modal Dialog
        class KiPowerSIWxDialog(wx.Dialog):
            def __init__(self, parent):
                super().__init__(parent, title="KiPowerSI Pro - KiCad 9 PDN & Thermal Analyzer", size=(480, 420))
                self.InitUI()

            def InitUI(self):
                pnl = wx.Panel(self)
                vbox = wx.BoxSizer(wx.VERTICAL)

                vbox.Add(wx.StaticText(pnl, label="KiPowerSI Pro KiCad 9 Analyzer"), 0, wx.ALL, 10)

                # Net Name
                vbox.Add(wx.StaticText(pnl, label="Target Power Net Name:"), 0, wx.LEFT, 10)
                self.net_ctrl = wx.TextCtrl(pnl, value="+5V")
                vbox.Add(self.net_ctrl, 0, wx.EXPAND | wx.ALL, 10)

                # Source Voltage
                vbox.Add(wx.StaticText(pnl, label="Source VRM Voltage (V):"), 0, wx.LEFT, 10)
                self.v_ctrl = wx.TextCtrl(pnl, value="5.0")
                vbox.Add(self.v_ctrl, 0, wx.EXPAND | wx.ALL, 10)

                # Load Current
                vbox.Add(wx.StaticText(pnl, label="Total Load Current (A):"), 0, wx.LEFT, 10)
                self.i_ctrl = wx.TextCtrl(pnl, value="2.0")
                vbox.Add(self.i_ctrl, 0, wx.EXPAND | wx.ALL, 10)

                btn_run = wx.Button(pnl, label="Run Analysis")
                btn_run.Bind(wx.EVT_BUTTON, self.OnRun)
                vbox.Add(btn_run, 0, wx.ALIGN_CENTER | wx.ALL, 15)

                pnl.SetSizer(vbox)

            def OnRun(self, event):
                net_name = self.net_ctrl.GetValue()
                source_v = float(self.v_ctrl.GetValue())
                load_i = float(self.i_ctrl.GetValue())

                solver_res, thermal_res, si_res, drc_res, html_path = run_analysis_pipeline(
                    board_obj=board_obj,
                    board_filepath=board_filepath,
                    net_name=net_name,
                    source_voltage=source_v,
                    load_current=load_i,
                    output_dir="analysis_reports"
                )

                webbrowser.open(os.path.abspath(html_path))
                wx.MessageBox(
                    f"Analysis Complete!\nMax IR-Drop: {solver_res.percentage_voltage_drop:.2f}%\n"
                    f"Max Temp Rise: +{thermal_res.max_temp_rise:.1f} °C\n"
                    f"Report saved to:\n{html_path}",
                    "KiPowerSI Pro",
                    wx.OK | wx.ICON_INFORMATION
                )
                self.Close()

        app = wx.App(False) if not wx.GetApp() else None
        dlg = KiPowerSIWxDialog(None)
        dlg.ShowModal()
        dlg.Destroy()

    except Exception:
        # Fallback to Tkinter standalone dialog
        dlg = KiPowerSITkDialog(board_filepath=board_filepath)
        dlg.show()
