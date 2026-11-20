"""
clean_math_strings.py
"""
with open('report_content.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if '$$R_{daily} =' in line:
        new_lines.append('                "R_daily = (Sum of C_t for t = 1 to 7) / 7.0",\n')
    elif '$$T_{runway} =' in line:
        new_lines.append('                "T_runway = Current Stock (S) / R_daily  [if R_daily > 0, else Infinity]",\n')
    elif 'Let $C_t$ represent' in line:
        new_lines.append('                "Let C_t represent the total quantity of a specific ingredient consumed on day t, where t in {1, 2, ..., 7} represents the rolling trailing 7-day observation window. The Trailing Daily Burn Rate (R_daily) is computed as:",\n')
    elif '• Critical / Depleted:' in line:
        new_lines.append('                "• Critical / Depleted: T_runway <= 2.0 days (Urgent emergency replenishment required).",\n')
    elif '• Warning / Low Stock:' in line:
        new_lines.append('                "• Warning / Low Stock: T_runway <= 5.0 days OR Current Stock <= Minimum Alert Buffer.",\n')
    elif '• Healthy Buffer:' in line:
        new_lines.append('                "• Healthy Buffer: T_runway > 5.0 days AND Current Stock > Minimum Alert Buffer.",\n')
    elif '• Division-by-Zero Protection' in line:
        new_lines.append('                "• Division-by-Zero Protection in Predictive Modeling: When an ingredient experiences zero consumption over the trailing 7 days, the denominator in the runway formula (R_daily) evaluates to zero. Invenpro elegantly handles this boundary condition: when R_daily = 0, the runway is designated as infinite, properly classified into the Healthy Buffer tier rather than triggering a computational exception.",\n')
    else:
        new_lines.append(line)

with open('report_content.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("Cleaned math strings successfully.")
