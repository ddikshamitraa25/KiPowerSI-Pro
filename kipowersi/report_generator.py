import os
import csv
from typing import Optional
from .graph_extractor import NetGraph
from .ir_drop_solver import SolverResult
from .thermal_engine import ThermalResult
from .signal_integrity import SIResult
from .drc_rules import DRCResult

class ReportGenerator:
    """Generates self-contained interactive HTML reports, SVG heatmaps, and CSV data exports."""

    def __init__(self, output_dir: str = "."):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_all(self, net_graph: NetGraph, solver_res: SolverResult, thermal_res: ThermalResult, si_res: SIResult, drc_res: DRCResult) -> str:
        """Generates HTML report, SVG heatmap, and CSV export. Returns path to HTML report."""
        svg_filename = f"{net_graph.net_name}_heatmap.svg"
        html_filename = f"{net_graph.net_name}_report.html"
        csv_filename = f"{net_graph.net_name}_summary.csv"

        svg_path = os.path.join(self.output_dir, svg_filename)
        html_path = os.path.join(self.output_dir, html_filename)
        csv_path = os.path.join(self.output_dir, csv_filename)

        # Generate SVG Heatmap
        svg_content = self._render_svg_heatmap(net_graph, solver_res, thermal_res)
        with open(svg_path, "w", encoding="utf-8") as f:
            f.write(svg_content)

        # Generate CSV Exporter
        self._export_csv(csv_path, net_graph, solver_res, thermal_res, si_res)

        # Generate HTML Report
        html_content = self._render_html_report(net_graph, solver_res, thermal_res, si_res, drc_res, svg_content)
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return html_path

    def _render_svg_heatmap(self, net_graph: NetGraph, solver_res: SolverResult, thermal_res: ThermalResult) -> str:
        """Generates scalable vector graphic (SVG) heatmap showing trace layout and temperature/current overlay."""
        if not net_graph.nodes:
            return "<svg width='400' height='200'><text x='20' y='100'>Empty Net Graph</text></svg>"

        xs = [n.x for n in net_graph.nodes.values()]
        ys = [n.y for n in net_graph.nodes.values()]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)

        margin = 15.0
        width_mm = max(100.0, (max_x - min_x) + 2 * margin)
        height_mm = max(80.0, (max_y - min_y) + 2 * margin)

        scale = 6.0  # Pixels per mm
        svg_w = int(width_mm * scale)
        svg_h = int(height_mm * scale)

        def transform(x, y):
            tx = (x - min_x + margin) * scale
            ty = (y - min_y + margin) * scale
            return tx, ty

        lines_svg = []
        # Render edges with color gradient based on current density / temperature
        for edge in net_graph.edges:
            x1, y1 = transform(edge.start_node.x, edge.start_node.y)
            x2, y2 = transform(edge.end_node.x, edge.end_node.y)
            dt = thermal_res.edge_temp_rise.get(edge.edge_id, 0.0)
            status = thermal_res.edge_hotspot_status.get(edge.edge_id, "SAFE")

            if status == "CRITICAL":
                color = "#EF4444"  # Vibrant Red
                stroke_w = max(4, int(edge.width * scale * 1.5))
            elif status == "WARNING":
                color = "#F59E0B"  # Orange/Amber
                stroke_w = max(3, int(edge.width * scale * 1.2))
            else:
                color = "#10B981"  # Emerald Green
                stroke_w = max(2, int(edge.width * scale))

            lines_svg.append(
                f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                f'stroke="{color}" stroke-width="{stroke_w}" stroke-linecap="round">\n'
                f'  <title>Edge {edge.edge_id} ({edge.layer}): w={edge.width}mm, L={edge.length:.1f}mm | +{dt:.1f}°C</title>\n'
                f'</line>'
            )

        # Render Nodes
        nodes_svg = []
        for n in net_graph.nodes.values():
            nx, ny = transform(n.x, n.y)
            v = solver_res.node_voltages.get(n.node_id, 0.0)
            fill_color = "#3B82F6" if n.node_type == "pad" else "#6B7280"
            r = 6 if n.node_type == "pad" else 4
            label = f"{n.component_ref}-{n.pad_name}" if n.pad_name else f"N{n.node_id}"

            nodes_svg.append(
                f'<circle cx="{nx:.1f}" cy="{ny:.1f}" r="{r}" fill="{fill_color}" stroke="#FFFFFF" stroke-width="1.5">\n'
                f'  <title>Node {n.node_id} ({label}): V={v:.3f}V at ({n.x}, {n.y})</title>\n'
                f'</circle>\n'
                f'<text x="{nx+8:.1f}" y="{ny+4:.1f}" fill="#1F2937" font-size="11" font-family="sans-serif">{label} ({v:.2f}V)</text>'
            )

        svg = f"""<svg width="{svg_w}" height="{svg_h}" viewBox="0 0 {svg_w} {svg_h}" xmlns="http://www.w3.org/2000/svg" style="background: #F9FAFB; border-radius: 8px; border: 1px solid #E5E7EB;">
    <!-- Grid Background -->
    <defs>
        <pattern id="grid" width="30" height="30" patternUnits="userSpaceOnUse">
            <path d="M 30 0 L 0 0 0 30" fill="none" stroke="#E5E7EB" stroke-width="0.5"/>
        </pattern>
    </defs>
    <rect width="100%" height="100%" fill="url(#grid)" />
    <g id="edges">
        {''.join(lines_svg)}
    </g>
    <g id="nodes">
        {''.join(nodes_svg)}
    </g>
    <!-- Legend -->
    <g transform="translate(15, {svg_h - 45})">
        <rect width="280" height="35" rx="6" fill="#FFFFFF" opacity="0.9" stroke="#D1D5DB" />
        <circle cx="15" cy="18" r="5" fill="#10B981" />
        <text x="25" y="22" font-size="11" font-family="sans-serif">Safe (&lt;10°C)</text>
        <circle cx="105" cy="18" r="5" fill="#F59E0B" />
        <text x="115" y="22" font-size="11" font-family="sans-serif">Warning (10-30°C)</text>
        <circle cx="205" cy="18" r="5" fill="#EF4444" />
        <text x="215" y="22" font-size="11" font-family="sans-serif">Critical (&gt;30°C)</text>
    </g>
</svg>"""
        return svg

    def _export_csv(self, csv_path: str, net_graph: NetGraph, solver_res: SolverResult, thermal_res: ThermalResult, si_res: SIResult):
        """Exports detailed edge and node metrics to CSV."""
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["KiPowerSI Pro Analysis Summary - Net", net_graph.net_name])
            writer.writerow([])
            writer.writerow(["--- EDGE METRICS ---"])
            writer.writerow(["Edge_ID", "Start_Node", "End_Node", "Layer", "Width_mm", "Length_mm", "Current_A", "Current_Density_A_mm2", "Power_Loss_mW", "Temp_Rise_C", "Status"])
            for e in net_graph.edges:
                i_val = solver_res.edge_currents.get(e.edge_id, 0.0)
                j_val = solver_res.edge_current_densities.get(e.edge_id, 0.0)
                p_mw = solver_res.edge_power_dissipation.get(e.edge_id, 0.0) * 1000.0
                dt = thermal_res.edge_temp_rise.get(e.edge_id, 0.0)
                st = thermal_res.edge_hotspot_status.get(e.edge_id, "SAFE")
                writer.writerow([e.edge_id, e.start_node.node_id, e.end_node.node_id, e.layer, e.width, f"{e.length:.2f}", f"{i_val:.4f}", f"{j_val:.2f}", f"{p_mw:.2f}", f"{dt:.2f}", st])

            writer.writerow([])
            writer.writerow(["--- NODE METRICS ---"])
            writer.writerow(["Node_ID", "Label", "Layer", "X_mm", "Y_mm", "Voltage_V", "IR_Drop_mV"])
            for n in net_graph.nodes.values():
                v = solver_res.node_voltages.get(n.node_id, 0.0)
                drop_mv = (solver_res.source_voltage - v) * 1000.0
                lbl = f"{n.component_ref}-{n.pad_name}" if n.pad_name else f"N{n.node_id}"
                writer.writerow([n.node_id, lbl, n.layer, n.x, n.y, f"{v:.4f}", f"{drop_mv:.2f}"])

    def _render_html_report(self, net_graph: NetGraph, solver_res: SolverResult, thermal_res: ThermalResult, si_res: SIResult, drc_res: DRCResult, svg_heatmap: str) -> str:
        """Renders comprehensive HTML report template."""
        drc_badge = '<span style="background: #10B981; color: white; padding: 4px 12px; border-radius: 9999px; font-weight: bold;">PASSED</span>' if drc_res.passed else '<span style="background: #EF4444; color: white; padding: 4px 12px; border-radius: 9999px; font-weight: bold;">VIOLATIONS DETECTED</span>'

        violations_rows = []
        if drc_res.violations:
            for v in drc_res.violations:
                badge_clr = "#EF4444" if v.severity == "ERROR" else "#F59E0B"
                violations_rows.append(
                    f'<tr>'
                    f'<td><span style="background: {badge_clr}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px;">{v.severity}</span></td>'
                    f'<td><strong>{v.rule_name}</strong></td>'
                    f'<td>{v.message}</td>'
                    f'<td><code>{v.element_id}</code></td>'
                    f'<td><span style="color: #EF4444; font-weight: 600;">{v.value_str}</span></td>'
                    f'<td>{v.threshold_str}</td>'
                    f'</tr>'
                )
        else:
            violations_rows.append('<tr><td colspan="6" style="text-align: center; color: #10B981; font-weight: 600; padding: 16px;">No DRC Violations Found! Net layout complies with all PDN & Thermal rules.</td></tr>')

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KiPowerSI Pro Analysis Report - Net {net_graph.net_name}</title>
    <style>
        :root {{
            --primary: #2563EB;
            --bg: #F8FAFC;
            --card-bg: #FFFFFF;
            --text: #1E293B;
            --border: #E2E8F0;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg);
            color: var(--text);
            margin: 0;
            padding: 24px;
            line-height: 1.5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: var(--card-bg);
            padding: 20px 32px;
            border-radius: 12px;
            border: 1px solid var(--border);
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            margin-bottom: 24px;
        }}
        .header h1 {{
            margin: 0;
            font-size: 24px;
            color: #0F172A;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }}
        .card {{
            background: var(--card-bg);
            padding: 20px;
            border-radius: 10px;
            border: 1px solid var(--border);
            box-shadow: 0 1px 2px rgba(0,0,0,0.04);
        }}
        .card-title {{
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #64748B;
            font-weight: 600;
            margin-bottom: 8px;
        }}
        .card-value {{
            font-size: 28px;
            font-weight: 700;
            color: #0F172A;
        }}
        .section {{
            background: var(--card-bg);
            padding: 24px;
            border-radius: 12px;
            border: 1px solid var(--border);
            margin-bottom: 24px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }}
        .section-title {{
            font-size: 18px;
            font-weight: 700;
            margin-top: 0;
            margin-bottom: 16px;
            color: #0F172A;
            border-bottom: 2px solid #F1F5F9;
            padding-bottom: 8px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }}
        th, td {{
            text-align: left;
            padding: 10px 14px;
            border-bottom: 1px solid var(--border);
        }}
        th {{
            background-color: #F8FAFC;
            font-weight: 600;
            color: #475569;
        }}
        tr:hover {{
            background-color: #F1F5F9;
        }}
        code {{
            background: #F1F5F9;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: monospace;
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <div>
                <h1>KiPowerSI Pro - Power & Signal Integrity Analysis</h1>
                <p style="margin: 4px 0 0 0; color: #64748B; font-size: 14px;">Target Net: <strong>{net_graph.net_name}</strong> | KiCad 9 Action Plugin Engine</p>
            </div>
            <div>
                {drc_badge}
            </div>
        </div>

        <!-- Metric Cards -->
        <div class="grid">
            <div class="card">
                <div class="card-title">Max DC IR-Drop</div>
                <div class="card-value" style="color: {'#EF4444' if solver_res.percentage_voltage_drop > 3.0 else '#10B981'};">
                    {solver_res.percentage_voltage_drop:.2f}%
                </div>
                <small style="color: #64748B;">{solver_res.max_voltage_drop:.3f} V drop across net</small>
            </div>
            <div class="card">
                <div class="card-title">Max Temp Rise (&Delta;T)</div>
                <div class="card-value" style="color: {'#EF4444' if thermal_res.max_temp_rise > 15.0 else '#10B981'};">
                    +{thermal_res.max_temp_rise:.1f} °C
                </div>
                <small style="color: #64748B;">Peak Temp: {thermal_res.ambient_temp_c + thermal_res.max_temp_rise:.1f} °C</small>
            </div>
            <div class="card">
                <div class="card-title">Max Current Density</div>
                <div class="card-value">
                    {solver_res.max_current_density:.1f} <span style="font-size: 16px;">A/mm²</span>
                </div>
                <small style="color: #64748B;">Limit: &lt;30.0 A/mm²</small>
            </div>
            <div class="card">
                <div class="card-title">Characteristic Impedance (Z₀)</div>
                <div class="card-value">
                    {si_res.char_impedance_z0:.1f} <span style="font-size: 16px;">&Omega;</span>
                </div>
                <small style="color: #64748B;">Propagation Delay: {si_res.propagation_delay_ps_mm:.1f} ps/mm</small>
            </div>
        </div>

        <!-- Heatmap Visualization Section -->
        <div class="section">
            <h2 class="section-title">2D Thermal & Current Density Layout Overlay</h2>
            <div style="display: flex; justify-content: center; padding: 12px 0;">
                {svg_heatmap}
            </div>
        </div>

        <!-- DRC Violations Section -->
        <div class="section">
            <h2 class="section-title">Automated Rule Checks & Violations ({len(drc_res.violations)})</h2>
            <table>
                <thead>
                    <tr>
                        <th>Severity</th>
                        <th>Rule Name</th>
                        <th>Description</th>
                        <th>Target Element</th>
                        <th>Measured Value</th>
                        <th>Constraint Limit</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(violations_rows)}
                </tbody>
            </table>
        </div>

        <!-- Signal Integrity Summary -->
        <div class="section">
            <h2 class="section-title">High-Speed Signal Integrity & Transmission Line Parasitics</h2>
            <div class="grid" style="margin-bottom: 0;">
                <div>
                    <p><strong>Total Trace Capacitance (C):</strong> {si_res.total_capacitance_pf:.2f} pF</p>
                    <p><strong>Total Trace Inductance (L):</strong> {si_res.total_inductance_nh:.2f} nH</p>
                </div>
                <div>
                    <p><strong>Reflection Coefficient (&Gamma;):</strong> {si_res.reflection_coefficient_gamma:.3f}</p>
                    <p><strong>Crosstalk Coupling Factor (K_C):</strong> {si_res.crosstalk_kc:.3f}</p>
                </div>
            </div>
        </div>

        <!-- Footer -->
        <div style="text-align: center; color: #94A3B8; font-size: 13px; margin-top: 32px;">
            Generated automatically by <strong>KiPowerSI Pro</strong> | FOSSEE eSim Internship Project | KiCad 9 Plugin
        </div>
    </div>
</body>
</html>"""
        return html
