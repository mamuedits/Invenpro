"""
generate_final_report.py
Generates the complete, exhaustive, professional academic Project Report for INVENPRO
in both Word (.docx) and PDF (.pdf) formats.
Features:
- Full 8 Chapters with all sections (1.1 to 8.3)
- Preliminary Pages (Cover Page, LPU Profile, Abstract, Table of Contents, Lists of Figures/Tables/Abbreviations)
- Annexure-I Cover Page with LPU Logo and Student Signature
- Professional Black theme throughout (pure black headings, black table headers with white text, black rules)
- Continuous flow within chapters without long blank spaces or artificial page breaks
- References (IEEE) and Appendices A through E
"""

import os
import re
from PIL import Image as PILImage

# docx imports
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

# reportlab imports
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

BASE_DIR = r"c:\LPU\7th sem\INT253\Pythonproject"
DOCX_PATH = os.path.join(BASE_DIR, "Invenpro_Project_Report.docx")
PDF_PATH = os.path.join(BASE_DIR, "Invenpro_Project_Report.pdf")

LOGO_PATH = os.path.join(BASE_DIR, "lpu_logo.png")
SIGNATURE_PATH = os.path.join(BASE_DIR, "student_signature.png")
DOCX_IMAGES_DIR = os.path.join(BASE_DIR, "docx_images")

