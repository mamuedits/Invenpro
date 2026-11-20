"""
fix_section_57.py
Replaces control characters in report_content.py with clean text formulas.
"""
import re

with open('report_content.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace control characters \x0c, \x08, etc.
cleaned_text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)

with open('report_content.py', 'w', encoding='utf-8') as f:
    f.write(cleaned_text)

print("Sanitized report_content.py of control characters.")
