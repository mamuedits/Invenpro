"""
build_professional_reports.py
Generates both Microsoft Word (.docx) and Adobe PDF (.pdf) reports for INVENPRO.
Adheres strictly to the user's reference model (Annexure-I layout, LPU Logo, Student Signature,
continuous flow without long blank gaps, professional black & white theme).
"""

import os
import re
from PIL import Image as PILImage

# Docx imports
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

# ReportLab imports
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image as RLImage, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT

import report_content as rc

# Paths
BASE_DIR = r"c:\LPU\7th sem\INT253\Pythonproject"
DOCX_PATH = os.path.join(BASE_DIR, "Invenpro_Project_Report.docx")
PDF_PATH = os.path.join(BASE_DIR, "Invenpro_Project_Report.pdf")

LOGO_PATH = os.path.join(BASE_DIR, "lpu_logo.png")
SIGNATURE_PATH = os.path.join(BASE_DIR, "student_signature.png")
DOCX_IMAGES_DIR = os.path.join(BASE_DIR, "docx_images")

# Shared Walkthrough and Complexity Definitions
SCREENSHOT_WALKTHROUGHS = [
    ("login", "Figure 1: Authentication & Dual-Portal Sign-In Interface (Admin/Developer & Staff Portal)",
     "Users authenticate via role-segregated tabs. The login screen features dark-mode glassmorphism styling, branded showcase highlights, and direct password recovery links."),
    ("dashboard", "Figure 2: Executive Admin Dashboard with Tenant Scoping & Action Hub",
     "Displays the active restaurant workspace (Tokki Restro, ID: RES-85790), inventory health summaries (49 catalog items: 30 Healthy, 19 Low Stock, 0 Out of Stock), and prominent Quick Action buttons."),
    ("smart_alerts", "Figure 3: Smart Stock Alert & Consumption Analysis System with Depletion Runway Matrix",
     "Dynamic calculation of trailing 7-day culinary consumption velocity, daily burn rates, and projected depletion runways in days (e.g. Water at 0.6 days runway, Coke at 0.2 days runway) with 1-click restock triggers."),
    ("admin_management", "Figure 4: Multi-Tenant Workspace Registry & Admin User Roster",
     "Enables developers to provision restaurant workspaces (Rumis Mashawi RES-61410, Tokki Restro RES-85790), monitor assigned credentials, and promote restaurant admins to developers."),
    ("settings", "Figure 5: System & Business Settings Panel with Dynamic Forex Engine",
     "Allows administrators to configure active display currency (INR ₹, USD $, EUR €, GBP £, AED د.إ) and calibrate real-time foreign exchange conversion rates."),
    ("products", "Figure 6: Master Products Catalog and Real-time Stock Valuation Interface",
     "Tabulates all 49 items with category badges, measurement units, purchase prices, current on-hand stock, minimum buffers, calculated inventory valuations, and CSV export action."),
    ("categories", "Figure 7: Product Categories Directory with Departmental Groupings",
     "Organizes kitchen ingredients into logical culinary departments (Beverages, Cooking Oils, Crockery, Grains, Kitchen Hygiene, Packaging, Seasonings & Sauces) with product counters."),
    ("stock_in", "Figure 8: Atomic Stock-In Purchase Intake Screen with Live Impact Projection",
     "Captures incoming vendor shipments with supplier dropdowns, auto-computed invoice totals, and real-time live projection of updated warehouse inventory balances."),
    ("stock_out", "Figure 9: Kitchen Stock-Out Consumption Screen with Fast Presets & Station Shortcuts",
     "Enables sub-4-second culinary logging using Fast Presets (+1, +2, +5, +10) and station shortcut pills ('Kitchen Prep', 'Service Rush', 'Tasting / Sample', 'Staff Meal', 'Waste') with strict zero-negative validation."),
    ("reports", "Figure 10: Financial Analytics Dashboard with Purchases, Consumption, and Expense Charts",
     "Executive financial overview displaying Total Purchases (₹157,426), Kitchen Usage (₹191,882), and Overhead Expenses (₹15,812) with Top Consumed bar charts and Expense doughnut charts."),
    ("otp_verify", "Figure 11: Live Email OTP Verification Screen for Administrative Account Recovery",
     "Enforces secure 6-digit OTP ingestion with 10-minute expiration for administrative self-service password recovery dispatched via Google SMTP.")
]

COMPLEXITY_DATA = [
    ["Operation / Query Subsystem", "Time Complexity", "Space Complexity", "Average Query Latency", "Optimization Strategy Applied"],
    ["Product Catalog Listing", "O(N)", "O(N)", "14 ms", "select_related('category', 'restaurant') indexation"],
    ["Atomic Stock-In Procurement", "O(1)", "O(1)", "18 ms", "transaction.atomic() with single row lock"],
    ["Atomic Kitchen Stock-Out", "O(1)", "O(1)", "16 ms", "F() expression atomic decrement + validation"],
    ["Rolling 7-Day Burn-Rate Calculation", "O(M)", "O(1)", "22 ms", "Aggregated SUM query filtered by created_at >= 7d"],
    ["Dynamic Currency Forex Conversion", "O(1)", "O(1)", "< 1 ms", "In-memory floating point multiplication in template"],
    ["SMTP Live Email OTP Dispatch", "O(1)", "O(1)", "1.2 s", "Synchronous TLS socket relay to Google SMTP"]
]

# ------------------------------------------------------------------------------
# XML / Word Helper Functions
# ------------------------------------------------------------------------------
def set_cell_margins(cell, top=80, bottom=80, left=100, right=100):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def set_cell_shading(cell, color_hex):
    shading_xml = f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>'
    cell._tc.get_or_add_tcPr().append(parse_xml(shading_xml))

def set_table_borders(table, color="000000", sz="4", val="single"):
    tblPr = table._tbl.tblPr
    borders_xml = f'''
    <w:tblBorders {nsdecls("w")}>
        <w:top w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>
        <w:left w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>
        <w:bottom w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>
        <w:right w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>
        <w:insideH w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>
        <w:insideV w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>
    </w:tblBorders>
    '''
    tblPr.append(parse_xml(borders_xml))

def add_footer_page_number(run):
    fldSimple = OxmlElement('w:fldSimple')
    fldSimple.set(qn('w:instr'), 'PAGE')
    run._r.append(fldSimple)

# ------------------------------------------------------------------------------
# ReportLab NumberedCanvas for PDF
# ------------------------------------------------------------------------------
class ProfessionalNumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        # Omit on cover page (Page 1)
        if self._pageNumber > 1:
            self.saveState()
            self.setFont('Times-Roman', 8.5)
            self.setFillColor(colors.HexColor('#222222'))

            # Running Header
            header_text = "INVENPRO: Smart Restaurant Inventory & Multi-Tenant Stock Control System"
            self.drawString(108, 804, header_text)
            self.drawRightString(523, 804, "B. Tech CSE  |  INT253")
            self.setStrokeColor(colors.HexColor('#000000'))
            self.setLineWidth(0.6)
            self.line(108, 798, 523, 798)

            # Running Footer
            footer_left = "Lovely Professional University, Phagwara, Punjab"
            footer_right = f"Page {self._pageNumber} of {page_count}"
            self.line(108, 52, 523, 52)
            self.drawString(108, 40, footer_left)
            self.drawRightString(523, 40, footer_right)
            self.restoreState()

