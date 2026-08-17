import io
import re
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.platypus.flowables import HRFlowable


def generate_pdf_report(title: str, content: str) -> bytes:
    buffer = io.BytesIO()

    # Document setup (0.75-inch margins)
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # 1. Center-Aligned Header Styles
    doc_title_style = ParagraphStyle(
        'ExecutiveTitle',
        parent=styles['Heading1'],
        fontSize=22,
        leading=26,
        textColor=colors.HexColor('#0F172A'),
        alignment=TA_CENTER,
        spaceAfter=6
    )

    doc_meta_style = ParagraphStyle(
        'ExecutiveMeta',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#64748B'),
        alignment=TA_CENTER,
        spaceAfter=14
    )

    # 2. Body Section Styles
    h2_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontSize=13,
        leading=17,
        textColor=colors.HexColor('#1E3A8A'),
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'BodyText',
        parent=styles['Normal'],
        fontSize=10,
        leading=15,
        textColor=colors.HexColor('#334155'),
        alignment=TA_LEFT,
        spaceAfter=8
    )

    bullet_style = ParagraphStyle(
        'BulletText',
        parent=body_style,
        leftIndent=14,
        spaceAfter=4
    )

    story = []

    # 3. Centered Header Block
    date_str = datetime.now().strftime("%B %d, %Y")
    
    # Auto-titlecase the main title for presentation
    formatted_title = title.title()
    
    story.append(Paragraph(f"<b>{formatted_title}</b>", doc_title_style))
    story.append(Paragraph(f"<b>Executive Research Brief</b> • Generated on {date_str}", doc_meta_style))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#2563EB"), spaceAfter=16))

    # 4. Markdown Parsing
    lines = content.split('\n')
    for line in lines:
        line_str = line.strip()
        if not line_str:
            continue

        # Format bold **text** and italic *text*
        formatted = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line_str)
        formatted = re.sub(r'\*(.*?)\*', r'<i>\1</i>', formatted)

        # Headings
        if formatted.startswith('# '):
            story.append(Paragraph(formatted[2:], doc_title_style))
        elif formatted.startswith('## ') or formatted.startswith('### '):
            clean_head = re.sub(r'^#+\s*', '', formatted)
            story.append(Paragraph(clean_head, h2_style))
        # Bullet Points
        elif formatted.startswith('* ') or formatted.startswith('- ') or re.match(r'^\d+\.\s', formatted):
            clean_bullet = re.sub(r'^(\*|-|\d+\.)\s*', '', formatted)
            story.append(Paragraph(f"• {clean_bullet}", bullet_style))
        # Paragraphs
        else:
            story.append(Paragraph(formatted, body_style))

    # Build PDF
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes