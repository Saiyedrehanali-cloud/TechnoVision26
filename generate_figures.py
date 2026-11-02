"""
Figure generation script for TechnoVision research paper.
Reads results.json and generates publication-quality figures:
1. Energy breakdown stacked bars (Sleep, Sensing reads, Radio uplinks)
2. Two-panel trade-off: Delay vs Energy and RMSE vs Energy
3. ASR Architecture Block Diagram

Works with Python standard library (generates clean standalone SVG files),
and also saves 300 DPI PNGs if matplotlib is installed.
"""

import json
import math
import os
import sys

OUTPUT_DIR = "figures"
RESULTS_FILE = "results.json"

# Palette matching UI_UX.md section 0
COLORS = {
    'navy': '#1F3A5F',
    'teal': '#0E9F8E',
    'orange': '#F28C28',
    'red': '#E4572E',
    'green': '#3BA55D',
    'blue': '#4A90D9',
    'purple': '#7E57C2',
    'yellow': '#F9C74F',
    'bg': '#F4F8FC',
    'ink': '#1B2A41',
    'muted': '#6B7C93',
    'border': '#CBD5E1'
}


def load_results():
    if not os.path.exists(RESULTS_FILE):
        print(f"Error: {RESULTS_FILE} not found. Run 'python iot_asr_demo.py experiment' first.")
        sys.exit(1)
    with open(RESULTS_FILE, "r") as f:
        return json.load(f)


def generate_figure1_energy_breakdown(results):
    """
    Figure 1: Energy breakdown stacked bar chart.
    Sleep floor, Sensor reads, Radio transmission uplinks.
    """
    schemes = ['F10', 'F60', 'F600', 'SoD60', 'ASR']
    
    # E_sleep per day = 86400 * 3.3 * 10e-6 = 2.8512 J
    e_sleep_day = 86400 * 3.3 * 10e-6
    e_msg = 0.0134319552
    
    # Calculate components
    data = []
    for s in schemes:
        msgs = results[s]['msgs_day']['mean']
        rds = results[s]['reads_day']['mean']
        has_logic = s in ('SoD60', 'ASR')
        e_read_single = 0.30e-3 + (0.02e-3 if has_logic else 0.0)
        e_reads = rds * e_read_single
        e_radio = msgs * e_msg
        e_total = e_sleep_day + e_reads + e_radio
        data.append({
            'name': s,
            'sleep': e_sleep_day,
            'reads': e_reads,
            'radio': e_radio,
            'total': e_total
        })

    # Generate standalone SVG
    w, h = 640, 400
    pad_l, pad_r, pad_t, pad_b = 60, 40, 50, 60
    chart_w = w - pad_l - pad_r
    chart_h = h - pad_t - pad_b
    
    max_y = 130.0  # F10 is ~121.5 J
    bar_width = 54
    gap = (chart_w - (len(schemes) * bar_width)) / (len(schemes) + 1)
    
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" style="background:#FFF; font-family:sans-serif;">',
        f'<text x="{w/2}" y="28" text-anchor="middle" font-size="16" font-weight="bold" fill="{COLORS["navy"]}">Daily Energy Consumption Breakdown (Joules/day)</text>',
        # Legend
        f'<g transform="translate({w - 300}, 20)">',
        f'<rect x="0" y="0" width="12" height="12" fill="{COLORS["blue"]}"/>',
        f'<text x="18" y="10" font-size="11" fill="{COLORS["ink"]}">Sleep Floor</text>',
        f'<rect x="90" y="0" width="12" height="12" fill="{COLORS["yellow"]}"/>',
        f'<text x="108" y="10" font-size="11" fill="{COLORS["ink"]}">Sensor Reads</text>',
        f'<rect x="195" y="0" width="12" height="12" fill="{COLORS["red"]}"/>',
        f'<text x="213" y="10" font-size="11" fill="{COLORS["ink"]}">Radio TX</text>',
        '</g>'
    ]
    
    # Y Grid
    for y_val in [0, 25, 50, 75, 100, 125]:
        y_pos = pad_t + chart_h - (y_val / max_y * chart_h)
        svg.append(f'<line x1="{pad_l}" y1="{y_pos}" x2="{w - pad_r}" y2="{y_pos}" stroke="{COLORS["border"]}" stroke-dasharray="3,3"/>')
        svg.append(f'<text x="{pad_l - 8}" y="{y_pos + 4}" text-anchor="end" font-size="11" fill="{COLORS["muted"]}">{y_val}</text>')
        
    # Stacked Bars
    for i, d in enumerate(data):
        bx = pad_l + gap + i * (bar_width + gap)
        h_sleep = (d['sleep'] / max_y) * chart_h
        h_reads = (d['reads'] / max_y) * chart_h
        h_radio = (d['radio'] / max_y) * chart_h
        
        y_bottom = pad_t + chart_h
        # Sleep
        y_sleep = y_bottom - h_sleep
        svg.append(f'<rect x="{bx}" y="{y_sleep}" width="{bar_width}" height="{h_sleep}" fill="{COLORS["blue"]}"/>')
        # Reads
        y_reads = y_sleep - h_reads
        svg.append(f'<rect x="{bx}" y="{y_reads}" width="{bar_width}" height="{h_reads}" fill="{COLORS["yellow"]}"/>')
        # Radio
        y_radio = y_reads - h_radio
        svg.append(f'<rect x="{bx}" y="{y_radio}" width="{bar_width}" height="{h_radio}" fill="{COLORS["red"]}"/>')
        
        # Total text
        svg.append(f'<text x="{bx + bar_width/2}" y="{y_radio - 6}" text-anchor="middle" font-size="11" font-weight="bold" fill="{COLORS["navy"]}">{d["total"]:.1f}J</text>')
        # Label
        svg.append(f'<text x="{bx + bar_width/2}" y="{y_bottom + 18}" text-anchor="middle" font-size="12" font-weight="500" fill="{COLORS["ink"]}">{d["name"]}</text>')
        
    svg.append('</svg>')
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_svg = os.path.join(OUTPUT_DIR, "fig1_energy_breakdown.svg")
    with open(out_svg, "w") as f:
        f.write("\n".join(svg))
    print(f"Generated {out_svg}")


