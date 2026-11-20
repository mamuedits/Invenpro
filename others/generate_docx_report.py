"""
generate_docx_report.py
Generates the comprehensive academic Word document for Invenpro Project Report.
Following standard LPU INT253 B.Tech CSE Project Report guidelines.
"""

import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

import report_content as rc

def create_element(name):
    return OxmlElement(name)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
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

def set_table_borders(table, color="D1D5DB", sz="4", val="single"):
    tblPr = table._tbl.tblPr
    borders_xml = f'''
    <w:tblBorders {nsdecls("w")}>
        <w:top w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>
        <w:left w:val="none"/>
        <w:bottom w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>
        <w:right w:val="none"/>
        <w:insideH w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>
        <w:insideV w:val="none"/>
    </w:tblBorders>
    '''
    tblPr.append(parse_xml(borders_xml))

def add_footer_page_number(run):
    fldSimple = OxmlElement('w:fldSimple')
    fldSimple.set(qn('w:instr'), 'PAGE')
    run._r.append(fldSimple)

def build_docx():
    doc = docx.Document()

    # Configure A4 page geometry & margins
    section = doc.sections[0]
    section.page_width = Inches(8.27)   # 21.0 cm A4
    section.page_height = Inches(11.69) # 29.7 cm A4
    section.left_margin = Inches(1.5)   # Binding margin
    section.right_margin = Inches(1.0)
    section.top_margin = Inches(1.0)
    section.bottom_margin = Inches(1.0)

    # Configure Normal Style
    normal_style = doc.styles['Normal']
    normal_style.font.name = 'Times New Roman'
    normal_style.font.size = Pt(12)
    normal_style.font.color.rgb = RGBColor(17, 24, 39) # #111827 Dark charcoal
    normal_style.paragraph_format.line_spacing = 1.5
    normal_style.paragraph_format.space_after = Pt(6)
    normal_style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    # Configure Footer
    footer = section.footer
    footer_p = footer.paragraphs[0]
    footer_p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    f_run = footer_p.add_run(f"Invenpro – INT253 Academic Project Report  |  Page ")
    f_run.font.name = 'Times New Roman'
    f_run.font.size = Pt(10)
    f_run.font.italic = True
    f_run.font.color.rgb = RGBColor(107, 114, 128)
    p_num_run = footer_p.add_run()
    p_num_run.font.name = 'Times New Roman'
    p_num_run.font.size = Pt(10)
    p_num_run.font.bold = True
    p_num_run.font.color.rgb = RGBColor(107, 114, 128)
    add_footer_page_number(p_num_run)

    # ==========================================================================
    # 1. COVER PAGE / TITLE PAGE
    # ==========================================================================
    # College standard Title Page format
    p_top = doc.add_paragraph()
    p_top.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_top.paragraph_format.space_before = Pt(36)
    p_top.paragraph_format.space_after = Pt(12)
    r = p_top.add_run("A PROJECT REPORT ON\n")
    r.font.name = 'Times New Roman'
    r.font.size = Pt(14)
    r.font.bold = True
    r.font.color.rgb = RGBColor(55, 65, 81)

    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(18)
    p_title.paragraph_format.space_after = Pt(24)
    r_title = p_title.add_run(rc.METADATA['project_title'])
    r_title.font.name = 'Times New Roman'
    r_title.font.size = Pt(18)
    r_title.font.bold = True
    r_title.font.color.rgb = RGBColor(6, 78, 59) # Deep Emerald

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.paragraph_format.space_before = Pt(12)
    p_sub.paragraph_format.space_after = Pt(18)
    r_sub = p_sub.add_run(
        "Submitted in partial fulfilment of the requirements for the award of the degree of\n"
        f"{rc.METADATA['degree']}\nIN\n{rc.METADATA['department']}\n\n"
        f"Course Code: {rc.METADATA['course_code']} ({rc.METADATA['course_name']})"
    )
    r_sub.font.name = 'Times New Roman'
    r_sub.font.size = Pt(12)
    r_sub.font.italic = True
    r_sub.font.color.rgb = RGBColor(75, 85, 99)

    p_box = doc.add_paragraph()
    p_box.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_box.paragraph_format.space_before = Pt(30)
    p_box.paragraph_format.space_after = Pt(30)

    # 2-column borderless table for Submitted By & Under the Guidance Of
    meta_table = doc.add_table(rows=1, cols=2)
    meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_table.autofit = False
    meta_table.columns[0].width = Inches(2.7)
    meta_table.columns[1].width = Inches(2.7)

    cell_left = meta_table.cell(0, 0)
    cell_right = meta_table.cell(0, 1)

    p_l = cell_left.paragraphs[0]
    p_l.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_l.paragraph_format.line_spacing = 1.3
    r = p_l.add_run("SUBMITTED BY:\n")
    r.font.bold = True
    r.font.size = Pt(11)
    r.font.color.rgb = RGBColor(6, 78, 59)
    r = p_l.add_run(f"Name: {rc.METADATA['student_name']}\n")
    r.font.bold = True
    r.font.size = Pt(12)
    r = p_l.add_run(f"Registration No: {rc.METADATA['reg_no']}\n")
    r.font.size = Pt(11)
    r = p_l.add_run(f"Semester: {rc.METADATA['semester']}\nAcademic Year: {rc.METADATA['academic_year']}")
    r.font.size = Pt(11)

    p_r = cell_right.paragraphs[0]
    p_r.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p_r.paragraph_format.line_spacing = 1.3
    r = p_r.add_run("UNDER THE GUIDANCE OF:\n")
    r.font.bold = True
    r.font.size = Pt(11)
    r.font.color.rgb = RGBColor(6, 78, 59)
    r = p_r.add_run(f"{rc.METADATA['guide_name']}\n")
    r.font.bold = True
    r.font.size = Pt(12)
    r = p_r.add_run(f"{rc.METADATA['guide_designation']}\n")
    r.font.size = Pt(11)
    r = p_r.add_run(f"Department of Computer Science & Engineering\n{rc.METADATA['school']}")
    r.font.size = Pt(11)

    p_bottom = doc.add_paragraph()
    p_bottom.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_bottom.paragraph_format.space_before = Pt(40)
    r_bot = p_bottom.add_run(
        f"{rc.METADATA['school']}\n"
        f"{rc.METADATA['university']}\n"
        f"{rc.METADATA['submission_date']}"
    )
    r_bot.font.name = 'Times New Roman'
    r_bot.font.size = Pt(12)
    r_bot.font.bold = True
    r_bot.font.color.rgb = RGBColor(17, 24, 39)

    doc.add_page_break()

    # ==========================================================================
    # 2. ABSTRACT (No Certificate/Declaration/Acknowledgement per user request)
    # ==========================================================================
    h_abs = doc.add_paragraph()
    h_abs.alignment = WD_ALIGN_PARAGRAPH.CENTER
    h_abs.paragraph_format.space_before = Pt(12)
    h_abs.paragraph_format.space_after = Pt(18)
    r_abs = h_abs.add_run("ABSTRACT")
    r_abs.font.name = 'Times New Roman'
    r_abs.font.size = Pt(16)
    r_abs.font.bold = True
    r_abs.font.color.rgb = RGBColor(6, 78, 59)

    for para in rc.ABSTRACT_TEXT.split('\n\n'):
        p = doc.add_paragraph(para)
        p.paragraph_format.line_spacing = 1.5
        p.paragraph_format.space_after = Pt(8)
        p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    doc.add_page_break()

    # ==========================================================================
    # 3. TABLE OF CONTENTS
    # ==========================================================================
    h_toc = doc.add_paragraph()
    h_toc.alignment = WD_ALIGN_PARAGRAPH.CENTER
    h_toc.paragraph_format.space_before = Pt(12)
    h_toc.paragraph_format.space_after = Pt(18)
    r_toc = h_toc.add_run("TABLE OF CONTENTS")
    r_toc.font.name = 'Times New Roman'
    r_toc.font.size = Pt(16)
    r_toc.font.bold = True
    r_toc.font.color.rgb = RGBColor(6, 78, 59)

    toc_items = [
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
        ("    4.1 System Architecture (Django MTV & Tenant Scoping)", "18"),
        ("    4.2 UML Use Case Diagram", "20"),
        ("    4.3 UML Activity Diagram", "21"),
        ("    4.4 UML Class Diagram", "22"),
        ("    4.5 UML Sequence Diagrams", "23"),
        ("    4.6 Database Design and Relational Schema", "25"),
        ("    4.7 Entity-Relationship (ER) Diagram", "27"),
        ("    4.8 Module Design", "28"),
        ("    4.9 UI/UX Design System", "29"),
        ("Chapter 5: Implementation", "30"),
        ("    5.1 Development Environment", "30"),
        ("    5.2 Project Structure", "31"),
        ("    5.3 Technologies Used", "32"),
        ("    5.4 Module Implementation Walkthrough", "33"),
        ("    5.5 Authentication & Live Email OTP Stack", "34"),
        ("    5.6 Database Implementation and Migrations", "35"),
        ("    5.7 Mathematical Model for Burn-Rate and Runway Forecasting", "36"),
        ("    5.8 Application Screenshots and Interface Walkthrough", "37"),
        ("Chapter 6: Testing and Validation", "45"),
        ("    6.1 Testing Methodology", "45"),
        ("    6.2 Automated Test Suite Execution Results (26 Test Cases)", "46"),
        ("    6.3 Security Testing", "49"),
        ("    6.4 Performance and Usability Testing", "50"),
        ("Chapter 7: Results and Discussion", "51"),
        ("    7.1 Project Outcomes", "51"),
        ("    7.2 Features Successfully Implemented", "52"),
        ("    7.3 Operational Results and Live Metrics", "53"),
        ("    7.4 Technical Discussion", "54"),
        ("Chapter 8: Conclusion and Future Scope", "55"),
        ("    8.1 Conclusion", "55"),
        ("    8.2 Limitations of the System", "56"),
        ("    8.3 Future Scope and Enhancements", "57"),
        ("References / Bibliography", "58"),
        ("Appendix A: Application UI Screenshots & Field Reference", "60"),
        ("Appendix B: Selected Core Source Code Listings", "62"),
        ("Appendix C: Complete Database Schema & Data Dictionary", "66"),
        ("Appendix D: Installation and Environment Configuration Guide", "69"),
        ("Appendix E: User and Operations Manual", "70")
    ]

    toc_table = doc.add_table(rows=len(toc_items), cols=2)
    toc_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    toc_table.autofit = False
    toc_table.columns[0].width = Inches(5.0)
    toc_table.columns[1].width = Inches(0.7)

    for i, (title, page) in enumerate(toc_items):
        row = toc_table.rows[i]
        c0, c1 = row.cells[0], row.cells[1]
        set_cell_margins(c0, top=30, bottom=30, left=50, right=50)
        set_cell_margins(c1, top=30, bottom=30, left=50, right=50)

        p0 = c0.paragraphs[0]
        p0.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p0.paragraph_format.line_spacing = 1.15
        p0.paragraph_format.space_after = Pt(2)
        r0 = p0.add_run(title)
        r0.font.name = 'Times New Roman'
        r0.font.size = Pt(11)
        if title.startswith("Chapter") or title.startswith("References") or title.startswith("Appendix") or title in ["Abstract", "List of Figures", "List of Tables", "List of Abbreviations"]:
            r0.font.bold = True

        p1 = c1.paragraphs[0]
        p1.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p1.paragraph_format.line_spacing = 1.15
        p1.paragraph_format.space_after = Pt(2)
        r1 = p1.add_run(page)
        r1.font.name = 'Times New Roman'
        r1.font.size = Pt(11)
        if r0.font.bold:
            r1.font.bold = True

    doc.add_page_break()

    # ==========================================================================
    # 4. LIST OF FIGURES & LIST OF TABLES
    # ==========================================================================
    h_lof = doc.add_paragraph()
    h_lof.alignment = WD_ALIGN_PARAGRAPH.CENTER
    h_lof.paragraph_format.space_before = Pt(12)
    h_lof.paragraph_format.space_after = Pt(14)
    r_lof = h_lof.add_run("LIST OF FIGURES")
    r_lof.font.name = 'Times New Roman'
    r_lof.font.size = Pt(16)
    r_lof.font.bold = True
    r_lof.font.color.rgb = RGBColor(6, 78, 59)

    lof_table = doc.add_table(rows=len(rc.FIGURES_LIST), cols=2)
    lof_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    lof_table.autofit = False
    lof_table.columns[0].width = Inches(1.2)
    lof_table.columns[1].width = Inches(4.5)

    for i, (fig_id, fig_title) in enumerate(rc.FIGURES_LIST):
        r = lof_table.rows[i]
        c0, c1 = r.cells[0], r.cells[1]
        set_cell_margins(c0, top=30, bottom=30, left=40, right=40)
        set_cell_margins(c1, top=30, bottom=30, left=40, right=40)
        p0 = c0.paragraphs[0]
        r0 = p0.add_run(fig_id)
        r0.font.bold = True
        r0.font.size = Pt(11)
        p1 = c1.paragraphs[0]
        r1 = p1.add_run(fig_title)
        r1.font.size = Pt(11)

    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    h_lot = doc.add_paragraph()
    h_lot.alignment = WD_ALIGN_PARAGRAPH.CENTER
    h_lot.paragraph_format.space_before = Pt(12)
    h_lot.paragraph_format.space_after = Pt(14)
    r_lot = h_lot.add_run("LIST OF TABLES")
    r_lot.font.name = 'Times New Roman'
    r_lot.font.size = Pt(16)
    r_lot.font.bold = True
    r_lot.font.color.rgb = RGBColor(6, 78, 59)

    lot_table = doc.add_table(rows=len(rc.TABLES_LIST), cols=2)
    lot_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    lot_table.autofit = False
    lot_table.columns[0].width = Inches(1.2)
    lot_table.columns[1].width = Inches(4.5)

    for i, (tbl_id, tbl_title) in enumerate(rc.TABLES_LIST):
        r = lot_table.rows[i]
        c0, c1 = r.cells[0], r.cells[1]
        set_cell_margins(c0, top=30, bottom=30, left=40, right=40)
        set_cell_margins(c1, top=30, bottom=30, left=40, right=40)
        p0 = c0.paragraphs[0]
        r0 = p0.add_run(tbl_id)
        r0.font.bold = True
        r0.font.size = Pt(11)
        p1 = c1.paragraphs[0]
        r1 = p1.add_run(tbl_title)
        r1.font.size = Pt(11)

    doc.add_page_break()

    # ==========================================================================
    # 5. LIST OF ABBREVIATIONS
    # ==========================================================================
    h_loa = doc.add_paragraph()
    h_loa.alignment = WD_ALIGN_PARAGRAPH.CENTER
    h_loa.paragraph_format.space_before = Pt(12)
    h_loa.paragraph_format.space_after = Pt(14)
    r_loa = h_loa.add_run("LIST OF ABBREVIATIONS")
    r_loa.font.name = 'Times New Roman'
    r_loa.font.size = Pt(16)
    r_loa.font.bold = True
    r_loa.font.color.rgb = RGBColor(6, 78, 59)

    loa_table = doc.add_table(rows=len(rc.ABBREVIATIONS), cols=2)
    loa_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    loa_table.autofit = False
    loa_table.columns[0].width = Inches(1.5)
    loa_table.columns[1].width = Inches(4.2)

    for i, (abbr, full) in enumerate(rc.ABBREVIATIONS):
        r = loa_table.rows[i]
        c0, c1 = r.cells[0], r.cells[1]
        set_cell_margins(c0, top=25, bottom=25, left=40, right=40)
        set_cell_margins(c1, top=25, bottom=25, left=40, right=40)
        p0 = c0.paragraphs[0]
        r0 = p0.add_run(abbr)
        r0.font.bold = True
        r0.font.size = Pt(11)
        p1 = c1.paragraphs[0]
        r1 = p1.add_run(full)
        r1.font.size = Pt(11)

    doc.add_page_break()

    # ==========================================================================
    # 6. CHAPTERS 1 TO 8
    # ==========================================================================
    chapters = [rc.CHAPTER_1, rc.CHAPTER_2, rc.CHAPTER_3, rc.CHAPTER_4, rc.CHAPTER_5, rc.CHAPTER_6, rc.CHAPTER_7, rc.CHAPTER_8]

    for chap in chapters:
        # Chapter Heading
        p_ch = doc.add_paragraph()
        p_ch.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p_ch.paragraph_format.space_before = Pt(18)
        p_ch.paragraph_format.space_after = Pt(12)
        r_ch = p_ch.add_run(f"CHAPTER {chap['number']}\n{chap['title'].upper()}")
        r_ch.font.name = 'Times New Roman'
        r_ch.font.size = Pt(16)
        r_ch.font.bold = True
        r_ch.font.color.rgb = RGBColor(6, 78, 59)

        for sec in chap['sections']:
            # Section Heading
            p_sec = doc.add_paragraph()
            p_sec.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p_sec.paragraph_format.space_before = Pt(14)
            p_sec.paragraph_format.space_after = Pt(6)
            r_sec = p_sec.add_run(f"{sec['number']} {sec['title']}")
            r_sec.font.name = 'Times New Roman'
            r_sec.font.size = Pt(13)
            r_sec.font.bold = True
            r_sec.font.color.rgb = RGBColor(31, 41, 55)

            # Paragraphs
            for text in sec['paragraphs']:
                if text.startswith("[IMAGE:"):
                    # Format: [IMAGE:key:Figure X.Y: Caption]
                    parts = text[7:-1].split(':', 1)
                    img_key = parts[0]
                    caption = parts[1]
                    png_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docx_images", f"{img_key}.png")
                    img_path = png_path if os.path.exists(png_path) else rc.SCREENSHOT_PATHS.get(img_key)
                    if img_path and os.path.exists(img_path):
                        p_img = doc.add_paragraph()
                        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        p_img.paragraph_format.space_before = Pt(8)
                        p_img.paragraph_format.space_after = Pt(4)
                        p_img.add_run().add_picture(img_path, width=Inches(5.4))

                        p_cap = doc.add_paragraph()
                        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        p_cap.paragraph_format.space_before = Pt(2)
                        p_cap.paragraph_format.space_after = Pt(12)
                        r_cap = p_cap.add_run(caption)
                        r_cap.font.name = 'Times New Roman'
                        r_cap.font.size = Pt(10)
                        r_cap.font.italic = True
                        r_cap.font.color.rgb = RGBColor(75, 85, 99)
                    continue

                if text.startswith("```"):
                    # Code snippet block
                    code_lines = text.strip('`').replace('text\n', '').split('\n')
                    p_code = doc.add_paragraph()
                    p_code.paragraph_format.space_before = Pt(4)
                    p_code.paragraph_format.space_after = Pt(8)
                    p_code.paragraph_format.line_spacing = 1.05
                    for line in code_lines:
                        r_c = p_code.add_run(line + "\n")
                        r_c.font.name = 'Consolas'
                        r_c.font.size = Pt(9)
                        r_c.font.color.rgb = RGBColor(31, 41, 55)
                    continue

                p = doc.add_paragraph()
                p.paragraph_format.line_spacing = 1.5
                p.paragraph_format.space_after = Pt(6)
                p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                r_p = p.add_run(text)
                r_p.font.name = 'Times New Roman'
                r_p.font.size = Pt(12)

            # Check if section has a table
            if 'table' in sec:
                tbl_info = sec['table']
                p_cap = doc.add_paragraph()
                p_cap.alignment = WD_ALIGN_PARAGRAPH.LEFT
                p_cap.paragraph_format.space_before = Pt(10)
                p_cap.paragraph_format.space_after = Pt(4)
                r_cap = p_cap.add_run(tbl_info['title'])
                r_cap.font.name = 'Times New Roman'
                r_cap.font.size = Pt(11)
                r_cap.font.bold = True
                r_cap.font.color.rgb = RGBColor(6, 78, 59)

                # Render table
                headers = tbl_info['headers']
                rows = tbl_info['rows']
                tbl = doc.add_table(rows=len(rows) + 1, cols=len(headers))
                tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
                set_table_borders(tbl)

                # Header Row
                hdr_cells = tbl.rows[0].cells
                for col_idx, header_text in enumerate(headers):
                    cell = hdr_cells[col_idx]
                    set_cell_shading(cell, "064E3B") # Deep Forest Green
                    set_cell_margins(cell, top=80, bottom=80, left=100, right=100)
                    p_h = cell.paragraphs[0]
                    p_h.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    p_h.paragraph_format.space_after = Pt(0)
                    r_h = p_h.add_run(header_text)
                    r_h.font.name = 'Times New Roman'
                    r_h.font.size = Pt(9.5)
                    r_h.font.bold = True
                    r_h.font.color.rgb = RGBColor(255, 255, 255)

                # Data Rows
                for row_idx, row_data in enumerate(rows):
                    row_cells = tbl.rows[row_idx + 1].cells
                    bg_color = "F9FAFB" if row_idx % 2 == 1 else "FFFFFF"
                    for col_idx, cell_value in enumerate(row_data):
                        cell = row_cells[col_idx]
                        if bg_color != "FFFFFF":
                            set_cell_shading(cell, bg_color)
                        set_cell_margins(cell, top=60, bottom=60, left=80, right=80)
                        p_c = cell.paragraphs[0]
                        p_c.paragraph_format.space_after = Pt(0)
                        p_c.paragraph_format.line_spacing = 1.15
                        r_c = p_c.add_run(str(cell_value))
                        r_c.font.name = 'Times New Roman'
                        r_c.font.size = Pt(9.0)
                        if str(cell_value) in ["PASS", "Healthy"]:
                            r_c.font.bold = True
                            r_c.font.color.rgb = RGBColor(5, 150, 105) # Green
                        elif str(cell_value) in ["Low"]:
                            r_c.font.bold = True
                            r_c.font.color.rgb = RGBColor(217, 119, 6) # Amber
                        elif str(cell_value) in ["Critical", "out_of_stock"]:
                            r_c.font.bold = True
                            r_c.font.color.rgb = RGBColor(220, 38, 38) # Red

                doc.add_paragraph().paragraph_format.space_after = Pt(8)

        doc.add_page_break()

    # ==========================================================================
    # 7. REFERENCES / BIBLIOGRAPHY
    # ==========================================================================
    h_ref = doc.add_paragraph()
    h_ref.alignment = WD_ALIGN_PARAGRAPH.LEFT
    h_ref.paragraph_format.space_before = Pt(18)
    h_ref.paragraph_format.space_after = Pt(14)
    r_ref = h_ref.add_run("REFERENCES / BIBLIOGRAPHY")
    r_ref.font.name = 'Times New Roman'
    r_ref.font.size = Pt(16)
    r_ref.font.bold = True
    r_ref.font.color.rgb = RGBColor(6, 78, 59)

    for i, ref in enumerate(rc.REFERENCES):
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Inches(0.4)
        p.paragraph_format.first_line_indent = Inches(-0.4)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.line_spacing = 1.25
        r_num = p.add_run(f"[{i+1}]\t")
        r_num.font.name = 'Times New Roman'
        r_num.font.size = Pt(11)
        r_num.font.bold = True
        r_text = p.add_run(ref)
        r_text.font.name = 'Times New Roman'
        r_text.font.size = Pt(11)

    doc.add_page_break()

    # ==========================================================================
    # 8. APPENDICES A THROUGH E
    # ==========================================================================
    h_app = doc.add_paragraph()
    h_app.alignment = WD_ALIGN_PARAGRAPH.LEFT
    h_app.paragraph_format.space_before = Pt(18)
    h_app.paragraph_format.space_after = Pt(14)
    r_app = h_app.add_run("APPENDICES")
    r_app.font.name = 'Times New Roman'
    r_app.font.size = Pt(16)
    r_app.font.bold = True
    r_app.font.color.rgb = RGBColor(6, 78, 59)

    for app in rc.APPENDICES:
        p_ah = doc.add_paragraph()
        p_ah.paragraph_format.space_before = Pt(14)
        p_ah.paragraph_format.space_after = Pt(6)
        r_ah = p_ah.add_run(f"Appendix {app['id']}: {app['title']}")
        r_ah.font.name = 'Times New Roman'
        r_ah.font.size = Pt(13)
        r_ah.font.bold = True
        r_ah.font.color.rgb = RGBColor(31, 41, 55)

        p_ad = doc.add_paragraph(app['description'])
        p_ad.paragraph_format.space_after = Pt(8)
        p_ad.paragraph_format.line_spacing = 1.3

        if app['id'] == 'A':
            # Appendix A: Screenshots summary reference table
            p_sub = doc.add_paragraph("Summary of Production User Interface Screens:")
            p_sub.paragraph_format.space_after = Pt(4)
            p_sub.runs[0].font.bold = True
            for fig_id, fig_title in rc.FIGURES_LIST[7:]: # Figure 5.1 to 5.11
                p_it = doc.add_paragraph()
                p_it.paragraph_format.left_indent = Inches(0.2)
                p_it.paragraph_format.space_after = Pt(3)
                r_id = p_it.add_run(f"{fig_id}: ")
                r_id.font.bold = True
                p_it.add_run(fig_title)

        elif app['id'] == 'B':
            # Appendix B: Selected Source Code
            for code_block in rc.APPENDIX_B_CODE:
                p_fn = doc.add_paragraph()
                p_fn.paragraph_format.space_before = Pt(8)
                p_fn.paragraph_format.space_after = Pt(2)
                r_fn = p_fn.add_run(f"Listing: {code_block['filename']}")
                r_fn.font.bold = True
                r_fn.font.size = Pt(10.5)
                r_fn.font.color.rgb = RGBColor(6, 78, 59)

                p_c = doc.add_paragraph()
                p_c.paragraph_format.space_before = Pt(2)
                p_c.paragraph_format.space_after = Pt(8)
                p_c.paragraph_format.line_spacing = 1.05
                for line in code_block['code'].split('\n'):
                    r_line = p_c.add_run(line + "\n")
                    r_line.font.name = 'Consolas'
                    r_line.font.size = Pt(8.5)

        elif app['id'] == 'C':
            # Appendix C: Data Dictionary Tables
            for dt in rc.DATA_DICTIONARY_TABLES:
                p_tcap = doc.add_paragraph()
                p_tcap.paragraph_format.space_before = Pt(8)
                p_tcap.paragraph_format.space_after = Pt(3)
                r_tc = p_tcap.add_run(dt['title'])
                r_tc.font.bold = True
                r_tc.font.size = Pt(10)
                r_tc.font.color.rgb = RGBColor(6, 78, 59)

                t = doc.add_table(rows=len(dt['rows']) + 1, cols=len(dt['headers']))
                t.alignment = WD_TABLE_ALIGNMENT.CENTER
                set_table_borders(t)

                for c_idx, h_text in enumerate(dt['headers']):
                    cell = t.rows[0].cells[c_idx]
                    set_cell_shading(cell, "064E3B")
                    set_cell_margins(cell, top=60, bottom=60, left=80, right=80)
                    p_th = cell.paragraphs[0]
                    r_th = p_th.add_run(h_text)
                    r_th.font.name = 'Times New Roman'
                    r_th.font.size = Pt(9)
                    r_th.font.bold = True
                    r_th.font.color.rgb = RGBColor(255, 255, 255)

                for r_idx, r_data in enumerate(dt['rows']):
                    bg = "F9FAFB" if r_idx % 2 == 1 else "FFFFFF"
                    for c_idx, val in enumerate(r_data):
                        cell = t.rows[r_idx + 1].cells[c_idx]
                        if bg != "FFFFFF":
                            set_cell_shading(cell, bg)
                        set_cell_margins(cell, top=50, bottom=50, left=60, right=60)
                        p_td = cell.paragraphs[0]
                        p_td.paragraph_format.space_after = Pt(0)
                        r_td = p_td.add_run(str(val))
                        r_td.font.name = 'Times New Roman'
                        r_td.font.size = Pt(8.5)

        elif app['id'] == 'D':
            # Appendix D: Setup Guide
            for line in rc.APPENDIX_D_TEXT.split('\n'):
                p_d = doc.add_paragraph()
                p_d.paragraph_format.space_after = Pt(3)
                p_d.paragraph_format.line_spacing = 1.15
                if line.strip().startswith(('git ', 'pip ', 'python ', 'SECRET_KEY', 'DEBUG', 'ALLOWED', 'EMAIL_')):
                    r_code = p_d.add_run(line)
                    r_code.font.name = 'Consolas'
                    r_code.font.size = Pt(9)
                else:
                    r_txt = p_d.add_run(line)
                    r_txt.font.name = 'Times New Roman'
                    r_txt.font.size = Pt(11)

        elif app['id'] == 'E':
            # Appendix E: User Manual
            for line in rc.APPENDIX_E_TEXT.split('\n'):
                p_e = doc.add_paragraph()
                p_e.paragraph_format.space_after = Pt(3)
                p_e.paragraph_format.line_spacing = 1.2
                r_txt = p_e.add_run(line)
                r_txt.font.name = 'Times New Roman'
                r_txt.font.size = Pt(11)
                if line.strip().startswith(('1.', '2.', '3.')):
                    r_txt.font.bold = True

    output_path = r"c:\LPU\7th sem\INT253\Pythonproject\Invenpro_Project_Report.docx"
    doc.save(output_path)
    print(f"Word Document successfully saved to {output_path} (Size: {os.path.getsize(output_path)} bytes)")

if __name__ == '__main__':
    build_docx()