# ------------------------------------------------------------------------------
# Word Formatting Helpers
# ------------------------------------------------------------------------------
def set_cell_margins(cell, top=70, bottom=70, left=90, right=90):
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
        <w:left w:val="none"/>
        <w:bottom w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>
        <w:right w:val="none"/>
        <w:insideH w:val="{val}" w:sz="{sz}" w:space="0" w:color="D1D5DB"/>
        <w:insideV w:val="none"/>
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
# 1. BUILD COMPLETE WORD DOCUMENT (.DOCX)
# ------------------------------------------------------------------------------
TOC_ITEMS = [
("Abstract", "ii"),
("List of Figures", "iv"),
("List of Tables", "v"),
("List of Abbreviations", "vi"),
("Chapter 1: Introduction", "1"),
("    1.1 Background", "1"),
("    1.2 Problem Statement", "2"),
("    1.3 Motivation", "3"),
("    1.4 Objectives of the Project", "4"),
("    1.5 Scope of the Project", "5"),
("    1.6 Proposed Solution", "6"),
("Chapter 2: Literature Review and Existing System Analysis", "7"),
("    2.1 Existing Systems and Industry Practices", "7"),
("    2.2 Related Commercial Systems", "8"),
("    2.3 Limitations of Existing Systems", "9"),
("    2.4 Comparative Analysis", "10"),
("    2.5 Need for the Proposed System", "11"),
("Chapter 3: System Requirements Analysis", "12"),
("    3.1 Functional Requirements", "12"),
("    3.2 Non-Functional Requirements", "14"),
("    3.3 Hardware Requirements", "15"),
("    3.4 Software Requirements", "16"),
("    3.5 Feasibility Study", "17"),
("Chapter 4: System Design", "18"),
("    4.1 System Architecture", "18"),
("    4.2 UML Use Case Diagram", "19"),
("    4.3 UML Activity Diagram", "20"),
("    4.4 UML Class Diagram", "21"),
("    4.5 UML Sequence Diagrams", "22"),
("    4.6 Database Design and Relational Schema", "24"),
("    4.7 Entity-Relationship (ER) Diagram", "25"),
("    4.8 Module Design", "26"),
("    4.9 UI/UX Design System", "27"),
("Chapter 5: Implementation", "28"),
("    5.1 Development Environment", "28"),
("    5.2 Project Structure", "29"),
("    5.3 Technologies Used", "30"),
("    5.4 Module Implementation Walkthrough", "31"),
("    5.5 Authentication & Live Email OTP Stack", "32"),
("    5.6 Database Implementation and Migrations", "33"),
("    5.7 Mathematical Model for Burn-Rate & Runway Forecasting", "34"),
("    5.8 Application Screenshots and Interface Walkthrough", "35"),
("Chapter 6: Testing and Validation", "43"),
("    6.1 Testing Methodology", "43"),
("    6.2 Automated Test Suite Execution Results (26 Test Cases)", "44"),
("    6.3 Security Testing", "47"),
("    6.4 Performance and Usability Testing", "48"),
("Chapter 7: Results and Discussion", "49"),
("    7.1 Project Outcomes", "49"),
("    7.2 Features Successfully Implemented", "50"),
("    7.3 Operational Results and Live Metrics", "51"),
("    7.4 Technical Discussion", "52"),
("Chapter 8: Conclusion and Future Scope", "53"),
("    8.1 Conclusion", "53"),
("    8.2 Limitations of the System", "54"),
("    8.3 Future Scope and Enhancements", "55"),
("References / Bibliography", "56"),
("Appendix A: Application UI Screenshots & Field Reference", "58"),
("Appendix B: Selected Core Source Code Listings", "60"),
("Appendix C: Complete Database Schema & Data Dictionary", "64"),
("Appendix D: Installation and Environment Configuration Guide", "67"),
("Appendix E: User and Operations Manual", "68")
]
def generate_docx():
    print("Generating Complete Word document (.docx)...")
    doc = docx.Document()

    # Geometry
    section = doc.sections[0]
    section.page_width = Inches(8.27)
    section.page_height = Inches(11.69)
    section.left_margin = Inches(1.5) # Binding margin
    section.right_margin = Inches(1.0)
    section.top_margin = Inches(1.0)
    section.bottom_margin = Inches(1.0)

    # Normal Style
    normal = doc.styles['Normal']
    normal.font.name = 'Times New Roman'
    normal.font.size = Pt(11)
    normal.font.color.rgb = RGBColor(0, 0, 0)
    normal.paragraph_format.line_spacing = 1.15
    normal.paragraph_format.space_after = Pt(4)
    normal.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    # Footer
    footer = section.footer
    footer_p = footer.paragraphs[0]
    footer_p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    f_run = footer_p.add_run("Lovely Professional University  |  Page ")
    f_run.font.name = 'Times New Roman'
    f_run.font.size = Pt(9.5)
    f_run.font.color.rgb = RGBColor(80, 80, 80)
    p_num_run = footer_p.add_run()
    p_num_run.font.name = 'Times New Roman'
    p_num_run.font.size = Pt(9.5)
    p_num_run.font.bold = True
    p_num_run.font.color.rgb = RGBColor(0, 0, 0)
    add_footer_page_number(p_num_run)

    # --------------------------------------------------------------------------
    # COVER PAGE (Annexure-I layout from reference model)
    # --------------------------------------------------------------------------
    p_annex = doc.add_paragraph()
    p_annex.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_annex.paragraph_format.space_before = Pt(12)
    p_annex.paragraph_format.space_after = Pt(24)
    r = p_annex.add_run("Annexure-I")
    r.font.name = 'Times New Roman'
    r.font.size = Pt(12)
    r.font.color.rgb = RGBColor(0, 0, 0)

    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(8)
    p_title.paragraph_format.space_after = Pt(30)
    r_t = p_title.add_run("INVENPRO – SMART RESTAURANT INVENTORY &\nMULTI-TENANT STOCK CONTROL SYSTEM")
    r_t.font.name = 'Times New Roman'
    r_t.font.size = Pt(16.5)
    r_t.font.bold = True
    r_t.font.color.rgb = RGBColor(0, 0, 0)

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.paragraph_format.space_before = Pt(8)
    p_sub.paragraph_format.space_after = Pt(24)
    r_s1 = p_sub.add_run("Project report\n")
    r_s1.font.name = 'Times New Roman'
    r_s1.font.size = Pt(12)
    r_s1.font.bold = True
    r_s2 = p_sub.add_run("Submitted in partial fulfilment of the requirements for the award of degree of\n")
    r_s2.font.name = 'Times New Roman'
    r_s2.font.size = Pt(10.5)
    r_s3 = p_sub.add_run("B. TECH CSE")
    r_s3.font.name = 'Times New Roman'
    r_s3.font.size = Pt(12)
    r_s3.font.bold = True

    p_subto = doc.add_paragraph()
    p_subto.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_subto.paragraph_format.space_before = Pt(14)
    p_subto.paragraph_format.space_after = Pt(14)
    r_st1 = p_subto.add_run("Submitted to\n")
    r_st1.font.name = 'Times New Roman'
    r_st1.font.size = Pt(10.5)
    r_st2 = p_subto.add_run("LOVELY PROFESSIONAL UNIVERSITY\nPHAGWARA, PUNJAB")
    r_st2.font.name = 'Times New Roman'
    r_st2.font.size = Pt(12.5)
    r_st2.font.bold = True

    # LPU Logo
    if os.path.exists(LOGO_PATH):
        p_logo = doc.add_paragraph()
        p_logo.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_logo.paragraph_format.space_before = Pt(10)
        p_logo.paragraph_format.space_after = Pt(26)
        p_logo.add_run().add_picture(LOGO_PATH, width=Inches(2.4))

    # Submitted by block
    p_by = doc.add_paragraph()
    p_by.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_by.paragraph_format.space_before = Pt(14)
    p_by.paragraph_format.space_after = Pt(2)
    r_by1 = p_by.add_run("Submitted by\n")
    r_by1.font.bold = True
    r_by1.font.size = Pt(10.5)
    r_by2 = p_by.add_run(f"Name of student: {rc.METADATA['student_name']}\n")
    r_by2.font.bold = True
    r_by2.font.size = Pt(11)
    r_by3 = p_by.add_run(f"Registration Number: {rc.METADATA['reg_no']}\n")
    r_by3.font.bold = True
    r_by3.font.size = Pt(11)
    r_by4 = p_by.add_run("Signature of the student:\n")
    r_by4.font.bold = True
    r_by4.font.size = Pt(10.5)

    if os.path.exists(SIGNATURE_PATH):
        p_sig = doc.add_paragraph()
        p_sig.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p_sig.paragraph_format.space_before = Pt(2)
        p_sig.paragraph_format.space_after = Pt(8)
        p_sig.add_run().add_picture(SIGNATURE_PATH, width=Inches(1.2))

    doc.add_page_break()

    # --------------------------------------------------------------------------
    # UNIVERSITY PROFILE & ABSTRACT (Page 2)
    # --------------------------------------------------------------------------
    p_lpu_head = doc.add_paragraph()
    p_lpu_head.paragraph_format.space_before = Pt(8)
    p_lpu_head.paragraph_format.space_after = Pt(4)
    r = p_lpu_head.add_run("Lovely Professional University (LPU), Phagwara, Punjab")
    r.font.bold = True
    r.font.size = Pt(12.5)

    p_lpu1 = doc.add_paragraph(
        "Lovely Professional University (LPU), situated in Phagwara, Punjab, is one of India's leading private "
        "universities known for its academic excellence, cutting-edge technical infrastructure, and innovative educational "
        "practices. Established in 2005 under the Lovely International Trust, the university is recognized by the University "
        "Grants Commission (UGC) and has been accredited with the prestigious NAAC A++ grade, highlighting its rigorous academic "
        "framework, high research output, and strict institutional quality standards."
    )
    p_lpu1.paragraph_format.space_after = Pt(4)

    p_lpu2 = doc.add_paragraph(
        "LPU offers a comprehensive range of undergraduate, postgraduate, and doctoral degree programs across engineering, "
        "computer applications, management, and allied sciences. The Department of Computer Science & Engineering under "
        "the School of Computer Science and Engineering provides industry-oriented software engineering education, practical "
        "full-stack development experience, and active project-based research mentoring."
    )
    p_lpu2.paragraph_format.space_after = Pt(8)

    # Abstract
    p_abs_head = doc.add_paragraph()
    p_abs_head.paragraph_format.space_before = Pt(6)
    p_abs_head.paragraph_format.space_after = Pt(4)
    r_absh = p_abs_head.add_run("Executive Abstract")
    r_absh.font.bold = True
    r_absh.font.size = Pt(12)

    for para in rc.ABSTRACT_TEXT.split('\n\n'):
        p = doc.add_paragraph(para)
        p.paragraph_format.space_after = Pt(4)

    doc.add_page_break()

    # --------------------------------------------------------------------------
    # TABLE OF CONTENTS
    # --------------------------------------------------------------------------
    p_toc_head = doc.add_paragraph()
    p_toc_head.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_toc_head.paragraph_format.space_before = Pt(8)
    p_toc_head.paragraph_format.space_after = Pt(10)
    r_toch = p_toc_head.add_run("TABLE OF CONTENTS")
    r_toch.font.bold = True
    r_toch.font.size = Pt(14)


    toc_table = doc.add_table(rows=len(TOC_ITEMS), cols=2)
    toc_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    toc_table.autofit = False
    toc_table.columns[0].width = Inches(5.1)
    toc_table.columns[1].width = Inches(0.6)

    for i, (title_str, page_str) in enumerate(TOC_ITEMS):
        row = toc_table.rows[i]
        c0, c1 = row.cells[0], row.cells[1]
        set_cell_margins(c0, top=20, bottom=20, left=40, right=40)
        set_cell_margins(c1, top=20, bottom=20, left=40, right=40)

        p0 = c0.paragraphs[0]
        p0.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p0.paragraph_format.line_spacing = 1.05
        p0.paragraph_format.space_after = Pt(1)
        r0 = p0.add_run(title_str)
        r0.font.name = 'Times New Roman'
        r0.font.size = Pt(10)
        if title_str.startswith("Chapter") or title_str.startswith("References") or title_str.startswith("Appendix") or title_str in ["Abstract", "List of Figures", "List of Tables", "List of Abbreviations"]:
            r0.font.bold = True

        p1 = c1.paragraphs[0]
        p1.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p1.paragraph_format.line_spacing = 1.05
        p1.paragraph_format.space_after = Pt(1)
        r1 = p1.add_run(page_str)
        r1.font.name = 'Times New Roman'
        r1.font.size = Pt(10)
        if r0.font.bold: r1.font.bold = True

    doc.add_page_break()

    # --------------------------------------------------------------------------
    # LIST OF FIGURES, TABLES, AND ABBREVIATIONS
    # --------------------------------------------------------------------------
    p_lof_h = doc.add_paragraph()
    p_lof_h.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_lof_h.paragraph_format.space_before = Pt(6)
    p_lof_h.paragraph_format.space_after = Pt(8)
    r = p_lof_h.add_run("LIST OF FIGURES")
    r.font.bold = True
    r.font.size = Pt(13)

    lof_tbl = doc.add_table(rows=len(rc.FIGURES_LIST), cols=2)
    lof_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    lof_tbl.autofit = False
    lof_tbl.columns[0].width = Inches(1.2)
    lof_tbl.columns[1].width = Inches(4.5)
    for i, (fid, ftitle) in enumerate(rc.FIGURES_LIST):
        r = lof_tbl.rows[i]
        set_cell_margins(r.cells[0], 18, 18, 30, 30)
        set_cell_margins(r.cells[1], 18, 18, 30, 30)
        p0 = r.cells[0].paragraphs[0]
        p0.paragraph_format.line_spacing = 1.05
        p0.paragraph_format.space_after = Pt(1)
        r0 = p0.add_run(fid)
        r0.font.bold = True
        r0.font.size = Pt(9.5)
        p1 = r.cells[1].paragraphs[0]
        p1.paragraph_format.line_spacing = 1.05
        p1.paragraph_format.space_after = Pt(1)
        r1 = p1.add_run(ftitle)
        r1.font.size = Pt(9.5)

    p_lot_h = doc.add_paragraph()
    p_lot_h.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_lot_h.paragraph_format.space_before = Pt(12)
    p_lot_h.paragraph_format.space_after = Pt(8)
    r = p_lot_h.add_run("LIST OF TABLES")
    r.font.bold = True
    r.font.size = Pt(13)

    lot_tbl = doc.add_table(rows=len(rc.TABLES_LIST), cols=2)
    lot_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    lot_tbl.autofit = False
    lot_tbl.columns[0].width = Inches(1.2)
    lot_tbl.columns[1].width = Inches(4.5)
    for i, (tid, ttitle) in enumerate(rc.TABLES_LIST):
        r = lot_tbl.rows[i]
        set_cell_margins(r.cells[0], 18, 18, 30, 30)
        set_cell_margins(r.cells[1], 18, 18, 30, 30)
        p0 = r.cells[0].paragraphs[0]
        p0.paragraph_format.line_spacing = 1.05
        p0.paragraph_format.space_after = Pt(1)
        r0 = p0.add_run(tid)
        r0.font.bold = True
        r0.font.size = Pt(9.5)
        p1 = r.cells[1].paragraphs[0]
        p1.paragraph_format.line_spacing = 1.05
        p1.paragraph_format.space_after = Pt(1)
        r1 = p1.add_run(ttitle)
        r1.font.size = Pt(9.5)

    doc.add_page_break()

    p_loa_h = doc.add_paragraph()
    p_loa_h.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_loa_h.paragraph_format.space_before = Pt(6)
    p_loa_h.paragraph_format.space_after = Pt(8)
    r = p_loa_h.add_run("LIST OF ABBREVIATIONS")
    r.font.bold = True
    r.font.size = Pt(13)

    loa_tbl = doc.add_table(rows=len(rc.ABBREVIATIONS), cols=2)
    loa_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    loa_tbl.autofit = False
    loa_tbl.columns[0].width = Inches(1.5)
    loa_tbl.columns[1].width = Inches(4.2)
    for i, (abbr, fdesc) in enumerate(rc.ABBREVIATIONS):
        r = loa_tbl.rows[i]
        set_cell_margins(r.cells[0], 16, 16, 30, 30)
        set_cell_margins(r.cells[1], 16, 16, 30, 30)
        p0 = r.cells[0].paragraphs[0]
        p0.paragraph_format.line_spacing = 1.05
        p0.paragraph_format.space_after = Pt(1)
        r0 = p0.add_run(abbr)
        r0.font.bold = True
        r0.font.size = Pt(9.5)
        p1 = r.cells[1].paragraphs[0]
        p1.paragraph_format.line_spacing = 1.05
        p1.paragraph_format.space_after = Pt(1)
        r1 = p1.add_run(fdesc)
        r1.font.size = Pt(9.5)

    doc.add_page_break()

    # --------------------------------------------------------------------------
    # CHAPTERS 1 THROUGH 8 (Continuous flow inside each chapter)
    # --------------------------------------------------------------------------
    chapters = [rc.CHAPTER_1, rc.CHAPTER_2, rc.CHAPTER_3, rc.CHAPTER_4, rc.CHAPTER_5, rc.CHAPTER_6, rc.CHAPTER_7, rc.CHAPTER_8]

    for chap in chapters:
        # Chapter Heading (Bold Black)
        p_ch = doc.add_paragraph()
        p_ch.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p_ch.paragraph_format.space_before = Pt(14)
        p_ch.paragraph_format.space_after = Pt(8)
        p_ch.paragraph_format.keep_with_next = True
        r_ch = p_ch.add_run(f"CHAPTER {chap['number']}: {chap['title'].upper()}")
        r_ch.font.name = 'Times New Roman'
        r_ch.font.size = Pt(15)
        r_ch.font.bold = True
        r_ch.font.color.rgb = RGBColor(0, 0, 0)

        # Underline rule in black
        p_rule = doc.add_paragraph()
        p_rule.paragraph_format.space_before = Pt(0)
        p_rule.paragraph_format.space_after = Pt(8)
        p_rule.paragraph_format.keep_with_next = True
        r_ru = p_rule.add_run("―" * 55)
        r_ru.font.color.rgb = RGBColor(0, 0, 0)

        for sec in chap['sections']:
            # Section Heading
            p_sec = doc.add_paragraph()
            p_sec.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p_sec.paragraph_format.space_before = Pt(10)
            p_sec.paragraph_format.space_after = Pt(4)
            p_sec.paragraph_format.keep_with_next = True
            r_sec = p_sec.add_run(f"{sec['number']} {sec['title']}")
            r_sec.font.name = 'Times New Roman'
            r_sec.font.size = Pt(12)
            r_sec.font.bold = True
            r_sec.font.color.rgb = RGBColor(0, 0, 0)

            # Paragraphs
            for text in sec['paragraphs']:
                if text.startswith("[IMAGE:"):
                    parts = text[7:-1].split(':', 1)
                    img_key = parts[0]
                    caption = parts[1]
                    png_path = os.path.join(DOCX_IMAGES_DIR, f"{img_key}.png")
                    img_path = png_path if os.path.exists(png_path) else rc.SCREENSHOT_PATHS.get(img_key)

                    if img_path and os.path.exists(img_path):
                        p_img = doc.add_paragraph()
                        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        p_img.paragraph_format.space_before = Pt(6)
                        p_img.paragraph_format.space_after = Pt(2)
                        p_img.paragraph_format.keep_with_next = True
                        p_img.add_run().add_picture(img_path, width=Inches(4.8))

                        p_cap = doc.add_paragraph()
                        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        p_cap.paragraph_format.space_before = Pt(2)
                        p_cap.paragraph_format.space_after = Pt(8)
                        r_cap = p_cap.add_run(caption)
                        r_cap.font.name = 'Times New Roman'
                        r_cap.font.size = Pt(9.5)
                        r_cap.font.bold = True
                        r_cap.font.color.rgb = RGBColor(0, 0, 0)
                    continue

                if text.startswith("```"):
                    code_lines = text.strip('`').replace('text\n', '').split('\n')
                    p_code = doc.add_paragraph()
                    p_code.paragraph_format.space_before = Pt(3)
                    p_code.paragraph_format.space_after = Pt(6)
                    p_code.paragraph_format.line_spacing = 1.02
                    for line in code_lines:
                        r_c = p_code.add_run(line + "\n")
                        r_c.font.name = 'Consolas'
                        r_c.font.size = Pt(8.5)
                        r_c.font.color.rgb = RGBColor(0, 0, 0)
                    continue

                p = doc.add_paragraph()
                p.paragraph_format.line_spacing = 1.15
                p.paragraph_format.space_after = Pt(4)
                p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                r_p = p.add_run(text)
                r_p.font.name = 'Times New Roman'
                r_p.font.size = Pt(11)
                r_p.font.color.rgb = RGBColor(0, 0, 0)

            # Table in Section
            if 'table' in sec:
                tbl_info = sec['table']
                p_cap = doc.add_paragraph()
                p_cap.alignment = WD_ALIGN_PARAGRAPH.LEFT
                p_cap.paragraph_format.space_before = Pt(8)
                p_cap.paragraph_format.space_after = Pt(3)
                p_cap.paragraph_format.keep_with_next = True
                r_cap = p_cap.add_run(tbl_info['title'])
                r_cap.font.name = 'Times New Roman'
                r_cap.font.size = Pt(10)
                r_cap.font.bold = True
                r_cap.font.color.rgb = RGBColor(0, 0, 0)

                headers = tbl_info['headers']
                rows = tbl_info['rows']
                tbl = doc.add_table(rows=len(rows) + 1, cols=len(headers))
                tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
                set_table_borders(tbl)

                # Header Row in Solid Black
                for col_idx, header_text in enumerate(headers):
                    cell = tbl.rows[0].cells[col_idx]
                    set_cell_shading(cell, "000000") # Black header
                    set_cell_margins(cell, top=60, bottom=60, left=70, right=70)
                    p_h = cell.paragraphs[0]
                    p_h.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    p_h.paragraph_format.space_after = Pt(0)
                    r_h = p_h.add_run(header_text)
                    r_h.font.name = 'Times New Roman'
                    r_h.font.size = Pt(8.5)
                    r_h.font.bold = True
                    r_h.font.color.rgb = RGBColor(255, 255, 255)

                # Data Rows
                for row_idx, row_data in enumerate(rows):
                    bg_color = "F9FAFB" if row_idx % 2 == 1 else "FFFFFF"
                    for col_idx, cell_value in enumerate(row_data):
                        cell = tbl.rows[row_idx + 1].cells[col_idx]
                        if bg_color != "FFFFFF":
                            set_cell_shading(cell, bg_color)
                        set_cell_margins(cell, top=45, bottom=45, left=60, right=60)
                        p_c = cell.paragraphs[0]
                        p_c.paragraph_format.space_after = Pt(0)
                        p_c.paragraph_format.line_spacing = 1.05
                        r_c = p_c.add_run(str(cell_value))
                        r_c.font.name = 'Times New Roman'
                        r_c.font.size = Pt(8.0)
                        r_c.font.color.rgb = RGBColor(0, 0, 0)
                        if str(cell_value) in ["PASS", "Healthy", "Yes"]:
                            r_c.font.bold = True

                doc.add_paragraph().paragraph_format.space_after = Pt(6)

        # Page break at the end of each major chapter
        doc.add_page_break()

    # --------------------------------------------------------------------------
    # REFERENCES / BIBLIOGRAPHY
    # --------------------------------------------------------------------------
    p_ref_h = doc.add_paragraph()
    p_ref_h.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_ref_h.paragraph_format.space_before = Pt(14)
    p_ref_h.paragraph_format.space_after = Pt(8)
    r = p_ref_h.add_run("REFERENCES / BIBLIOGRAPHY")
    r.font.name = 'Times New Roman'
    r.font.size = Pt(15)
    r.font.bold = True
    r.font.color.rgb = RGBColor(0, 0, 0)

    p_r_rule = doc.add_paragraph()
    p_r_rule.paragraph_format.space_before = Pt(0)
    p_r_rule.paragraph_format.space_after = Pt(8)
    r_ru = p_r_rule.add_run("―" * 55)
    r_ru.font.color.rgb = RGBColor(0, 0, 0)

    for i, ref in enumerate(rc.REFERENCES):
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Inches(0.3)
        p.paragraph_format.first_line_indent = Inches(-0.3)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.line_spacing = 1.15
        r_num = p.add_run(f"[{i+1}]\t")
        r_num.font.bold = True
        r_num.font.size = Pt(10)
        r_text = p.add_run(ref)
        r_text.font.size = Pt(10)

    doc.add_page_break()

    # --------------------------------------------------------------------------
    # APPENDICES A THROUGH E
    # --------------------------------------------------------------------------
    p_app_h = doc.add_paragraph()
    p_app_h.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_app_h.paragraph_format.space_before = Pt(14)
    p_app_h.paragraph_format.space_after = Pt(8)
    r = p_app_h.add_run("APPENDICES")
    r.font.name = 'Times New Roman'
    r.font.size = Pt(15)
    r.font.bold = True
    r.font.color.rgb = RGBColor(0, 0, 0)

    for app in rc.APPENDICES:
        p_ah = doc.add_paragraph()
        p_ah.paragraph_format.space_before = Pt(10)
        p_ah.paragraph_format.space_after = Pt(4)
        p_ah.paragraph_format.keep_with_next = True
        r_ah = p_ah.add_run(f"Appendix {app['id']}: {app['title']}")
        r_ah.font.name = 'Times New Roman'
        r_ah.font.size = Pt(12)
        r_ah.font.bold = True
        r_ah.font.color.rgb = RGBColor(0, 0, 0)

        p_ad = doc.add_paragraph(app['description'])
        p_ad.paragraph_format.space_after = Pt(6)
        p_ad.paragraph_format.line_spacing = 1.15

        if app['id'] == 'A':
            for fig_id, fig_title in rc.FIGURES_LIST[7:]:
                p_it = doc.add_paragraph()
                p_it.paragraph_format.left_indent = Inches(0.2)
                p_it.paragraph_format.space_after = Pt(2)
                r_id = p_it.add_run(f"{fig_id}: ")
                r_id.font.bold = True
                p_it.add_run(fig_title)

        elif app['id'] == 'B':
            for code_block in rc.APPENDIX_B_CODE:
                p_fn = doc.add_paragraph()
                p_fn.paragraph_format.space_before = Pt(6)
                p_fn.paragraph_format.space_after = Pt(2)
                p_fn.paragraph_format.keep_with_next = True
                r_fn = p_fn.add_run(f"Listing: {code_block['filename']}")
                r_fn.font.bold = True
                r_fn.font.size = Pt(10)
                r_fn.font.color.rgb = RGBColor(0, 0, 0)

                p_c = doc.add_paragraph()
                p_c.paragraph_format.space_before = Pt(2)
                p_c.paragraph_format.space_after = Pt(6)
                p_c.paragraph_format.line_spacing = 1.02
                for line in code_block['code'].split('\n'):
                    r_line = p_c.add_run(line + "\n")
                    r_line.font.name = 'Consolas'
                    r_line.font.size = Pt(8.0)

        elif app['id'] == 'C':
            for dt in rc.DATA_DICTIONARY_TABLES:
                p_tcap = doc.add_paragraph()
                p_tcap.paragraph_format.space_before = Pt(6)
                p_tcap.paragraph_format.space_after = Pt(2)
                p_tcap.paragraph_format.keep_with_next = True
                r_tc = p_tcap.add_run(dt['title'])
                r_tc.font.bold = True
                r_tc.font.size = Pt(9.5)
                r_tc.font.color.rgb = RGBColor(0, 0, 0)

                t = doc.add_table(rows=len(dt['rows']) + 1, cols=len(dt['headers']))
                t.alignment = WD_TABLE_ALIGNMENT.CENTER
                set_table_borders(t)

                for c_idx, h_text in enumerate(dt['headers']):
                    cell = t.rows[0].cells[c_idx]
                    set_cell_shading(cell, "000000")
                    set_cell_margins(cell, 50, 50, 60, 60)
                    p_th = cell.paragraphs[0]
                    r_th = p_th.add_run(h_text)
                    r_th.font.bold = True
                    r_th.font.size = Pt(8.0)
                    r_th.font.color.rgb = RGBColor(255, 255, 255)

                for r_idx, r_data in enumerate(dt['rows']):
                    bg = "F9FAFB" if r_idx % 2 == 1 else "FFFFFF"
                    for c_idx, val in enumerate(r_data):
                        cell = t.rows[r_idx + 1].cells[c_idx]
                        if bg != "FFFFFF": set_cell_shading(cell, bg)
                        set_cell_margins(cell, 40, 40, 50, 50)
                        p_td = cell.paragraphs[0]
                        p_td.paragraph_format.space_after = Pt(0)
                        r_td = p_td.add_run(str(val))
                        r_td.font.size = Pt(7.5)

        elif app['id'] == 'D':
            for line in rc.APPENDIX_D_TEXT.split('\n'):
                p_d = doc.add_paragraph()
                p_d.paragraph_format.space_after = Pt(2)
                if line.strip().startswith(('git ', 'pip ', 'python ', 'SECRET_KEY', 'DEBUG', 'ALLOWED', 'EMAIL_')):
                    r_code = p_d.add_run(line)
                    r_code.font.name = 'Consolas'
                    r_code.font.size = Pt(8.5)
                else:
                    r_txt = p_d.add_run(line)
                    r_txt.font.size = Pt(10)

        elif app['id'] == 'E':
            for line in rc.APPENDIX_E_TEXT.split('\n'):
                p_e = doc.add_paragraph()
                p_e.paragraph_format.space_after = Pt(2)
                r_txt = p_e.add_run(line)
                r_txt.font.size = Pt(10)
                if line.strip().startswith(('1.', '2.')):
                    r_txt.font.bold = True

    try:
        doc.save(DOCX_PATH)
        print(f"Word document saved successfully to: {DOCX_PATH} ({os.path.getsize(DOCX_PATH)} bytes)")
    except PermissionError:
        alt_docx = os.path.join(BASE_DIR, "Invenpro_Project_Report_Complete.docx")
        doc.save(alt_docx)
        print(f"Word document was open in MS Word. Saved successfully to: {alt_docx} ({os.path.getsize(alt_docx)} bytes)")


