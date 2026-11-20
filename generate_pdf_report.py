"""
generate_pdf_report.py
Generates the comprehensive academic PDF document for Invenpro Project Report.
Following standard LPU INT253 B.Tech CSE Project Report guidelines.
Uses ReportLab with two-pass NumberedCanvas for exact "Page X of Y" pagination.
"""

import os
from PIL import Image as PILImage
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT

import report_content as rc

class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to dynamically compute total page count and draw
    professional running headers and footers with 'Page X of Y'.
    """
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
        # Omit headers and footers on Cover Page (Page 1)
        if self._pageNumber > 1:
            self.saveState()
            self.setFont('Times-Roman', 8.5)
            self.setFillColor(colors.HexColor('#4B5563')) # Gray 600

            # Running Header
            header_text = "INVENPRO: Smart Restaurant Inventory & Stock Runway Control System"
            self.drawString(108, 800, header_text)
            self.drawRightString(523, 800, "INT253 Project Report")
            self.setStrokeColor(colors.HexColor('#E5E7EB'))
            self.setLineWidth(0.6)
            self.line(108, 794, 523, 794)

            # Running Footer
            footer_left = f"Department of CSE, LPU  |  Muhammed PP (12324844)"
            footer_right = f"Page {self._pageNumber} of {page_count}"
            self.line(108, 54, 523, 54)
            self.drawString(108, 42, footer_left)
            self.drawRightString(523, 42, footer_right)
            self.restoreState()

def build_pdf():
    pdf_filename = r"c:\LPU\7th sem\INT253\Pythonproject\Invenpro_Project_Report.pdf"

    # Margins: Left 1.5" (108pt), Right 1.0" (72pt), Top 1.0" (72pt), Bottom 1.0" (72pt)
    # Total A4 width: 595.27pt. Content width: 595.27 - 108 - 72 = 415.27pt (~5.77 inches)
    content_width = 415.27

    doc = SimpleDocTemplate(
        pdf_filename,
        pagesize=A4,
        leftMargin=108,
        rightMargin=72,
        topMargin=72,
        bottomMargin=72
    )

    base_styles = getSampleStyleSheet()

    # Custom Typography Styles
    body_style = ParagraphStyle(
        'AcademicBody',
        parent=base_styles['Normal'],
        fontName='Times-Roman',
        fontSize=11,
        leading=16,
        alignment=TA_JUSTIFY,
        textColor=colors.HexColor('#111827'),
        spaceAfter=6
    )

    title_cover_style = ParagraphStyle(
        'CoverTitle',
        parent=base_styles['Normal'],
        fontName='Times-Bold',
        fontSize=17,
        leading=22,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#064E3B'),
        spaceAfter=14
    )

    chap_title_style = ParagraphStyle(
        'ChapterTitle',
        parent=base_styles['Normal'],
        fontName='Times-Bold',
        fontSize=15,
        leading=19,
        alignment=TA_LEFT,
        textColor=colors.HexColor('#064E3B'),
        spaceBefore=14,
        spaceAfter=10
    )

    sec_title_style = ParagraphStyle(
        'SectionTitle',
        parent=base_styles['Normal'],
        fontName='Times-Bold',
        fontSize=12.5,
        leading=16,
        alignment=TA_LEFT,
        textColor=colors.HexColor('#1F2937'),
        spaceBefore=12,
        spaceAfter=6
    )

    caption_style = ParagraphStyle(
        'FigureCaption',
        parent=base_styles['Normal'],
        fontName='Times-Italic',
        fontSize=9.5,
        leading=13,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#4B5563'),
        spaceBefore=3,
        spaceAfter=10
    )

    table_title_style = ParagraphStyle(
        'TableCaption',
        parent=base_styles['Normal'],
        fontName='Times-Bold',
        fontSize=10,
        leading=13,
        alignment=TA_LEFT,
        textColor=colors.HexColor('#064E3B'),
        spaceBefore=8,
        spaceAfter=4
    )

    tbl_header_style = ParagraphStyle(
        'TblHdr',
        parent=base_styles['Normal'],
        fontName='Times-Bold',
        fontSize=8.5,
        leading=11,
        alignment=TA_CENTER,
        textColor=colors.white
    )

    tbl_cell_style = ParagraphStyle(
        'TblCell',
        parent=base_styles['Normal'],
        fontName='Times-Roman',
        fontSize=8.0,
        leading=10.5,
        textColor=colors.HexColor('#111827')
    )

    tbl_cell_center = ParagraphStyle(
        'TblCellCenter',
        parent=tbl_cell_style,
        alignment=TA_CENTER
    )

    code_style = ParagraphStyle(
        'CodeStyle',
        parent=base_styles['Normal'],
        fontName='Courier',
        fontSize=8.0,
        leading=10.5,
        textColor=colors.HexColor('#1F2937'),
        backColor=colors.HexColor('#F9FAFB')
    )

    story = []

    # ==========================================================================
    # 1. COVER PAGE / TITLE PAGE (Annexure-I Standard)
    # ==========================================================================
    story.append(Spacer(1, 20))
    p_top = Paragraph("<b>A PROJECT REPORT ON</b>", ParagraphStyle(
        'TopSub', parent=base_styles['Normal'], fontName='Times-Bold', fontSize=12, alignment=TA_CENTER, textColor=colors.HexColor('#4B5563')
    ))
    story.append(p_top)
    story.append(Spacer(1, 14))

    story.append(Paragraph(rc.METADATA['project_title'], title_cover_style))
    story.append(Spacer(1, 12))

    sub_text = (
        "<i>Submitted in partial fulfilment of the requirements for the award of the degree of</i><br/>"
        f"<b>{rc.METADATA['degree']}</b><br/>IN<br/><b>{rc.METADATA['department']}</b><br/><br/>"
        f"<b>Course Code: {rc.METADATA['course_code']} ({rc.METADATA['course_name']})</b>"
    )
    story.append(Paragraph(sub_text, ParagraphStyle(
        'SubHead', parent=base_styles['Normal'], fontName='Times-Roman', fontSize=11, leading=15, alignment=TA_CENTER, textColor=colors.HexColor('#374151')
    )))
    story.append(Spacer(1, 30))

    # Meta Table: Submitted By & Under the Guidance Of
    left_meta = (
        f"<b>SUBMITTED BY:</b><br/>"
        f"<b>Name:</b> {rc.METADATA['student_name']}<br/>"
        f"<b>Registration No:</b> {rc.METADATA['reg_no']}<br/>"
        f"<b>Semester:</b> {rc.METADATA['semester']}<br/>"
        f"<b>Academic Year:</b> {rc.METADATA['academic_year']}"
    )
    right_meta = (
        f"<b>UNDER THE GUIDANCE OF:</b><br/>"
        f"<b>{rc.METADATA['guide_name']}</b><br/>"
        f"{rc.METADATA['guide_designation']}<br/>"
        f"Department of Computer Science & Engineering<br/>"
        f"{rc.METADATA['school']}"
    )

    meta_data = [
        [
            Paragraph(left_meta, ParagraphStyle('ML', parent=tbl_cell_style, fontSize=9.5, leading=13)),
            Paragraph(right_meta, ParagraphStyle('MR', parent=tbl_cell_style, fontSize=9.5, leading=13, alignment=TA_RIGHT))
        ]
    ]
    meta_tbl = Table(meta_data, colWidths=[content_width * 0.48, content_width * 0.52])
    meta_tbl.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(meta_tbl)
    story.append(Spacer(1, 45))

    inst_text = (
        f"<b>{rc.METADATA['school']}</b><br/>"
        f"<b>{rc.METADATA['university']}</b><br/>"
        f"<b>{rc.METADATA['submission_date']}</b>"
    )
    story.append(Paragraph(inst_text, ParagraphStyle(
        'InstText', parent=base_styles['Normal'], fontName='Times-Roman', fontSize=11, leading=15, alignment=TA_CENTER, textColor=colors.HexColor('#111827')
    )))

    story.append(PageBreak())

    # ==========================================================================
    # 2. ABSTRACT (No Certificate/Declaration/Acknowledgement per user request)
    # ==========================================================================
    story.append(Paragraph("<b>ABSTRACT</b>", ParagraphStyle(
        'AbsTitle', parent=base_styles['Normal'], fontName='Times-Bold', fontSize=15, alignment=TA_CENTER, textColor=colors.HexColor('#064E3B'), spaceAfter=14
    )))

    for para in rc.ABSTRACT_TEXT.split('\n\n'):
        story.append(Paragraph(para, body_style))
        story.append(Spacer(1, 4))

    story.append(PageBreak())

    # ==========================================================================
    # 3. TABLE OF CONTENTS
    # ==========================================================================
    story.append(Paragraph("<b>TABLE OF CONTENTS</b>", ParagraphStyle(
        'TOCTitle', parent=base_styles['Normal'], fontName='Times-Bold', fontSize=15, alignment=TA_CENTER, textColor=colors.HexColor('#064E3B'), spaceAfter=14
    )))

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

    toc_data = []
    for item_title, page_str in toc_items:
        is_bold = item_title.startswith("Chapter") or item_title.startswith("References") or item_title.startswith("Appendix") or item_title in ["Abstract", "List of Figures", "List of Tables", "List of Abbreviations"]
        font_tag = "<b>" if is_bold else ""
        end_font_tag = "</b>" if is_bold else ""
        t_par = Paragraph(f"{font_tag}{item_title}{end_font_tag}", tbl_cell_style)
        p_par = Paragraph(f"{font_tag}{page_str}{end_font_tag}", tbl_cell_center)
        toc_data.append([t_par, p_par])

    toc_tbl = Table(toc_data, colWidths=[content_width * 0.88, content_width * 0.12])
    toc_tbl.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 2),
        ('RIGHTPADDING', (0,0), (-1,-1), 2),
        ('TOPPADDING', (0,0), (-1,-1), 2.2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.2),
        ('LINEBELOW', (0,0), (-1,-1), 0.3, colors.HexColor('#F3F4F6')),
    ]))
    story.append(toc_tbl)
    story.append(PageBreak())

    # ==========================================================================
    # 4. LIST OF FIGURES & LIST OF TABLES
    # ==========================================================================
    story.append(Paragraph("<b>LIST OF FIGURES</b>", ParagraphStyle(
        'LOFTitle', parent=base_styles['Normal'], fontName='Times-Bold', fontSize=15, alignment=TA_CENTER, textColor=colors.HexColor('#064E3B'), spaceAfter=12
    )))

    lof_data = []
    for fid, ftitle in rc.FIGURES_LIST:
        lof_data.append([
            Paragraph(f"<b>{fid}</b>", tbl_cell_style),
            Paragraph(ftitle, tbl_cell_style)
        ])
    lof_tbl = Table(lof_data, colWidths=[content_width * 0.22, content_width * 0.78])
    lof_tbl.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('LINEBELOW', (0,0), (-1,-1), 0.3, colors.HexColor('#F3F4F6')),
    ]))
    story.append(lof_tbl)
    story.append(Spacer(1, 14))

    story.append(Paragraph("<b>LIST OF TABLES</b>", ParagraphStyle(
        'LOTTitle', parent=base_styles['Normal'], fontName='Times-Bold', fontSize=15, alignment=TA_CENTER, textColor=colors.HexColor('#064E3B'), spaceAfter=12
    )))

    lot_data = []
    for tid, ttitle in rc.TABLES_LIST:
        lot_data.append([
            Paragraph(f"<b>{tid}</b>", tbl_cell_style),
            Paragraph(ttitle, tbl_cell_style)
        ])
    lot_tbl = Table(lot_data, colWidths=[content_width * 0.22, content_width * 0.78])
    lot_tbl.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('LINEBELOW', (0,0), (-1,-1), 0.3, colors.HexColor('#F3F4F6')),
    ]))
    story.append(lot_tbl)
    story.append(PageBreak())

    # ==========================================================================
    # 5. LIST OF ABBREVIATIONS
    # ==========================================================================
    story.append(Paragraph("<b>LIST OF ABBREVIATIONS</b>", ParagraphStyle(
        'LOADTitle', parent=base_styles['Normal'], fontName='Times-Bold', fontSize=15, alignment=TA_CENTER, textColor=colors.HexColor('#064E3B'), spaceAfter=12
    )))

    loa_data = []
    for abbr, full_desc in rc.ABBREVIATIONS:
        loa_data.append([
            Paragraph(f"<b>{abbr}</b>", tbl_cell_style),
            Paragraph(full_desc, tbl_cell_style)
        ])
    loa_tbl = Table(loa_data, colWidths=[content_width * 0.25, content_width * 0.75])
    loa_tbl.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 2.2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.2),
        ('LINEBELOW', (0,0), (-1,-1), 0.3, colors.HexColor('#F3F4F6')),
    ]))
    story.append(loa_tbl)
    story.append(PageBreak())

    # ==========================================================================
    # 6. CHAPTERS 1 TO 8
    # ==========================================================================
    chapters = [rc.CHAPTER_1, rc.CHAPTER_2, rc.CHAPTER_3, rc.CHAPTER_4, rc.CHAPTER_5, rc.CHAPTER_6, rc.CHAPTER_7, rc.CHAPTER_8]

    for chap in chapters:
        ch_heading = f"CHAPTER {chap['number']}: {chap['title'].upper()}"
        story.append(Paragraph(ch_heading, chap_title_style))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#064E3B'), spaceAfter=10))

        for sec in chap['sections']:
            sec_heading = f"{sec['number']} {sec['title']}"
            story.append(Paragraph(sec_heading, sec_title_style))

            for text in sec['paragraphs']:
                if text.startswith("[IMAGE:"):
                    parts = text[7:-1].split(':', 1)
                    img_key = parts[0]
                    caption = parts[1]
                    png_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docx_images", f"{img_key}.png")
                    img_path = png_path if os.path.exists(png_path) else rc.SCREENSHOT_PATHS.get(img_key)

                    if img_path and os.path.exists(img_path):
                        # Calculate proportional height for 415pt width (16:9 ratio -> 233.4pt)
                        img_flow = Image(img_path, width=content_width, height=content_width * (9.0 / 16.0))
                        cap_flow = Paragraph(caption, caption_style)
                        story.append(KeepTogether([Spacer(1, 4), img_flow, cap_flow, Spacer(1, 4)]))
                    continue

                if text.startswith("```"):
                    code_lines = text.strip('`').replace('text\n', '')
                    c_par = Paragraph(f"<font face='Courier' size=7.5>{code_lines.replace(' ', '&nbsp;').replace(chr(10), '<br/>')}</font>", code_style)
                    c_tbl = Table([[c_par]], colWidths=[content_width])
                    c_tbl.setStyle(TableStyle([
                        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F9FAFB')),
                        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#E5E7EB')),
                        ('TOPPADDING', (0,0), (-1,-1), 5),
                        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
                        ('LEFTPADDING', (0,0), (-1,-1), 8),
                        ('RIGHTPADDING', (0,0), (-1,-1), 8),
                    ]))
                    story.append(Spacer(1, 4))
                    story.append(c_tbl)
                    story.append(Spacer(1, 6))
                    continue

                story.append(Paragraph(text, body_style))

            # Table in Section
            if 'table' in sec:
                tbl_info = sec['table']
                story.append(Spacer(1, 4))
                story.append(Paragraph(tbl_info['title'], table_title_style))

                headers = tbl_info['headers']
                rows = tbl_info['rows']
                col_count = len(headers)

                # Determine dynamic column widths to fit content_width exactly
                if col_count == 4:
                    col_widths = [content_width * 0.22, content_width * 0.26, content_width * 0.26, content_width * 0.26]
                elif col_count == 5:
                    col_widths = [content_width * 0.20, content_width * 0.22, content_width * 0.18, content_width * 0.24, content_width * 0.16]
                elif col_count == 6:
                    # e.g., Table 6.1 (26 Test Cases)
                    col_widths = [content_width * 0.10, content_width * 0.24, content_width * 0.24, content_width * 0.22, content_width * 0.12, content_width * 0.08]
                else:
                    col_widths = [content_width / col_count] * col_count

                tbl_data = []
                # Header
                hdr_row = [Paragraph(f"<b>{h}</b>", tbl_header_style) for h in headers]
                tbl_data.append(hdr_row)

                # Rows
                for row_idx, r_vals in enumerate(rows):
                    row_cells = []
                    for c_idx, val in enumerate(r_vals):
                        val_str = str(val)
                        if val_str == "PASS":
                            c_p = Paragraph("<font color='#059669'><b>PASS</b></font>", tbl_cell_center)
                        elif val_str == "Healthy":
                            c_p = Paragraph("<font color='#059669'><b>Healthy</b></font>", tbl_cell_style)
                        elif val_str == "Low":
                            c_p = Paragraph("<font color='#D97706'><b>Low</b></font>", tbl_cell_style)
                        elif val_str in ["Critical", "out_of_stock"]:
                            c_p = Paragraph("<font color='#DC2626'><b>" + val_str + "</b></font>", tbl_cell_style)
                        else:
                            c_p = Paragraph(val_str, tbl_cell_style)
                        row_cells.append(c_p)
                    tbl_data.append(row_cells)

                grid_tbl = Table(tbl_data, colWidths=col_widths, repeatRows=1)
                t_style = [
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#064E3B')), # Deep green header
                    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                    ('TOPPADDING', (0,0), (-1,-1), 3.5),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 3.5),
                    ('LEFTPADDING', (0,0), (-1,-1), 4),
                    ('RIGHTPADDING', (0,0), (-1,-1), 4),
                    ('GRID', (0,0), (-1,-1), 0.4, colors.HexColor('#D1D5DB')),
                ]
                # Alternating row colors
                for r_i in range(1, len(tbl_data)):
                    if r_i % 2 == 0:
                        t_style.append(('BACKGROUND', (0, r_i), (-1, r_i), colors.HexColor('#F9FAFB')))

                grid_tbl.setStyle(TableStyle(t_style))
                story.append(grid_tbl)
                story.append(Spacer(1, 8))

        story.append(PageBreak())

    # ==========================================================================
    # 7. REFERENCES / BIBLIOGRAPHY
    # ==========================================================================
    story.append(Paragraph("<b>REFERENCES / BIBLIOGRAPHY</b>", chap_title_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#064E3B'), spaceAfter=12))

    ref_data = []
    for i, ref in enumerate(rc.REFERENCES):
        ref_data.append([
            Paragraph(f"<b>[{i+1}]</b>", tbl_cell_center),
            Paragraph(ref, ParagraphStyle('RefTxt', parent=body_style, fontSize=10, leading=14))
        ])
    ref_tbl = Table(ref_data, colWidths=[content_width * 0.08, content_width * 0.92])
    ref_tbl.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 2),
        ('RIGHTPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(ref_tbl)
    story.append(PageBreak())

    # ==========================================================================
    # 8. APPENDICES A THROUGH E
    # ==========================================================================
    story.append(Paragraph("<b>APPENDICES</b>", chap_title_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#064E3B'), spaceAfter=12))

    for app in rc.APPENDICES:
        story.append(Paragraph(f"<b>Appendix {app['id']}: {app['title']}</b>", sec_title_style))
        story.append(Paragraph(app['description'], body_style))
        story.append(Spacer(1, 4))

        if app['id'] == 'A':
            app_a_data = []
            for fid, ftitle in rc.FIGURES_LIST[7:]:
                app_a_data.append([
                    Paragraph(f"<b>{fid}</b>", tbl_cell_style),
                    Paragraph(ftitle, tbl_cell_style)
                ])
            app_a_tbl = Table(app_a_data, colWidths=[content_width * 0.22, content_width * 0.78])
            app_a_tbl.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('TOPPADDING', (0,0), (-1,-1), 2.5),
                ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
                ('LINEBELOW', (0,0), (-1,-1), 0.3, colors.HexColor('#F3F4F6')),
            ]))
            story.append(app_a_tbl)
            story.append(Spacer(1, 8))

        elif app['id'] == 'B':
            for code_block in rc.APPENDIX_B_CODE:
                story.append(Paragraph(f"<b>Listing: {code_block['filename']}</b>", table_title_style))
                c_par = Paragraph(f"<font face='Courier' size=7.0>{code_block['code'].replace(' ', '&nbsp;').replace(chr(10), '<br/>')}</font>", code_style)
                c_tbl = Table([[c_par]], colWidths=[content_width])
                c_tbl.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F9FAFB')),
                    ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#E5E7EB')),
                    ('TOPPADDING', (0,0), (-1,-1), 4),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                    ('LEFTPADDING', (0,0), (-1,-1), 6),
                    ('RIGHTPADDING', (0,0), (-1,-1), 6),
                ]))
                story.append(c_tbl)
                story.append(Spacer(1, 6))

        elif app['id'] == 'C':
            for dt in rc.DATA_DICTIONARY_TABLES:
                story.append(Paragraph(dt['title'], table_title_style))
                dt_hdr = [Paragraph(f"<b>{h}</b>", tbl_header_style) for h in dt['headers']]
                dt_data = [dt_hdr]
                for r_vals in dt['rows']:
                    dt_data.append([Paragraph(str(v), tbl_cell_style) for v in r_vals])
                dt_col_w = [content_width * 0.18, content_width * 0.16, content_width * 0.16, content_width * 0.12, content_width * 0.14, content_width * 0.24]
                dt_tbl = Table(dt_data, colWidths=dt_col_w, repeatRows=1)
                dt_style = [
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#064E3B')),
                    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                    ('TOPPADDING', (0,0), (-1,-1), 3),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 3),
                    ('LEFTPADDING', (0,0), (-1,-1), 3),
                    ('RIGHTPADDING', (0,0), (-1,-1), 3),
                    ('GRID', (0,0), (-1,-1), 0.4, colors.HexColor('#D1D5DB')),
                ]
                for r_i in range(1, len(dt_data)):
                    if r_i % 2 == 0:
                        dt_style.append(('BACKGROUND', (0, r_i), (-1, r_i), colors.HexColor('#F9FAFB')))
                dt_tbl.setStyle(TableStyle(dt_style))
                story.append(dt_tbl)
                story.append(Spacer(1, 8))

        elif app['id'] == 'D':
            d_lines = rc.APPENDIX_D_TEXT.replace(' ', '&nbsp;').replace('\n', '<br/>')
            story.append(Paragraph(f"<font face='Courier' size=8.0>{d_lines}</font>", code_style))
            story.append(Spacer(1, 8))

        elif app['id'] == 'E':
            for line in rc.APPENDIX_E_TEXT.split('\n'):
                if line.strip().startswith(('1.', '2.', '3.')):
                    story.append(Paragraph(f"<b>{line}</b>", sec_title_style))
                else:
                    story.append(Paragraph(line, body_style))
            story.append(Spacer(1, 8))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF Document successfully saved to {pdf_filename} (Size: {os.path.getsize(pdf_filename)} bytes)")

if __name__ == '__main__':
    build_pdf()