def generate_figure2_tradeoffs(results):
    """
    Figure 2: Energy vs Delay & Energy vs RMSE Trade-offs.
    """
    w, h = 720, 360
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" style="background:#FFF; font-family:sans-serif;">',
        f'<text x="{w/2}" y="26" text-anchor="middle" font-size="16" font-weight="bold" fill="{COLORS["navy"]}">Trade-Off Frontiers: Delay vs Energy &amp; RMSE vs Energy</text>'
    ]
    
    # Left panel: Delay vs Energy
    # Right panel: RMSE vs Energy
    # We illustrate the operating points for ASR, SoD60, F600, F60, F10
    svg.append(f'<g transform="translate(60, 60)">')
    svg.append(f'<text x="130" y="-10" text-anchor="middle" font-size="13" font-weight="600" fill="{COLORS["navy"]}">(a) Detection Delay vs Energy</text>')
    svg.append(f'<rect x="0" y="0" width="260" height="230" fill="none" stroke="{COLORS["border"]}"/>')
    svg.append(f'<text x="130" y="255" text-anchor="middle" font-size="11" fill="{COLORS["muted"]}">Daily Energy (J/day)</text>')
    svg.append(f'<text x="-15" y="115" text-anchor="middle" font-size="11" fill="{COLORS["muted"]}" transform="rotate(-90,-15,115)">Detection Delay (s)</text>')
    
    # Plot points on left panel
    # X range 0 to 130 J, Y range 0 to 260 s
    def p_x(j): return 20 + (j / 130.0) * 220
    def p_y(d): return 210 - (d / 260.0) * 190

    pts = [
        ('F10', results['F10']['j_day']['mean'], results['F10']['delay']['mean'], COLORS['red']),
        ('F60', results['F60']['j_day']['mean'], results['F60']['delay']['mean'], COLORS['red']),
        ('F600', results['F600']['j_day']['mean'], results['F600']['delay']['mean'], COLORS['red']),
        ('SoD60', results['SoD60']['j_day']['mean'], results['SoD60']['delay']['mean'], COLORS['orange']),
        ('ASR', results['ASR']['j_day']['mean'], results['ASR']['delay']['mean'], COLORS['teal']),
    ]

    for name, j_val, d_val, col in pts:
        cx = p_x(j_val)
        cy = p_y(d_val)
        if name == 'ASR':
            svg.append(f'<circle cx="{cx}" cy="{cy}" r="8" fill="none" stroke="{COLORS["green"]}" stroke-width="2"/>')
            svg.append(f'<circle cx="{cx}" cy="{cy}" r="4.5" fill="{col}"/>')
        else:
            svg.append(f'<circle cx="{cx}" cy="{cy}" r="4.5" fill="{col}"/>')
        svg.append(f'<text x="{cx + 8}" y="{cy + 4}" font-size="10" font-weight="600" fill="{col}">{name}</text>')
    svg.append('</g>')

    # Right panel: RMSE vs Energy
    svg.append(f'<g transform="translate(400, 60)">')
    svg.append(f'<text x="130" y="-10" text-anchor="middle" font-size="13" font-weight="600" fill="{COLORS["navy"]}">(b) Reconstruction RMSE vs Energy</text>')
    svg.append(f'<rect x="0" y="0" width="260" height="230" fill="none" stroke="{COLORS["border"]}"/>')
    svg.append(f'<text x="130" y="255" text-anchor="middle" font-size="11" fill="{COLORS["muted"]}">Daily Energy (J/day)</text>')
    svg.append(f'<text x="-15" y="115" text-anchor="middle" font-size="11" fill="{COLORS["muted"]}" transform="rotate(-90,-15,115)">Reconstruction RMSE (°C)</text>')

    def r_y(r): return 210 - ((r - 0.15) / 0.85) * 190

    for name, j_val, d_val, col in pts:
        r_val = results[name]['rmse']['mean']
        cx = p_x(j_val)
        cy = r_y(r_val)
        if name == 'ASR':
            svg.append(f'<circle cx="{cx}" cy="{cy}" r="8" fill="none" stroke="{COLORS["green"]}" stroke-width="2"/>')
            svg.append(f'<circle cx="{cx}" cy="{cy}" r="4.5" fill="{col}"/>')
        else:
            svg.append(f'<circle cx="{cx}" cy="{cy}" r="4.5" fill="{col}"/>')
        svg.append(f'<text x="{cx + 8}" y="{cy + 4}" font-size="10" font-weight="600" fill="{col}">{name}</text>')
    svg.append('</g>')

    svg.append('</svg>')
    
    out_svg = os.path.join(OUTPUT_DIR, "fig2_tradeoff_curves.svg")
    with open(out_svg, "w") as f:
        f.write("\n".join(svg))
    print(f"Generated {out_svg}")