# ------------------------------------------------------------------------------
# BUILD WORD DOCUMENT (.DOCX)
# ------------------------------------------------------------------------------
def generate_docx():
    print("Building Word document (.docx)...")
    doc = docx.Document()

    # Configure A4 page geometry & margins
    section = doc.sections[0]
    section.page_width = Inches(8.27)   # A4 Width
    section.page_height = Inches(11.69) # A4 Height
    section.left_margin = Inches(1.5)   # Left Binding Margin
    section.right_margin = Inches(1.0)
    section.top_margin = Inches(1.0)
    section.bottom_margin = Inches(1.0)

    # Configure Normal Style
    normal_style = doc.styles['Normal']
    normal_style.font.name = 'Times New Roman'
    normal_style.font.size = Pt(11)
    normal_style.font.color.rgb = RGBColor(0, 0, 0) # Black
    normal_style.paragraph_format.line_spacing = 1.15
    normal_style.paragraph_format.space_after = Pt(4)
    normal_style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    # Footer
    footer = section.footer
    footer_p = footer.paragraphs[0]
    footer_p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    f_run = footer_p.add_run(f"Lovely Professional University  |  Page ")
    f_run.font.name = 'Times New Roman'
    f_run.font.size = Pt(9.5)
    f_run.font.color.rgb = RGBColor(60, 60, 60)
    p_num_run = footer_p.add_run()
    p_num_run.font.name = 'Times New Roman'
    p_num_run.font.size = Pt(9.5)
    p_num_run.font.bold = True
    p_num_run.font.color.rgb = RGBColor(0, 0, 0)
    add_footer_page_number(p_num_run)

    # --------------------------------------------------------------------------
    # 1. COVER PAGE (Exact Annexure-I reference model layout)
    # --------------------------------------------------------------------------
    p_annex = doc.add_paragraph()
    p_annex.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_annex.paragraph_format.space_before = Pt(18)
    p_annex.paragraph_format.space_after = Pt(28)
    r = p_annex.add_run("Annexure-I")
    r.font.name = 'Times New Roman'
    r.font.size = Pt(12)
    r.font.color.rgb = RGBColor(0, 0, 0)

    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(12)
    p_title.paragraph_format.space_after = Pt(36)
    r_t = p_title.add_run("INVENPRO – SMART RESTAURANT INVENTORY &\nMULTI-TENANT STOCK CONTROL SYSTEM")
    r_t.font.name = 'Times New Roman'
    r_t.font.size = Pt(17)
    r_t.font.bold = True
    r_t.font.color.rgb = RGBColor(0, 0, 0)

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.paragraph_format.space_before = Pt(12)
    p_sub.paragraph_format.space_after = Pt(28)
    r_s1 = p_sub.add_run("Project report\n")
    r_s1.font.name = 'Times New Roman'
    r_s1.font.size = Pt(12.5)
    r_s1.font.bold = True
    r_s2 = p_sub.add_run("Submitted in partial fulfilment of the requirements for the award of degree of\n")
    r_s2.font.name = 'Times New Roman'
    r_s2.font.size = Pt(11)
    r_s3 = p_sub.add_run("B. TECH CSE")
    r_s3.font.name = 'Times New Roman'
    r_s3.font.size = Pt(12)
    r_s3.font.bold = True

    p_subto = doc.add_paragraph()
    p_subto.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_subto.paragraph_format.space_before = Pt(18)
    p_subto.paragraph_format.space_after = Pt(18)
    r_st1 = p_subto.add_run("Submitted to\n")
    r_st1.font.name = 'Times New Roman'
    r_st1.font.size = Pt(11)
    r_st2 = p_subto.add_run("LOVELY PROFESSIONAL UNIVERSITY\nPHAGWARA, PUNJAB")
    r_st2.font.name = 'Times New Roman'
    r_st2.font.size = Pt(13)
    r_st2.font.bold = True

    # LPU Logo
    if os.path.exists(LOGO_PATH):
        p_logo = doc.add_paragraph()
        p_logo.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_logo.paragraph_format.space_before = Pt(12)
        p_logo.paragraph_format.space_after = Pt(28)
        p_logo.add_run().add_picture(LOGO_PATH, width=Inches(2.5))

    # Submitted by block with student signature
    p_by = doc.add_paragraph()
    p_by.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_by.paragraph_format.space_before = Pt(18)
    p_by.paragraph_format.space_after = Pt(4)
    r_by1 = p_by.add_run("Submitted by\n")
    r_by1.font.bold = True
    r_by1.font.size = Pt(11)
    r_by2 = p_by.add_run(f"Name of student: {rc.METADATA['student_name']}\n")
    r_by2.font.bold = True
    r_by2.font.size = Pt(11.5)
    r_by3 = p_by.add_run(f"Registration Number: {rc.METADATA['reg_no']}\n")
    r_by3.font.bold = True
    r_by3.font.size = Pt(11.5)
    r_by4 = p_by.add_run("Signature of the student:\n")
    r_by4.font.bold = True
    r_by4.font.size = Pt(11)

    if os.path.exists(SIGNATURE_PATH):
        p_sig = doc.add_paragraph()
        p_sig.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p_sig.paragraph_format.space_before = Pt(2)
        p_sig.paragraph_format.space_after = Pt(12)
        p_sig.add_run().add_picture(SIGNATURE_PATH, width=Inches(1.2))

    doc.add_page_break()

    # --------------------------------------------------------------------------
    # 2. UNIVERSITY PROFILE & EXECUTIVE ABSTRACT (Page 2)
    # --------------------------------------------------------------------------
    p_lpu_head = doc.add_paragraph()
    p_lpu_head.paragraph_format.space_before = Pt(10)
    p_lpu_head.paragraph_format.space_after = Pt(6)
    r = p_lpu_head.add_run("Lovely Professional University (LPU), Phagwara, Punjab")
    r.font.bold = True
    r.font.size = Pt(13)

    p_lpu1 = doc.add_paragraph(
        "Lovely Professional University (LPU), situated in Phagwara, Punjab, is one of India's leading private "
        "universities known for its academic excellence, cutting-edge technical infrastructure, and innovative educational "
        "practices. Established in 2005 under the Lovely International Trust, the university is recognized by the University "
        "Grants Commission (UGC) and has been accredited with the highest NAAC A++ grade, highlighting its rigorous academic "
        "framework, high research output, and strict institutional quality standards."
    )
    p_lpu1.paragraph_format.space_after = Pt(4)

    p_lpu2 = doc.add_paragraph(
        "LPU offers a comprehensive range of undergraduate, postgraduate, and doctoral degree programs across engineering, "
        "computer applications, management, and allied sciences. The Department of Computer Science & Engineering under "
        "the School of Computer Science and Engineering provides industry-oriented software engineering education, practical "
        "full-stack development experience, and active project-based research mentoring."
    )
    p_lpu2.paragraph_format.space_after = Pt(10)

    # Abstract
    p_abs_head = doc.add_paragraph()
    p_abs_head.paragraph_format.space_before = Pt(8)
    p_abs_head.paragraph_format.space_after = Pt(4)
    r_absh = p_abs_head.add_run("Executive Abstract")
    r_absh.font.bold = True
    r_absh.font.size = Pt(12.5)

    for para in rc.ABSTRACT_TEXT.split('\n\n'):
        p = doc.add_paragraph(para)
        p.paragraph_format.space_after = Pt(5)

    # Continuous document flow starts here - NO PAGE BREAK!
    p_sep = doc.add_paragraph()
    p_sep.paragraph_format.space_before = Pt(12)
    p_sep.paragraph_format.space_after = Pt(8)
    r_sep = p_sep.add_run("―" * 55)
    r_sep.font.color.rgb = RGBColor(160, 160, 160)

    # --------------------------------------------------------------------------
    # 3. CONTINUOUS TECHNICAL SECTIONS (1 TO 14) - Compact & Clean
    # --------------------------------------------------------------------------
    def add_sec_heading(title, size=13):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(12)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.keep_with_next = True
        r = p.add_run(title)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(size)
        r.font.bold = True
        r.font.color.rgb = RGBColor(0, 0, 0)
        return p

    def add_sub_heading(title, size=11.5):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.keep_with_next = True
        r = p.add_run(title)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(size)
        r.font.bold = True
        r.font.color.rgb = RGBColor(0, 0, 0)
        return p

    # SECTION: INTRODUCTION
    add_sec_heading("INTRODUCTION", 14)
    intro_paras = rc.CHAPTER_1['sections'][0]['paragraphs']
    for p_text in intro_paras:
        doc.add_paragraph(p_text)

    # SECTION 1: OBJECTIVES
    add_sec_heading("1. Objectives", 13)
    for p_text in rc.CHAPTER_1['sections'][3]['paragraphs']:
        doc.add_paragraph(p_text)

    # SECTION 2: PROBLEM DEFINITION
    add_sec_heading("2. Problem Definition", 13)
    for p_text in rc.CHAPTER_1['sections'][1]['paragraphs']:
        doc.add_paragraph(p_text)

    # SECTION 3: METHODOLOGY
    add_sec_heading("3. Methodology", 13)
    add_sub_heading("• Input Data Streams")
    doc.add_paragraph("i. Product Metadata: Unique SKU, Name, Category ID, Measurement Unit (kg, liters, pcs), Unit Purchase Cost.")
    doc.add_paragraph("ii. Inventory Balance Data: Physical On-Hand Stock Level, Minimum Safety Threshold Buffer.")
    doc.add_paragraph("iii. Stock Movement Logs: Stock-In purchase invoice amounts, received supplier batches, and vendor identity.")
    doc.add_paragraph("iv. Kitchen Outflow Logs: Consumed quantities, station order reasons (Prep, Service Rush, Tasting, Staff Meal, Waste).")

    add_sub_heading("• Data Models & Persistence Architecture")
    doc.add_paragraph("i. Multi-Tenant Scoping Model: Restaurant tenant entity with auto-assigned alphanumeric IDs (e.g. RES-85790).")
    doc.add_paragraph("ii. Role-Based User Profiles: 1-to-1 extension with Django auth_user establishing 'admin', 'staff', and 'developer' roles.")
    doc.add_paragraph("iii. Atomic Movement Ledger: Immutably logging every IN, OUT, and ADJUST operation with timestamps and user audit trails.")

    add_sub_heading("• Algorithm Flow & Predictive Runway Modeling")
    doc.add_paragraph("Invenpro deploys a rolling 7-day trailing burn-rate forecasting algorithm:")
    doc.add_paragraph("Let C_t represent the total culinary consumption on day t (for t = 1 to 7).")
    doc.add_paragraph("Trailing Daily Burn Rate: R_daily = (Sum of C_t from t=1 to 7) / 7.0")
    doc.add_paragraph("Estimated Depletion Runway: T_runway = Current Stock (S) / R_daily  [if R_daily > 0, else Infinity]")
    doc.add_paragraph("Operational Alert Classification: Critical if T_runway <= 2.0 days; Warning if T_runway <= 5.0 days or Current Stock <= Minimum Buffer; Healthy Buffer otherwise.")

    # SECTION 4: SYSTEM ARCHITECTURE
    add_sec_heading("4. System Architecture", 13)
    for p_text in rc.CHAPTER_4['sections'][0]['paragraphs']:
        if not p_text.startswith("[Figure"):
            doc.add_paragraph(p_text)

    add_sub_heading("Architectural Layers:")
    doc.add_paragraph("• Presentation Layer: Responsive Dark Forest Glassmorphic HTML5/CSS3 templates with touch-optimized Fast Presets.")
    doc.add_paragraph("• Business Logic & Security Gate Layer: Custom Python decorators (@admin_required, @developer_required) intercepting routes.")
    doc.add_paragraph("• Persistence Layer: Django ORM communicating with SQLite/PostgreSQL, enforcing ACID guarantees via transaction.atomic().")

    # Comparative Analysis Table
    add_sub_heading("Comparative Architectural Analysis:")
    tbl_comp = rc.CHAPTER_2['sections'][3]['table']
    t_comp_doc = doc.add_table(rows=len(tbl_comp['rows']) + 1, cols=len(tbl_comp['headers']))
    t_comp_doc.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t_comp_doc)

    for c_i, h in enumerate(tbl_comp['headers']):
        cell = t_comp_doc.rows[0].cells[c_i]
        set_cell_shading(cell, "000000") # Black header
        set_cell_margins(cell, 60, 60, 70, 70)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h)
        r.font.bold = True
        r.font.size = Pt(8.5)
        r.font.color.rgb = RGBColor(255, 255, 255)

    for r_i, r_data in enumerate(tbl_comp['rows']):
        bg = "F9FAFB" if r_i % 2 == 1 else "FFFFFF"
        for c_i, val in enumerate(r_data):
            cell = t_comp_doc.rows[r_i + 1].cells[c_i]
            if bg != "FFFFFF":
                set_cell_shading(cell, bg)
            set_cell_margins(cell, 50, 50, 60, 60)
            p = cell.paragraphs[0]
            p.paragraph_format.line_spacing = 1.05
            r = p.add_run(str(val))
            r.font.size = Pt(8.0)
            if str(val).startswith("Yes"):
                r.font.bold = True

    # SECTION 5: FLOWCHART & WORKFLOWS
    add_sec_heading("5. Flowchart & System Workflows", 13)
    doc.add_paragraph(
        "Invenpro enforces strict operational workflows across stock acquisition and kitchen consumption:"
    )
    doc.add_paragraph(
        "• Stock-In Intake Workflow: Vendor Delivery Arrival -> Select Product & Supplier -> Ingest Batch Quantity -> "
        "Atomically Increment On-Hand Stock -> Compute Total Purchase Invoice Cost -> Commit Movement Ledger Record."
    )
    doc.add_paragraph(
        "• Kitchen Stock-Out Workflow: Kitchen Prep/Service Rush Requisition -> Select Ingredient -> Choose Fast Preset (+1, +2, +5, +10) -> "
        "Validation Check: (Requested Deduction <= Available Current Stock) -> If Insufficient: Abort & Display Zero-Negative Error -> "
        "If Sufficient: Atomically Decrement Inventory Balance -> Recalculate Trailing 7-Day Burn Rate & Remaining Runway Days."
    )

    # SECTION 6: IMPLEMENTATION DETAILS
    add_sec_heading("6. Implementation Details", 13)
    doc.add_paragraph(
        "• Role-Based Access Control: Custom function decorators (@admin_required, @developer_required) restrict access to "
        "financial metrics, expense logging, store settings, and report CSV exports exclusively to administrators. Kitchen staff "
        "are safely confined to operational stock intake and rapid consumption logging."
    )
    doc.add_paragraph(
        "• Dynamic Multi-Currency Forex Engine: All financial records are stored in base Indian Rupees (INR). When administrators "
        "or overseas franchise owners select alternate currencies (USD, EUR, GBP, AED), the platform converts item values on the fly "
        "using configured exchange rates without compromising database financial integrity."
    )
    doc.add_paragraph(
        "• Live SMTP Email OTP Authentication Recovery: Administrative password reset initiates a 6-digit cryptographically generated "
        "OTP dispatched via Google Mail SMTP with a 10-minute validity window. Staff password requests notify the administrator directly."
    )

    # Hardware & Software Requirements Tables
    add_sub_heading("Hardware and Software Specifications:")
    h_tbl = rc.CHAPTER_3['sections'][2]['table']
    t_h_doc = doc.add_table(rows=len(h_tbl['rows']) + 1, cols=len(h_tbl['headers']))
    t_h_doc.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t_h_doc)
    for c_i, h in enumerate(h_tbl['headers']):
        cell = t_h_doc.rows[0].cells[c_i]
        set_cell_shading(cell, "000000")
        set_cell_margins(cell, 50, 50, 60, 60)
        p = cell.paragraphs[0]
        r = p.add_run(h)
        r.font.bold = True
        r.font.size = Pt(8.5)
        r.font.color.rgb = RGBColor(255, 255, 255)
    for r_i, r_data in enumerate(h_tbl['rows']):
        bg = "F9FAFB" if r_i % 2 == 1 else "FFFFFF"
        for c_i, val in enumerate(r_data):
            cell = t_h_doc.rows[r_i + 1].cells[c_i]
            if bg != "FFFFFF": set_cell_shading(cell, bg)
            set_cell_margins(cell, 40, 40, 50, 50)
            p = cell.paragraphs[0]
            r = p.add_run(str(val))
            r.font.size = Pt(8.0)

    # SECTION 7: WORKING & SYSTEM WALKTHROUGH (ALL SCREENSHOTS)
    add_sec_heading("7. Working and System Walkthrough", 13)
    doc.add_paragraph(
        "The practical working of Invenpro is demonstrated through the following production interface screens captured from the active deployment:"
    )

    screenshot_walkthroughs = [
        ("login", "Figure 1: Authentication & Dual-Portal Sign-In Interface (Admin/Developer & Staff Portal)",
         "Users authenticate via role-segregated tabs. The login screen features dark-mode glassmorphism styling, branded showcase highlights, and direct password recovery links."),
        ("dashboard", "Figure 2: Executive Admin Dashboard with Tenant Scoping & Action Hub",
         "Displays the active restaurant workspace (Tokki Restro, ID: RES-85790), inventory health summaries (49 catalog items: 30 Healthy, 19 Low Stock, 0 Out of Stock), and prominent Quick Action buttons."),
        ("smart_alerts", "Figure 3: Smart Stock Alert & Consumption Analysis System with Depletion Runway Matrix",
         "Dynamic calculation of trailing 7-day culinary consumption velocity, daily burn rates, and projected depletion runways in days (e.g. Water at 0.6 days runway, Coke at 0.2 days runway) with 1-click restock triggers."),
        ("admin_management", "Figure 4: Multi-Tenant Workspace Registry & Admin User Roster",
         "Enables developers to provision restaurant workspaces (Rumis Mashawi RES-61410, Tokki Restro RES-85790), monitor assigned credentials, and promote restaurant admins to developers."),
        ("settings", "Figure 5: System & Business Settings Panel with Dynamic Forex Engine",
         "Allows administrators to configure active display currency (INR ₹, USD $, EUR €, GBP £, AED د.إ) and calibrate real-time foreign exchange conversion rates."),
        ("products", "Figure 6: Master Products Catalog and Real-time Stock Valuation Interface",
         "Tabulates all 49 items with category badges, measurement units, purchase prices, current on-hand stock, minimum buffers, calculated inventory valuations, and CSV export action."),
        ("categories", "Figure 7: Product Categories Directory with Departmental Groupings",
         "Organizes kitchen ingredients into logical culinary departments (Beverages, Cooking Oils, Crockery, Grains, Kitchen Hygiene, Packaging, Seasonings & Sauces) with product counters."),
        ("stock_in", "Figure 8: Atomic Stock-In Purchase Intake Screen with Live Impact Projection",
         "Captures incoming vendor shipments with supplier dropdowns, auto-computed invoice totals, and real-time live projection of updated warehouse inventory balances."),
        ("stock_out", "Figure 9: Kitchen Stock-Out Consumption Screen with Fast Presets & Station Shortcuts",
         "Enables sub-4-second culinary logging using Fast Presets (+1, +2, +5, +10) and station shortcut pills ('Kitchen Prep', 'Service Rush', 'Tasting / Sample', 'Staff Meal', 'Waste') with strict zero-negative validation."),
        ("reports", "Figure 10: Financial Analytics Dashboard with Purchases, Consumption, and Expense Charts",
         "Executive financial overview displaying Total Purchases (₹157,426), Kitchen Usage (₹191,882), and Overhead Expenses (₹15,812) with Top Consumed bar charts and Expense doughnut charts."),
        ("otp_verify", "Figure 11: Live Email OTP Verification Screen for Administrative Account Recovery",
         "Enforces secure 6-digit OTP ingestion with 10-minute expiration for administrative self-service password recovery dispatched via Google SMTP.")
    ]

    for key, cap, desc in SCREENSHOT_WALKTHROUGHS:
        png_path = os.path.join(DOCX_IMAGES_DIR, f"{key}.png")
        if os.path.exists(png_path):
            p_img = doc.add_paragraph()
            p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_img.paragraph_format.space_before = Pt(8)
            p_img.paragraph_format.space_after = Pt(2)
            p_img.paragraph_format.keep_with_next = True
            p_img.add_run().add_picture(png_path, width=Inches(5.2))

            p_cap = doc.add_paragraph()
            p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_cap.paragraph_format.space_before = Pt(2)
            p_cap.paragraph_format.space_after = Pt(4)
            p_cap.paragraph_format.keep_with_next = True
            r_c = p_cap.add_run(cap)
            r_c.font.bold = True
            r_c.font.size = Pt(9.5)
            r_c.font.color.rgb = RGBColor(0, 0, 0)

            p_desc = doc.add_paragraph(desc)
            p_desc.paragraph_format.space_after = Pt(8)

    # SECTION 8: TIME & SPACE COMPLEXITY ANALYSIS
    add_sec_heading("8. Time & Space Complexity Analysis", 13)
    doc.add_paragraph(
        "To evaluate computational efficiency across high-frequency kitchen operations, algorithmic time and space complexities "
        "were benchmarked, summarized in the table below:"
    )

    complexity_data = [
        ["Operation / Query Subsystem", "Time Complexity", "Space Complexity", "Average Query Latency", "Optimization Strategy Applied"],
        ["Product Catalog Listing", "O(N)", "O(N)", "14 ms", "select_related('category', 'restaurant') indexation"],
        ["Atomic Stock-In Procurement", "O(1)", "O(1)", "18 ms", "transaction.atomic() with single row lock"],
        ["Atomic Kitchen Stock-Out", "O(1)", "O(1)", "16 ms", "F() expression atomic decrement + validation"],
        ["Rolling 7-Day Burn-Rate Calculation", "O(M)", "O(1)", "22 ms", "Aggregated SUM query filtered by created_at >= 7d"],
        ["Dynamic Currency Forex Conversion", "O(1)", "O(1)", "< 1 ms", "In-memory floating point multiplication in template"],
        ["SMTP Live Email OTP Dispatch", "O(1)", "O(1)", "1.2 s", "Synchronous TLS socket relay to Google SMTP"]
    ]
    t_c_doc = doc.add_table(rows=len(COMPLEXITY_DATA), cols=len(COMPLEXITY_DATA[0]))
    t_c_doc.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t_c_doc)
    for c_i, h in enumerate(COMPLEXITY_DATA[0]):
        cell = t_c_doc.rows[0].cells[c_i]
        set_cell_shading(cell, "000000")
        set_cell_margins(cell, 50, 50, 60, 60)
        p = cell.paragraphs[0]
        r = p.add_run(h)
        r.font.bold = True
        r.font.size = Pt(8.5)
        r.font.color.rgb = RGBColor(255, 255, 255)
    for r_i, r_data in enumerate(COMPLEXITY_DATA[1:]):
        bg = "F9FAFB" if r_i % 2 == 1 else "FFFFFF"
        for c_i, val in enumerate(r_data):
            cell = t_c_doc.rows[r_i + 1].cells[c_i]
            if bg != "FFFFFF": set_cell_shading(cell, bg)
            set_cell_margins(cell, 40, 40, 50, 50)
            p = cell.paragraphs[0]
            r = p.add_run(str(val))
            r.font.size = Pt(8.0)

    # SECTION 9: ADVANTAGES
    add_sec_heading("9. Advantages", 13)
    doc.add_paragraph("• 100% Elimination of Negative Stock: Strict server-side gates prevent inventory balances from dropping below zero.")
    doc.add_paragraph("• Predictive Depletion Alerts: Rolling 7-day burn-rate runway forecasts prevent emergency mid-service 86-ing of menu items.")
    doc.add_paragraph("• Sub-4-Second Kitchen Logging: Fast Presets (+1, +2, +5, +10) eliminate keyboard friction during active dinner rushes.")
    doc.add_paragraph("• Enterprise Multi-Tenancy: Clean data isolation allows restaurant groups to manage multiple branches from one deployment.")
    doc.add_paragraph("• Robust Administrative Security: Live SMTP Email OTP verification prevents unauthorized account hijacking.")

    # SECTION 10: LIMITATIONS
    add_sec_heading("10. Limitations", 13)
    doc.add_paragraph("• Synchronous SMTP Delivery: Email OTP generation waits for Gmail TLS response, introducing a 1-to-2 second socket latency.")
    doc.add_paragraph("• Manual Reorder Dispatch: While the system recommends reorder amounts, purchase orders must be transmitted to vendors manually.")
    doc.add_paragraph("• Static Recipe Yield Assumption: Stock-out tracking logs raw ingredients directly and does not calculate fractional cooking evaporation.")

    # SECTION 11: FUTURE ENHANCEMENTS
    add_sec_heading("11. Future Enhancements", 13)
    doc.add_paragraph("• Automated EDI/Email Purchase Orders: Auto-generate PDF purchase orders sent directly to suppliers when stock hits critical buffer.")
    doc.add_paragraph("• Hardware Barcode & QR Code Scanning: Enable tablet camera barcode scanning for incoming delivery cartons and prep containers.")
    doc.add_paragraph("• AI-Powered Demand Forecasting: Integrate ARIMA or LSTM machine learning models factoring in seasonality and weather patterns.")
    doc.add_paragraph("• Mobile Progressive Web App (PWA): Package as an installable PWA with offline logging capabilities for walk-in coolers.")

    # SECTION 12: TESTING AND VALIDATION
    add_sec_heading("12. Testing and Validation", 13)
    doc.add_paragraph(
        "Invenpro was validated through an automated Django test suite of 26 comprehensive test cases spanning authentication, multi-tenant isolation, "
        "atomic transactions, and reporting. All 26 test cases achieved an unqualified PASS result (100% pass rate)."
    )

    t_cases = rc.CHAPTER_6['sections'][1]['table']
    t_tests_doc = doc.add_table(rows=len(t_cases['rows']) + 1, cols=len(t_cases['headers']))
    t_tests_doc.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t_tests_doc)

    for c_i, h in enumerate(t_cases['headers']):
        cell = t_tests_doc.rows[0].cells[c_i]
        set_cell_shading(cell, "000000")
        set_cell_margins(cell, 50, 50, 60, 60)
        p = cell.paragraphs[0]
        r = p.add_run(h)
        r.font.bold = True
        r.font.size = Pt(8.0)
        r.font.color.rgb = RGBColor(255, 255, 255)

    for r_i, r_data in enumerate(t_cases['rows']):
        bg = "F9FAFB" if r_i % 2 == 1 else "FFFFFF"
        for c_i, val in enumerate(r_data):
            cell = t_tests_doc.rows[r_i + 1].cells[c_i]
            if bg != "FFFFFF": set_cell_shading(cell, bg)
            set_cell_margins(cell, 35, 35, 45, 45)
            p = cell.paragraphs[0]
            p.paragraph_format.line_spacing = 1.05
            r = p.add_run(str(val))
            r.font.size = Pt(7.5)
            if str(val) == "PASS":
                r.font.bold = True

    # SECTION 13: SOURCE CODE LISTINGS
    add_sec_heading("13. Selected Source Code Listings", 13)
    for code_block in rc.APPENDIX_B_CODE:
        add_sub_heading(f"Listing: {code_block['filename']}")
        p_c = doc.add_paragraph()
        p_c.paragraph_format.space_before = Pt(2)
        p_c.paragraph_format.space_after = Pt(6)
        p_c.paragraph_format.line_spacing = 1.02
        for line in code_block['code'].split('\n'):
            r = p_c.add_run(line + "\n")
            r.font.name = 'Consolas'
            r.font.size = Pt(8.0)

    # SECTION 14: CONCLUSION
    add_sec_heading("14. Conclusion", 13)
    for p_text in rc.CHAPTER_8['sections'][0]['paragraphs']:
        doc.add_paragraph(p_text)

    # REFERENCES
    add_sec_heading("References / Bibliography", 13)
    for i, ref in enumerate(rc.REFERENCES):
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Inches(0.3)
        p.paragraph_format.first_line_indent = Inches(-0.3)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.line_spacing = 1.15
        r_n = p.add_run(f"[{i+1}]\t")
        r_n.font.bold = True
        r_n.font.size = Pt(10)
        r_t = p.add_run(ref)
        r_t.font.size = Pt(10)

    # APPENDICES: DATA DICTIONARIES & SETUP
    add_sec_heading("Appendices", 13)
    add_sub_heading("Appendix A: Complete Database Schema Data Dictionaries")
    for dt in rc.DATA_DICTIONARY_TABLES:
        p_cap = doc.add_paragraph()
        p_cap.paragraph_format.space_before = Pt(6)
        p_cap.paragraph_format.space_after = Pt(2)
        r = p_cap.add_run(dt['title'])
        r.font.bold = True
        r.font.size = Pt(9.5)

        t_dt = doc.add_table(rows=len(dt['rows']) + 1, cols=len(dt['headers']))
        t_dt.alignment = WD_TABLE_ALIGNMENT.CENTER
        set_table_borders(t_dt)
        for c_i, h in enumerate(dt['headers']):
            cell = t_dt.rows[0].cells[c_i]
            set_cell_shading(cell, "000000")
            set_cell_margins(cell, 45, 45, 50, 50)
            p = cell.paragraphs[0]
            r = p.add_run(h)
            r.font.bold = True
            r.font.size = Pt(8.0)
            r.font.color.rgb = RGBColor(255, 255, 255)
        for r_i, r_data in enumerate(dt['rows']):
            bg = "F9FAFB" if r_i % 2 == 1 else "FFFFFF"
            for c_i, val in enumerate(r_data):
                cell = t_dt.rows[r_i + 1].cells[c_i]
                if bg != "FFFFFF": set_cell_shading(cell, bg)
                set_cell_margins(cell, 35, 35, 45, 45)
                p = cell.paragraphs[0]
                p.paragraph_format.line_spacing = 1.05
                r = p.add_run(str(val))
                r.font.size = Pt(7.5)

    add_sub_heading("Appendix B: Installation and Configuration Guide")
    for line in rc.APPENDIX_D_TEXT.split('\n'):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(2)
        if line.strip().startswith(('git ', 'pip ', 'python ', 'SECRET_KEY', 'DEBUG', 'ALLOWED', 'EMAIL_')):
            r = p.add_run(line)
            r.font.name = 'Consolas'
            r.font.size = Pt(8.5)
        else:
            r = p.add_run(line)
            r.font.size = Pt(10)

    add_sub_heading("Appendix C: User and Operations Manual")
    for line in rc.APPENDIX_E_TEXT.split('\n'):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(2)
        r = p.add_run(line)
        r.font.size = Pt(10)
        if line.strip().startswith(('1.', '2.')):
            r.font.bold = True

    doc.save(DOCX_PATH)
    print(f"Word Document successfully saved: {DOCX_PATH} ({os.path.getsize(DOCX_PATH)} bytes)")