# ------------------------------------------------------------------------------
# 2. BUILD COMPLETE ADOBE PDF (.PDF)
# ------------------------------------------------------------------------------
def generate_pdf():
    print("Generating Complete Adobe PDF document (.pdf)...")
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

    body_style = ParagraphStyle(
        'FullBody',
        parent=base_styles['Normal'],
        fontName='Times-Roman',
        fontSize=10.5,
        leading=14.5,
        alignment=TA_JUSTIFY,
        textColor=colors.HexColor('#000000'),
        spaceAfter=4
    )

    chap_title_style = ParagraphStyle(
        'FullChapTitle',
        parent=base_styles['Normal'],
        fontName='Times-Bold',
        fontSize=14.5,
        leading=18,
        alignment=TA_LEFT,
        textColor=colors.HexColor('#000000'),
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )

    sec_title_style = ParagraphStyle(
        'FullSecTitle',
        parent=base_styles['Normal'],
        fontName='Times-Bold',
        fontSize=11.5,
        leading=15,
        alignment=TA_LEFT,
        textColor=colors.HexColor('#000000'),
        spaceBefore=8,
        spaceAfter=3,
        keepWithNext=True
    )

    caption_style = ParagraphStyle(
        'FullCaption',
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

    table_title_style = ParagraphStyle(
        'FullTblTitle',
        parent=base_styles['Normal'],
        fontName='Times-Bold',
        fontSize=9.5,
        leading=12.5,
        alignment=TA_LEFT,
        textColor=colors.HexColor('#000000'),
        spaceBefore=6,
        spaceAfter=3,
        keepWithNext=True
    )

    tbl_hdr_style = ParagraphStyle(
        'FullTblHdr',
        parent=base_styles['Normal'],
        fontName='Times-Bold',
        fontSize=8,
        leading=10,
        alignment=TA_CENTER,
        textColor=colors.white
    )

    tbl_cell_style = ParagraphStyle(
        'FullTblCell',
        parent=base_styles['Normal'],
        fontName='Times-Roman',
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor('#000000')
    )

    tbl_cell_center = ParagraphStyle(
        'FullTblCellCenter',
        parent=tbl_cell_style,
        alignment=TA_CENTER
    )

    code_style = ParagraphStyle(
        'FullCode',
        parent=base_styles['Normal'],
        fontName='Courier',
        fontSize=7.0,
        leading=9.0,
        textColor=colors.HexColor('#000000'),
        backColor=colors.HexColor('#F9FAFB')
    )

    story = []

    # 1. COVER PAGE (Annexure-I Layout)
    story.append(Spacer(1, 15))
    story.append(Paragraph("<b>Annexure-I</b>", ParagraphStyle(
        'Annex', parent=base_styles['Normal'], fontName='Times-Roman', fontSize=12, alignment=TA_CENTER, textColor=colors.HexColor('#000000')
    )))
    story.append(Spacer(1, 28))

    story.append(Paragraph("<b>INVENPRO – SMART RESTAURANT INVENTORY &<br/>MULTI-TENANT STOCK CONTROL SYSTEM</b>", ParagraphStyle(
        'CTitle', parent=base_styles['Normal'], fontName='Times-Bold', fontSize=16, leading=21, alignment=TA_CENTER, textColor=colors.HexColor('#000000')
    )))
    story.append(Spacer(1, 30))

    sub_report_text = (
        "<b>Project report</b><br/>"
        "<font size=10.5>Submitted in partial fulfilment of the requirements for the award of degree of</font><br/>"
        "<b>B. TECH CSE</b>"
    )
    story.append(Paragraph(sub_report_text, ParagraphStyle(
        'CSub', parent=base_styles['Normal'], fontName='Times-Roman', fontSize=11.5, leading=15.5, alignment=TA_CENTER, textColor=colors.HexColor('#000000')
    )))
    story.append(Spacer(1, 24))

    sub_to_text = (
        "<font size=10.5>Submitted to</font><br/>"
        "<b>LOVELY PROFESSIONAL UNIVERSITY</b><br/>"
        "<b>PHAGWARA, PUNJAB</b>"
    )
    story.append(Paragraph(sub_to_text, ParagraphStyle(
        'CSubTo', parent=base_styles['Normal'], fontName='Times-Roman', fontSize=12.5, leading=16.5, alignment=TA_CENTER, textColor=colors.HexColor('#000000')
    )))
    story.append(Spacer(1, 16))

    if os.path.exists(LOGO_PATH):
        story.append(RLImage(LOGO_PATH, width=175, height=58))
        story.append(Spacer(1, 24))

    by_text = (
        "<b>Submitted by</b><br/>"
        f"<b>Name of student: {rc.METADATA['student_name']}</b><br/>"
        f"<b>Registration Number: {rc.METADATA['reg_no']}</b><br/>"
        f"<b>Signature of the student:</b>"
    )
    story.append(Paragraph(by_text, ParagraphStyle(
        'CBy', parent=base_styles['Normal'], fontName='Times-Roman', fontSize=10.5, leading=14.5, alignment=TA_LEFT, textColor=colors.HexColor('#000000')
    )))
    story.append(Spacer(1, 4))

    if os.path.exists(SIGNATURE_PATH):
        story.append(RLImage(SIGNATURE_PATH, width=88, height=46))

    story.append(PageBreak())

    # 2. UNIVERSITY PROFILE & ABSTRACT (Page 2)
    story.append(Paragraph("<b>Lovely Professional University (LPU), Phagwara, Punjab</b>", ParagraphStyle(
        'LPUH', parent=base_styles['Normal'], fontName='Times-Bold', fontSize=12, leading=15, textColor=colors.HexColor('#000000'), spaceBefore=6, spaceAfter=5
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
        'AbsH', parent=base_styles['Normal'], fontName='Times-Bold', fontSize=11.5, leading=14.5, textColor=colors.HexColor('#000000'), spaceBefore=6, spaceAfter=4
    )))
    for p_txt in rc.ABSTRACT_TEXT.split('\n\n'):
        story.append(Paragraph(p_txt, body_style))

    story.append(PageBreak())

    # 3. TABLE OF CONTENTS
    story.append(Paragraph("<b>TABLE OF CONTENTS</b>", ParagraphStyle(
        'TOCH', parent=base_styles['Normal'], fontName='Times-Bold', fontSize=13.5, alignment=TA_CENTER, textColor=colors.HexColor('#000000'), spaceAfter=10
    )))
    toc_data = []
    for item_title, page_str in TOC_ITEMS:
        is_bold = item_title.startswith("Chapter") or item_title.startswith("References") or item_title.startswith("Appendix") or item_title in ["Abstract", "List of Figures", "List of Tables", "List of Abbreviations"]
        font_tag = "<b>" if is_bold else ""
        end_font_tag = "</b>" if is_bold else ""
        toc_data.append([
            Paragraph(f"{font_tag}{item_title}{end_font_tag}", tbl_cell_style),
            Paragraph(f"{font_tag}{page_str}{end_font_tag}", tbl_cell_center)
        ])
    toc_tbl = Table(toc_data, colWidths=[content_width * 0.88, content_width * 0.12])
    toc_tbl.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 2),
        ('RIGHTPADDING', (0,0), (-1,-1), 2),
        ('TOPPADDING', (0,0), (-1,-1), 1.8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1.8),
        ('LINEBELOW', (0,0), (-1,-1), 0.25, colors.HexColor('#E5E7EB')),
    ]))
    story.append(toc_tbl)
    story.append(PageBreak())

    # 4. LIST OF FIGURES & LIST OF TABLES
    story.append(Paragraph("<b>LIST OF FIGURES</b>", ParagraphStyle(
        'LOFH', parent=base_styles['Normal'], fontName='Times-Bold', fontSize=13, alignment=TA_CENTER, textColor=colors.HexColor('#000000'), spaceAfter=8
    )))
    lof_data = [[Paragraph(f"<b>{fid}</b>", tbl_cell_style), Paragraph(ftitle, tbl_cell_style)] for fid, ftitle in rc.FIGURES_LIST]
    lof_tbl = Table(lof_data, colWidths=[content_width * 0.22, content_width * 0.78])
    lof_tbl.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LINEBELOW', (0,0), (-1,-1), 0.25, colors.HexColor('#E5E7EB')),
    ]))
    story.append(lof_tbl)
    story.append(Spacer(1, 10))

    story.append(Paragraph("<b>LIST OF TABLES</b>", ParagraphStyle(
        'LOTH', parent=base_styles['Normal'], fontName='Times-Bold', fontSize=13, alignment=TA_CENTER, textColor=colors.HexColor('#000000'), spaceAfter=8
    )))
    lot_data = [[Paragraph(f"<b>{tid}</b>", tbl_cell_style), Paragraph(ttitle, tbl_cell_style)] for tid, ttitle in rc.TABLES_LIST]
    lot_tbl = Table(lot_data, colWidths=[content_width * 0.22, content_width * 0.78])
    lot_tbl.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LINEBELOW', (0,0), (-1,-1), 0.25, colors.HexColor('#E5E7EB')),
    ]))
    story.append(lot_tbl)
    story.append(PageBreak())

    # 5. LIST OF ABBREVIATIONS
    story.append(Paragraph("<b>LIST OF ABBREVIATIONS</b>", ParagraphStyle(
        'LOAH', parent=base_styles['Normal'], fontName='Times-Bold', fontSize=13, alignment=TA_CENTER, textColor=colors.HexColor('#000000'), spaceAfter=8
    )))
    loa_data = [[Paragraph(f"<b>{abbr}</b>", tbl_cell_style), Paragraph(fdesc, tbl_cell_style)] for abbr, fdesc in rc.ABBREVIATIONS]
    loa_tbl = Table(loa_data, colWidths=[content_width * 0.25, content_width * 0.75])
    loa_tbl.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LINEBELOW', (0,0), (-1,-1), 0.25, colors.HexColor('#E5E7EB')),
    ]))
    story.append(loa_tbl)
    story.append(PageBreak())

    # 6. ALL 8 CHAPTERS (Continuous flow inside chapters, no blank gaps)
    chapters = [rc.CHAPTER_1, rc.CHAPTER_2, rc.CHAPTER_3, rc.CHAPTER_4, rc.CHAPTER_5, rc.CHAPTER_6, rc.CHAPTER_7, rc.CHAPTER_8]
    for chap in chapters:
        ch_heading = f"CHAPTER {chap['number']}: {chap['title'].upper()}"
        story.append(Paragraph(ch_heading, chap_title_style))
        story.append(HRFlowable(width="100%", thickness=1.0, color=colors.HexColor('#000000'), spaceAfter=8))

        for sec in chap['sections']:
            sec_heading = f"{sec['number']} {sec['title']}"
            story.append(Paragraph(sec_heading, sec_title_style))

            for text in sec['paragraphs']:
                if text.startswith("[IMAGE:"):
                    parts = text[7:-1].split(':', 1)
                    img_key = parts[0]
                    caption = parts[1]
                    png_path = os.path.join(DOCX_IMAGES_DIR, f"{img_key}.png")
                    img_path = png_path if os.path.exists(png_path) else rc.SCREENSHOT_PATHS.get(img_key)

                    if img_path and os.path.exists(img_path):
                        img_flow = RLImage(img_path, width=content_width, height=content_width * (9.0 / 16.0))
                        cap_flow = Paragraph(caption, caption_style)
                        story.append(KeepTogether([Spacer(1, 4), img_flow, cap_flow, Spacer(1, 4)]))
                    continue

                if text.startswith("```"):
                    code_lines = text.strip('`').replace('text\n', '')
                    c_par = Paragraph(f"<font face='Courier' size=7.2>{code_lines.replace(' ', '&nbsp;').replace(chr(10), '<br/>')}</font>", code_style)
                    c_tbl = Table([[c_par]], colWidths=[content_width])
                    c_tbl.setStyle(TableStyle([
                        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F9FAFB')),
                        ('BOX', (0,0), (-1,-1), 0.4, colors.HexColor('#000000')),
                        ('TOPPADDING', (0,0), (-1,-1), 4),
                        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                        ('LEFTPADDING', (0,0), (-1,-1), 6),
                        ('RIGHTPADDING', (0,0), (-1,-1), 6),
                    ]))
                    story.append(Spacer(1, 3))
                    story.append(c_tbl)
                    story.append(Spacer(1, 4))
                    continue

                story.append(Paragraph(text, body_style))

            # Table in Section
            if 'table' in sec:
                tbl_info = sec['table']
                story.append(Spacer(1, 3))
                story.append(Paragraph(tbl_info['title'], table_title_style))

                headers = tbl_info['headers']
                rows = tbl_info['rows']
                col_count = len(headers)

                if col_count == 4:
                    col_widths = [content_width * 0.22, content_width * 0.26, content_width * 0.26, content_width * 0.26]
                elif col_count == 5:
                    col_widths = [content_width * 0.20, content_width * 0.22, content_width * 0.18, content_width * 0.24, content_width * 0.16]
                elif col_count == 6:
                    col_widths = [content_width * 0.09, content_width * 0.25, content_width * 0.24, content_width * 0.22, content_width * 0.12, content_width * 0.08]
                else:
                    col_widths = [content_width / col_count] * col_count

                tbl_data = [[Paragraph(f"<b>{h}</b>", tbl_hdr_style) for h in headers]]
                for r_idx, r_vals in enumerate(rows):
                    row_cells = []
                    for c_idx, val in enumerate(r_vals):
                        v_str = str(val)
                        if v_str == "PASS":
                            c_p = Paragraph("<b>PASS</b>", tbl_cell_center)
                        else:
                            c_p = Paragraph(v_str, tbl_cell_style)
                        row_cells.append(c_p)
                    tbl_data.append(row_cells)

                grid_tbl = Table(tbl_data, colWidths=col_widths, repeatRows=1)
                t_style = [
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#000000')), # Solid black header
                    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                    ('TOPPADDING', (0,0), (-1,-1), 2.5),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
                    ('LEFTPADDING', (0,0), (-1,-1), 3),
                    ('RIGHTPADDING', (0,0), (-1,-1), 3),
                    ('GRID', (0,0), (-1,-1), 0.35, colors.HexColor('#000000')),
                ]
                for r_i in range(1, len(tbl_data)):
                    if r_i % 2 == 0:
                        t_style.append(('BACKGROUND', (0, r_i), (-1, r_i), colors.HexColor('#F9FAFB')))
                grid_tbl.setStyle(TableStyle(t_style))
                story.append(grid_tbl)
                story.append(Spacer(1, 6))

        # Page break at end of each chapter
        story.append(PageBreak())

    # 7. REFERENCES
    story.append(Paragraph("<b>REFERENCES / BIBLIOGRAPHY</b>", chap_title_style))
    story.append(HRFlowable(width="100%", thickness=1.0, color=colors.HexColor('#000000'), spaceAfter=8))
    ref_data = [[Paragraph(f"<b>[{i+1}]</b>", tbl_cell_center), Paragraph(ref, body_style)] for i, ref in enumerate(rc.REFERENCES)]
    ref_tbl = Table(ref_data, colWidths=[content_width * 0.08, content_width * 0.92])
    ref_tbl.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('LEFTPADDING', (0,0), (-1,-1), 2),
        ('RIGHTPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(ref_tbl)
    story.append(PageBreak())

    # 8. APPENDICES A THROUGH E
    story.append(Paragraph("<b>APPENDICES</b>", chap_title_style))
    story.append(HRFlowable(width="100%", thickness=1.0, color=colors.HexColor('#000000'), spaceAfter=8))

    for app in rc.APPENDICES:
        story.append(Paragraph(f"<b>Appendix {app['id']}: {app['title']}</b>", sec_title_style))
        story.append(Paragraph(app['description'], body_style))
        story.append(Spacer(1, 3))

        if app['id'] == 'A':
            app_a_data = [[Paragraph(f"<b>{fid}</b>", tbl_cell_style), Paragraph(ftitle, tbl_cell_style)] for fid, ftitle in rc.FIGURES_LIST[7:]]
            app_a_tbl = Table(app_a_data, colWidths=[content_width * 0.22, content_width * 0.78])
            app_a_tbl.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('TOPPADDING', (0,0), (-1,-1), 2),
                ('BOTTOMPADDING', (0,0), (-1,-1), 2),
                ('LINEBELOW', (0,0), (-1,-1), 0.25, colors.HexColor('#E5E7EB')),
            ]))
            story.append(app_a_tbl)
            story.append(Spacer(1, 6))

        elif app['id'] == 'B':
            for code_block in rc.APPENDIX_B_CODE:
                story.append(Paragraph(f"<b>Listing: {code_block['filename']}</b>", table_title_style))
                c_par = Paragraph(f"<font face='Courier' size=6.8>{code_block['code'].replace(' ', '&nbsp;').replace(chr(10), '<br/>')}</font>", code_style)
                c_tbl = Table([[c_par]], colWidths=[content_width])
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

        elif app['id'] == 'C':
            for dt in rc.DATA_DICTIONARY_TABLES:
                story.append(Paragraph(f"<b>{dt['title']}</b>", table_title_style))
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

        elif app['id'] == 'D':
            d_lines = rc.APPENDIX_D_TEXT.replace(' ', '&nbsp;').replace('\n', '<br/>')
            story.append(Paragraph(f"<font face='Courier' size=7.8>{d_lines}</font>", code_style))
            story.append(Spacer(1, 6))

        elif app['id'] == 'E':
            for line in rc.APPENDIX_E_TEXT.split('\n'):
                if line.strip().startswith(('1.', '2.')):
                    story.append(Paragraph(f"<b>{line}</b>", sec_title_style))
                else:
                    story.append(Paragraph(line, body_style))
            story.append(Spacer(1, 6))

    try:
        doc.build(story, canvasmaker=ProfessionalNumberedCanvas)
        print(f"PDF document saved successfully to: {PDF_PATH} ({os.path.getsize(PDF_PATH)} bytes)")
        # Also create copy to Invenpro_Project_Report_Complete.pdf
        import shutil
        alt_pdf = os.path.join(BASE_DIR, "Invenpro_Project_Report_Complete.pdf")
        shutil.copyfile(PDF_PATH, alt_pdf)
        print(f"Backup copy saved to: {alt_pdf}")
    except PermissionError:
        alt_pdf = os.path.join(BASE_DIR, "Invenpro_Project_Report_Complete.pdf")
        doc_alt = SimpleDocTemplate(alt_pdf, pagesize=A4, leftMargin=108, rightMargin=72, topMargin=72, bottomMargin=72)
        doc_alt.build(story, canvasmaker=ProfessionalNumberedCanvas)
        print(f"PDF was open. Saved successfully to: {alt_pdf} ({os.path.getsize(alt_pdf)} bytes)")

if __name__ == '__main__':
    generate_docx()
    generate_pdf()
    print("Both full proper reports generated successfully!")