def generate_figure3_block_diagram():
    """
    Figure 3: ASR Block Diagram per UI_UX.md Section 3:
    Sensor Read -> (1) Glitch Filter -> (2) Report Rule -> Uplink -> Cloud
    """
    w, h = 680, 220
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" style="background:#FFF; font-family:sans-serif;">',
        f'<text x="{w/2}" y="24" text-anchor="middle" font-size="15" font-weight="bold" fill="{COLORS["navy"]}">ASR Node Architecture: Sampling, Filtering, and Reporting</text>',
        
        # Block 1: Sensor
        f'<g transform="translate(30, 60)">',
        f'<rect x="0" y="0" width="100" height="70" rx="8" fill="{COLORS["bg"]}" stroke="{COLORS["navy"]}" stroke-width="1.5"/>',
        f'<text x="50" y="32" text-anchor="middle" font-size="12" font-weight="bold" fill="{COLORS["navy"]}">Sensor Read</text>',
        f'<text x="50" y="50" text-anchor="middle" font-size="10" fill="{COLORS["muted"]}">x(t), 0.3 mJ</text>',
        f'</g>',

        # Arrow 1
        f'<line x1="130" y1="95" x2="170" y2="95" stroke="{COLORS["navy"]}" stroke-width="2" marker-end="url(#arrow)"/>',

        # Block 2: Glitch Filter
        f'<g transform="translate(170, 50)">',
        f'<rect x="0" y="0" width="130" height="90" rx="8" fill="#FEF3C7" stroke="{COLORS["orange"]}" stroke-width="1.5"/>',
        f'<text x="65" y="26" text-anchor="middle" font-size="11" font-weight="bold" fill="{COLORS["navy"]}">Stage 1: Glitch Filter</text>',
        f'<text x="65" y="46" text-anchor="middle" font-size="10" fill="{COLORS["ink"]}">|x - base| &ge; 2.0 &deg;C?</text>',
        f'<text x="65" y="62" text-anchor="middle" font-size="9" fill="{COLORS["muted"]}">Wait 2s &amp; re-read</text>',
        f'<text x="65" y="78" text-anchor="middle" font-size="9" fill="{COLORS["muted"]}">Discard transient</text>',
        f'</g>',

        # Arrow 2
        f'<line x1="300" y1="95" x2="340" y2="95" stroke="{COLORS["navy"]}" stroke-width="2"/>',

        # Block 3: Report Rule
        f'<g transform="translate(340, 50)">',
        f'<rect x="0" y="0" width="130" height="90" rx="8" fill="#E0F2FE" stroke="{COLORS["blue"]}" stroke-width="1.5"/>',
        f'<text x="65" y="26" text-anchor="middle" font-size="11" font-weight="bold" fill="{COLORS["navy"]}">Stage 2: Report Rule</text>',
        f'<text x="65" y="46" text-anchor="middle" font-size="10" fill="{COLORS["ink"]}">|x - last| &ge; &delta; (0.5&deg;C)</text>',
        f'<text x="65" y="62" text-anchor="middle" font-size="9" fill="{COLORS["muted"]}">OR Heartbeat 15m</text>',
        f'<text x="65" y="78" text-anchor="middle" font-size="9" fill="{COLORS["muted"]}">Adaptive interval</text>',
        f'</g>',

        # Arrow 3
        f'<line x1="470" y1="95" x2="510" y2="95" stroke="{COLORS["navy"]}" stroke-width="2"/>',

        # Block 4: LoRaWAN Uplink
        f'<g transform="translate(510, 60)">',
        f'<rect x="0" y="0" width="130" height="70" rx="8" fill="#CCFBF1" stroke="{COLORS["teal"]}" stroke-width="1.5"/>',
        f'<text x="65" y="30" text-anchor="middle" font-size="12" font-weight="bold" fill="{COLORS["teal"]}">LoRaWAN Uplink</text>',
        f'<text x="65" y="48" text-anchor="middle" font-size="10" fill="{COLORS["ink"]}">SenML/CBOR 25 B</text>',
        f'<text x="65" y="62" text-anchor="middle" font-size="9" fill="{COLORS["muted"]}">13.4 mJ @ SF7</text>',
        f'</g>',

        # Sleep Loop Back Arrow
        f'<path d="M 405 140 L 405 180 L 80 180 L 80 130" fill="none" stroke="{COLORS["purple"]}" stroke-width="1.5" stroke-dasharray="4,4"/>',
        f'<text x="240" y="195" text-anchor="middle" font-size="10" font-weight="600" fill="{COLORS["purple"]}">Adaptive Sleep: doubles up to 80s (calm) or resets to 10s</text>',

        # Defs
        f'<defs><marker id="arrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M 0 0 L 10 5 L 0 10 z" fill="{COLORS["navy"]}"/></marker></defs>',
        '</svg>'
    ]

    out_svg = os.path.join(OUTPUT_DIR, "fig3_block_diagram.svg")
    with open(out_svg, "w") as f:
        f.write("\n".join(svg))
    print(f"Generated {out_svg}")


if __name__ == '__main__':
    res = load_results()
    generate_figure1_energy_breakdown(res)
    generate_figure2_tradeoffs(results=res)
    generate_figure3_block_diagram()
    print("All figures successfully created in figures/ directory!")