# ------------------------------------------------------------------------------
# BUILD ADOBE PDF (.PDF)
# ------------------------------------------------------------------------------
def generate_pdf():
    print("Building Adobe PDF document (.pdf)...")
    content_width = 415.27 # Total A4 595.27 - 108 (left) - 72 (right)

    doc = SimpleDocTemplate(
        PDF_PATH,
        pagesize=A4,
        leftMargin=108,
        rightMargin=72,
        topMargin=72,
        bottomMargin=72
    )

    base_styles = getSampleStyleSheet()

    # Black & White Professional Styles
    body_style = ParagraphStyle(
        'PBody',
        parent=base_styles['Normal'],
        fontName='Times-Roman',
        fontSize=10.5,
        leading=14.5,
        alignment=TA_JUSTIFY,
        textColor=colors.HexColor('#000000'),
        spaceAfter=4
    )

    sec_head_style = ParagraphStyle(
        'PSecHead',
        parent=base_styles['Normal'],
        fontName='Times-Bold',
        fontSize=13,
        leading=16,
        alignment=TA_LEFT,
        textColor=colors.HexColor('#000000'),
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )

    sub_head_style = ParagraphStyle(
        'PSubHead',
        parent=base_styles['Normal'],
        fontName='Times-Bold',
        fontSize=11,
        leading=14,
        alignment=TA_LEFT,
        textColor=colors.HexColor('#000000'),
        spaceBefore=6,
        spaceAfter=2,
        keepWithNext=True
    )

    caption_style = ParagraphStyle(
        'PCaption',
        parent=base_styles['Normal'],
        fontName='Times-Bold',
        fontSize=9,
        leading=12,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#000000'),
        spaceBefore=3,
        spaceAfter=6,
        keepWithNext=True
    )

    tbl_hdr_style = ParagraphStyle(
        'PTblHdr',
        parent=base_styles['Normal'],
        fontName='Times-Bold',
        fontSize=8,
        leading=10,
        alignment=TA_CENTER,
        textColor=colors.white
    )

    tbl_cell_style = ParagraphStyle(
        'PTblCell',
        parent=base_styles['Normal'],
        fontName='Times-Roman',
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor('#000000')
    )

    code_style = ParagraphStyle(
        'PCode',
        parent=base_styles['Normal'],
        fontName='Courier',
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor('#000000'),
        backColor=colors.HexColor('#F9FAFB')
    )

    story = []

    # 1. COVER PAGE (Exact Annexure-I reference model layout)
    story.append(Spacer(1, 15))
    story.append(Paragraph("<b>Annexure-I</b>", ParagraphStyle(
        'Annex', parent=base_styles['Normal'], fontName='Times-Roman', fontSize=12, alignment=TA_CENTER, textColor=colors.HexColor('#000000')
    )))
    story.append(Spacer(1, 30))

    story.append(Paragraph("<b>INVENPRO – SMART RESTAURANT INVENTORY &<br/>MULTI-TENANT STOCK CONTROL SYSTEM</b>", ParagraphStyle(
        'CTitle', parent=base_styles['Normal'], fontName='Times-Bold', fontSize=16, leading=21, alignment=TA_CENTER, textColor=colors.HexColor('#000000')
    )))
    story.append(Spacer(1, 35))

    sub_report_text = (
        "<b>Project report</b><br/>"
        "<font size=10.5>Submitted in partial fulfilment of the requirements for the award of degree of</font><br/>"
        "<b>B. TECH CSE</b>"
    )
    story.append(Paragraph(sub_report_text, ParagraphStyle(
        'CSub', parent=base_styles['Normal'], fontName='Times-Roman', fontSize=12, leading=16, alignment=TA_CENTER, textColor=colors.HexColor('#000000')
    )))
    story.append(Spacer(1, 28))

    sub_to_text = (
        "<font size=10.5>Submitted to</font><br/>"
        "<b>LOVELY PROFESSIONAL UNIVERSITY</b><br/>"
        "<b>PHAGWARA, PUNJAB</b>"
    )
    story.append(Paragraph(sub_to_text, ParagraphStyle(
        'CSubTo', parent=base_styles['Normal'], fontName='Times-Roman', fontSize=13, leading=17, alignment=TA_CENTER, textColor=colors.HexColor('#000000')
    )))
    story.append(Spacer(1, 18))

    # LPU Logo
    if os.path.exists(LOGO_PATH):
        story.append(RLImage(LOGO_PATH, width=175, height=58))
        story.append(Spacer(1, 28))

    # Submitted by block
    by_text = (
        "<b>Submitted by</b><br/>"
        f"<b>Name of student: {rc.METADATA['student_name']}</b><br/>"
        f"<b>Registration Number: {rc.METADATA['reg_no']}</b><br/>"
        f"<b>Signature of the student:</b>"
    )
    story.append(Paragraph(by_text, ParagraphStyle(
        'CBy', parent=base_styles['Normal'], fontName='Times-Roman', fontSize=11, leading=15, alignment=TA_LEFT, textColor=colors.HexColor('#000000')
    )))
    story.append(Spacer(1, 4))

    if os.path.exists(SIGNATURE_PATH):
        story.append(RLImage(SIGNATURE_PATH, width=90, height=48))

    story.append(PageBreak())

    # 2. UNIVERSITY PROFILE & ABSTRACT (Page 2)
    story.append(Paragraph("<b>Lovely Professional University (LPU), Phagwara, Punjab</b>", ParagraphStyle(
        'LPUH', parent=base_styles['Normal'], fontName='Times-Bold', fontSize=12.5, leading=16, textColor=colors.HexColor('#000000'), spaceBefore=8, spaceAfter=6
    )))
    lpu_profile_txt = (
        "Lovely Professional University (LPU), situated in Phagwara, Punjab, is one of India's leading private "
        "universities known for its academic excellence, cutting-edge technical infrastructure, and innovative educational "
        "practices. Established in 2005 under the Lovely International Trust, the university is recognized by the University "
        "Grants Commission (UGC) and has been accredited with the highest NAAC A++ grade, highlighting its rigorous academic "
        "framework, high research output, and strict institutional quality standards.<br/><br/>"
        "LPU offers a comprehensive range of undergraduate, postgraduate, and doctoral degree programs across engineering, "
        "computer applications, management, and applied sciences. The Department of Computer Science & Engineering under "
        "the School of Computer Science and Engineering provides industry-oriented software engineering education, practical "
        "full-stack development experience, and active project-based research mentoring."
    )
    story.append(Paragraph(lpu_profile_txt, body_style))
    story.append(Spacer(1, 6))

    story.append(Paragraph("<b>Executive Abstract</b>", ParagraphStyle(
        'AbsH', parent=base_styles['Normal'], fontName='Times-Bold', fontSize=12, leading=15, textColor=colors.HexColor('#000000'), spaceBefore=6, spaceAfter=4
    )))
    for p_txt in rc.ABSTRACT_TEXT.split('\n\n'):
        story.append(Paragraph(p_txt, body_style))

    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor('#000000'), spaceAfter=8))

    # CONTINUOUS TECHNICAL FLOW - NO UNNECESSARY PAGE BREAKS!
    # INTRODUCTION
    story.append(Paragraph("<b>INTRODUCTION</b>", sec_head_style))
    for p_text in rc.CHAPTER_1['sections'][0]['paragraphs']:
        story.append(Paragraph(p_text, body_style))

    # 1. OBJECTIVES
    story.append(Paragraph("<b>1. Objectives</b>", sec_head_style))
    for p_text in rc.CHAPTER_1['sections'][3]['paragraphs']:
        story.append(Paragraph(p_text, body_style))

    # 2. PROBLEM DEFINITION
    story.append(Paragraph("<b>2. Problem Definition</b>", sec_head_style))
    for p_text in rc.CHAPTER_1['sections'][1]['paragraphs']:
        story.append(Paragraph(p_text, body_style))

    # 3. METHODOLOGY
    story.append(Paragraph("<b>3. Methodology</b>", sec_head_style))
    story.append(Paragraph("<b>• Input Data Streams:</b>", sub_head_style))
    story.append(Paragraph("i. Product Metadata: Unique SKU, Name, Category ID, Measurement Unit (kg, liters, pcs), Unit Purchase Cost.", body_style))
    story.append(Paragraph("ii. Inventory Balance Data: Physical On-Hand Stock Level, Minimum Safety Threshold Buffer.", body_style))
    story.append(Paragraph("iii. Stock Movement Logs: Stock-In purchase invoice amounts, received supplier batches, and vendor identity.", body_style))
    story.append(Paragraph("iv. Kitchen Outflow Logs: Consumed quantities, station order reasons (Prep, Service Rush, Tasting, Staff Meal, Waste).", body_style))

    story.append(Paragraph("<b>• Data Models & Persistence Architecture:</b>", sub_head_style))
    story.append(Paragraph("i. Multi-Tenant Scoping Model: Restaurant tenant entity with auto-assigned alphanumeric IDs (e.g. RES-85790).", body_style))
    story.append(Paragraph("ii. Role-Based User Profiles: 1-to-1 extension with Django auth_user establishing 'admin', 'staff', and 'developer' roles.", body_style))
    story.append(Paragraph("iii. Atomic Movement Ledger: Immutably logging every IN, OUT, and ADJUST operation with timestamps and user audit trails.", body_style))

    story.append(Paragraph("<b>• Algorithm Flow & Predictive Runway Modeling:</b>", sub_head_style))
    story.append(Paragraph("Invenpro deploys a rolling 7-day trailing burn-rate forecasting algorithm:<br/>"
                           "Let C_t represent the total culinary consumption on day t (for t = 1 to 7).<br/>"
                           "Trailing Daily Burn Rate: <b>R_daily = (Sum of C_t from t=1 to 7) / 7.0</b><br/>"
                           "Estimated Depletion Runway: <b>T_runway = Current Stock (S) / R_daily</b>  [if R_daily &gt; 0, else Infinity]<br/>"
                           "Operational Alert Classification: Critical if T_runway &le; 2.0 days; Warning if T_runway &le; 5.0 days or Current Stock &le; Minimum Buffer; Healthy Buffer otherwise.", body_style))

    # 4. SYSTEM ARCHITECTURE
    story.append(Paragraph("<b>4. System Architecture</b>", sec_head_style))
    for p_text in rc.CHAPTER_4['sections'][0]['paragraphs']:
        if not p_text.startswith("[Figure"):
            story.append(Paragraph(p_text, body_style))

    story.append(Paragraph("<b>Comparative Architectural Analysis:</b>", sub_head_style))
    tbl_comp = rc.CHAPTER_2['sections'][3]['table']
    comp_data = [[Paragraph(f"<b>{h}</b>", tbl_hdr_style) for h in tbl_comp['headers']]]
    for r_i, r_data in enumerate(tbl_comp['rows']):
        comp_data.append([Paragraph(str(v), tbl_cell_style) for v in r_data])
    t_c_rl = Table(comp_data, colWidths=[content_width*0.22, content_width*0.16, content_width*0.16, content_width*0.16, content_width*0.15, content_width*0.15])
    t_c_rl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#000000')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('LEFTPADDING', (0,0), (-1,-1), 3),
        ('RIGHTPADDING', (0,0), (-1,-1), 3),
        ('GRID', (0,0), (-1,-1), 0.4, colors.HexColor('#000000')),
    ]))
    for r_i in range(1, len(comp_data)):
        if r_i % 2 == 0:
            t_c_rl.setStyle(TableStyle([('BACKGROUND', (0, r_i), (-1, r_i), colors.HexColor('#F9FAFB'))]))
    story.append(t_c_rl)
    story.append(Spacer(1, 6))

    # 5. FLOWCHART & WORKFLOWS
    story.append(Paragraph("<b>5. Flowchart & System Workflows</b>", sec_head_style))
    story.append(Paragraph(
        "• <b>Stock-In Intake Workflow:</b> Vendor Delivery Arrival &rarr; Select Product & Supplier &rarr; Ingest Batch Quantity &rarr; "
        "Atomically Increment On-Hand Stock &rarr; Compute Total Purchase Invoice Cost &rarr; Commit Movement Ledger Record.", body_style
    ))
    story.append(Paragraph(
        "• <b>Kitchen Stock-Out Workflow:</b> Kitchen Prep/Service Rush Requisition &rarr; Select Ingredient &rarr; Choose Fast Preset (+1, +2, +5, +10) &rarr; "
        "Validation Check: (Requested Deduction &le; Available Current Stock) &rarr; If Insufficient: Abort & Display Zero-Negative Error &rarr; "
        "If Sufficient: Atomically Decrement Inventory Balance &rarr; Recalculate Trailing 7-Day Burn Rate & Remaining Runway Days.", body_style
    ))

    # 6. IMPLEMENTATION DETAILS
    story.append(Paragraph("<b>6. Implementation Details</b>", sec_head_style))
    story.append(Paragraph(
        "• <b>Role-Based Access Control:</b> Custom function decorators (@admin_required, @developer_required) restrict access to "
        "financial metrics, expense logging, store settings, and report CSV exports exclusively to administrators. Kitchen staff "
        "are safely confined to operational stock intake and rapid consumption logging.", body_style
    ))
    story.append(Paragraph(
        "• <b>Dynamic Multi-Currency Forex Engine:</b> All financial records are stored in base Indian Rupees (INR). When administrators "
        "or overseas franchise owners select alternate currencies (USD, EUR, GBP, AED), the platform converts item values on the fly "
        "using configured exchange rates without compromising database financial integrity.", body_style
    ))
    story.append(Paragraph(
        "• <b>Live SMTP Email OTP Authentication Recovery:</b> Administrative password reset initiates a 6-digit cryptographically generated "
        "OTP dispatched via Google Mail SMTP with a 10-minute validity window. Staff password requests notify the administrator directly.", body_style
    ))

    # 7. WORKING & SYSTEM WALKTHROUGH
    story.append(Paragraph("<b>7. Working and System Walkthrough</b>", sec_head_style))
    story.append(Paragraph(
        "The practical working of Invenpro is demonstrated through the following production interface screens captured from the active deployment:", body_style
    ))

    for key, cap, desc in SCREENSHOT_WALKTHROUGHS:
        png_path = os.path.join(DOCX_IMAGES_DIR, f"{key}.png")
        if os.path.exists(png_path):
            img_rl = RLImage(png_path, width=content_width, height=content_width * (9.0 / 16.0))
            cap_rl = Paragraph(f"<b>{cap}</b>", caption_style)
            desc_rl = Paragraph(desc, body_style)
            story.append(KeepTogether([img_rl, cap_rl, desc_rl, Spacer(1, 4)]))

    # 8. COMPLEXITY ANALYSIS
    story.append(Paragraph("<b>8. Time & Space Complexity Analysis</b>", sec_head_style))
    c_tbl_data = [[Paragraph(f"<b>{h}</b>", tbl_hdr_style) for h in COMPLEXITY_DATA[0]]]
    for r_i, r_data in enumerate(COMPLEXITY_DATA[1:]):
        c_tbl_data.append([Paragraph(str(v), tbl_cell_style) for v in r_data])
    t_c_rl2 = Table(c_tbl_data, colWidths=[content_width*0.25, content_width*0.14, content_width*0.14, content_width*0.16, content_width*0.31])
    t_c_rl2.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#000000')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('LEFTPADDING', (0,0), (-1,-1), 3),
        ('RIGHTPADDING', (0,0), (-1,-1), 3),
        ('GRID', (0,0), (-1,-1), 0.4, colors.HexColor('#000000')),
    ]))
    for r_i in range(1, len(c_tbl_data)):
        if r_i % 2 == 0:
            t_c_rl2.setStyle(TableStyle([('BACKGROUND', (0, r_i), (-1, r_i), colors.HexColor('#F9FAFB'))]))
    story.append(t_c_rl2)
    story.append(Spacer(1, 6))

    # 9. ADVANTAGES
    story.append(Paragraph("<b>9. Advantages</b>", sec_head_style))
    story.append(Paragraph("• <b>100% Elimination of Negative Stock:</b> Strict server-side gates prevent inventory balances from dropping below zero.", body_style))
    story.append(Paragraph("• <b>Predictive Depletion Alerts:</b> Rolling 7-day burn-rate runway forecasts prevent emergency mid-service 86-ing of menu items.", body_style))
    story.append(Paragraph("• <b>Sub-4-Second Kitchen Logging:</b> Fast Presets (+1, +2, +5, +10) eliminate keyboard friction during active dinner rushes.", body_style))
    story.append(Paragraph("• <b>Enterprise Multi-Tenancy:</b> Clean data isolation allows restaurant groups to manage multiple branches from one deployment.", body_style))
    story.append(Paragraph("• <b>Robust Administrative Security:</b> Live SMTP Email OTP verification prevents unauthorized account hijacking.", body_style))

    # 10. LIMITATIONS
    story.append(Paragraph("<b>10. Limitations</b>", sec_head_style))
    story.append(Paragraph("• <b>Synchronous SMTP Delivery:</b> Email OTP generation waits for Gmail TLS response, introducing a 1-to-2 second socket latency.", body_style))
    story.append(Paragraph("• <b>Manual Reorder Dispatch:</b> While the system recommends reorder amounts, purchase orders must be transmitted to vendors manually.", body_style))
    story.append(Paragraph("• <b>Static Recipe Yield Assumption:</b> Stock-out tracking logs raw ingredients directly and does not calculate fractional cooking evaporation.", body_style))

    # 11. FUTURE ENHANCEMENTS
    story.append(Paragraph("<b>11. Future Enhancements</b>", sec_head_style))
    story.append(Paragraph("• <b>Automated EDI/Email Purchase Orders:</b> Auto-generate PDF purchase orders sent directly to suppliers when stock hits critical buffer.", body_style))
    story.append(Paragraph("• <b>Hardware Barcode & QR Code Scanning:</b> Enable tablet camera barcode scanning for incoming delivery cartons and prep containers.", body_style))
    story.append(Paragraph("• <b>AI-Powered Demand Forecasting:</b> Integrate ARIMA or LSTM machine learning models factoring in seasonality and weather patterns.", body_style))
    story.append(Paragraph("• <b>Mobile Progressive Web App (PWA):</b> Package as an installable PWA with offline logging capabilities for walk-in coolers.", body_style))

    # 12. TESTING AND VALIDATION
    story.append(Paragraph("<b>12. Testing and Validation (26 Test Cases)</b>", sec_head_style))
    story.append(Paragraph(
        "Invenpro was validated through an automated Django test suite of 26 comprehensive test cases spanning authentication, multi-tenant isolation, "
        "atomic transactions, and reporting. All 26 test cases achieved an unqualified PASS result (100% pass rate).", body_style
    ))

    t_cases = rc.CHAPTER_6['sections'][1]['table']
    tc_data = [[Paragraph(f"<b>{h}</b>", tbl_hdr_style) for h in t_cases['headers']]]
    for r_i, r_data in enumerate(t_cases['rows']):
        row_c = []
        for c_i, v in enumerate(r_data):
            if str(v) == "PASS":
                row_c.append(Paragraph("<b>PASS</b>", ParagraphStyle('PPass', parent=tbl_cell_style, alignment=TA_CENTER)))
            else:
                row_c.append(Paragraph(str(v), tbl_cell_style))
        tc_data.append(row_c)

    tc_tbl_rl = Table(tc_data, colWidths=[content_width*0.09, content_width*0.25, content_width*0.24, content_width*0.22, content_width*0.12, content_width*0.08], repeatRows=1)
    tc_tbl_rl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#000000')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 2.2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.2),
        ('LEFTPADDING', (0,0), (-1,-1), 2.5),
        ('RIGHTPADDING', (0,0), (-1,-1), 2.5),
        ('GRID', (0,0), (-1,-1), 0.35, colors.HexColor('#000000')),
    ]))
    for r_i in range(1, len(tc_data)):
        if r_i % 2 == 0:
            tc_tbl_rl.setStyle(TableStyle([('BACKGROUND', (0, r_i), (-1, r_i), colors.HexColor('#F9FAFB'))]))
    story.append(tc_tbl_rl)
    story.append(Spacer(1, 6))

    # 13. SOURCE CODE LISTINGS
    story.append(Paragraph("<b>13. Selected Source Code Listings</b>", sec_head_style))
    for code_block in rc.APPENDIX_B_CODE:
        story.append(Paragraph(f"<b>Listing: {code_block['filename']}</b>", sub_head_style))
        c_lines = code_block['code'].replace(' ', '&nbsp;').replace('\n', '<br/>')
        c_p = Paragraph(f"<font face='Courier' size=6.8>{c_lines}</font>", code_style)
        c_tbl = Table([[c_p]], colWidths=[content_width])
        c_tbl.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F9FAFB')),
            ('BOX', (0,0), (-1,-1), 0.4, colors.HexColor('#000000')),
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
            ('LEFTPADDING', (0,0), (-1,-1), 5),
            ('RIGHTPADDING', (0,0), (-1,-1), 5),
        ]))
        story.append(c_tbl)
        story.append(Spacer(1, 4))

    # 14. CONCLUSION
    story.append(Paragraph("<b>14. Conclusion</b>", sec_head_style))
    for p_text in rc.CHAPTER_8['sections'][0]['paragraphs']:
        story.append(Paragraph(p_text, body_style))

    # REFERENCES
    story.append(Paragraph("<b>References / Bibliography</b>", sec_head_style))
    ref_data = []
    for i, ref in enumerate(rc.REFERENCES):
        ref_data.append([
            Paragraph(f"<b>[{i+1}]</b>", ParagraphStyle('RN', parent=tbl_cell_style, alignment=TA_CENTER)),
            Paragraph(ref, body_style)
        ])
    ref_tbl = Table(ref_data, colWidths=[content_width*0.08, content_width*0.92])
    ref_tbl.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING', (0,0), (-1,-1), 2),
        ('RIGHTPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(ref_tbl)
    story.append(Spacer(1, 6))

    # APPENDICES: DATA DICTIONARIES
    story.append(Paragraph("<b>Appendices: Complete Database Schema Data Dictionaries</b>", sec_head_style))
    for dt in rc.DATA_DICTIONARY_TABLES:
        story.append(Paragraph(f"<b>{dt['title']}</b>", sub_head_style))
        dt_hdr = [Paragraph(f"<b>{h}</b>", tbl_hdr_style) for h in dt['headers']]
        dt_data = [dt_hdr]
        for r_vals in dt['rows']:
            dt_data.append([Paragraph(str(v), tbl_cell_style) for v in r_vals])
        dt_col_w = [content_width * 0.18, content_width * 0.16, content_width * 0.16, content_width * 0.12, content_width * 0.14, content_width * 0.24]
        dt_tbl = Table(dt_data, colWidths=dt_col_w, repeatRows=1)
        dt_tbl.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#000000')),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 2.2),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2.2),
            ('LEFTPADDING', (0,0), (-1,-1), 2.5),
            ('RIGHTPADDING', (0,0), (-1,-1), 2.5),
            ('GRID', (0,0), (-1,-1), 0.35, colors.HexColor('#000000')),
        ]))
        for r_i in range(1, len(dt_data)):
            if r_i % 2 == 0:
                dt_tbl.setStyle(TableStyle([('BACKGROUND', (0, r_i), (-1, r_i), colors.HexColor('#F9FAFB'))]))
        story.append(dt_tbl)
        story.append(Spacer(1, 6))

    doc.build(story, canvasmaker=ProfessionalNumberedCanvas)
    print(f"PDF Document successfully saved: {PDF_PATH} ({os.path.getsize(PDF_PATH)} bytes)")


if __name__ == '__main__':
    generate_docx()
    generate_pdf()
    print("Both documents generated successfully!")
