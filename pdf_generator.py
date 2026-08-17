import io
import html
import re
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.platypus.flowables import HRFlowable


def clean_text_for_reportlab(text: str) -> str:
    if not text:
        return ""
    
    # 1. Unescape existing HTML entities
    text = html.unescape(text)

    # 2. Extract and temporarily preserve Markdown bold & italic text
    text = re.sub(r'\*\*(.*?)\*\*', r'___BOLD_\1_BOLD___', text)
    text = re.sub(r'\*(.*?)\*', r'___ITALIC_\1_ITALIC___', text)

    # 3. Strip ALL raw HTML / XML tags from text
    text = re.sub(r'<[^>]+>', '', text)

    # 4. Escape remaining XML reserved characters (&, <, >)
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    # 5. Restore bold & italic tags in ReportLab-safe XML format
    text = re.sub(r'___BOLD_(.*?)_BOLD___', r'<b>\1</b>', text)
    text = re.sub(r'___ITALIC_(.*?)_ITALIC___', r'<i>\1</i>', text)
    
    return text


def generate_pdf_report(title: str, content: str) -> bytes:
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

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

    date_str = datetime.now().strftime("%B %d, %Y")
    formatted_title = clean_text_for_reportlab(title.title())
    
    story.append(Paragraph(f"<b>{formatted_title}</b>", doc_title_style))
    story.append(Paragraph(f"<b>Executive Research Brief</b> &bull; Generated on {date_str}", doc_meta_style))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#2563EB"), spaceAfter=16))

    lines = content.split('\n')
    for line in lines:
        line_str = line.strip()
        if not line_str:
            continue

        formatted = clean_text_for_reportlab(line_str)

        if formatted.startswith('# '):
            story.append(Paragraph(formatted[2:], doc_title_style))
        elif formatted.startswith('## ') or formatted.startswith('### '):
            clean_head = re.sub(r'^#+\s*', '', formatted)
            story.append(Paragraph(clean_head, h2_style))
        elif formatted.startswith('* ') or formatted.startswith('- ') or re.match(r'^\d+\.\s', formatted):
            clean_bullet = re.sub(r'^(\*|-|\d+\.)\s*', '', formatted)
            story.append(Paragraph(f"&bull; {clean_bullet}", bullet_style))
        elif formatted.startswith('&gt; '):
            clean_quote = formatted[5:]
            story.append(Paragraph(f"<i>{clean_quote}</i>", bullet_style))
        else:
            story.append(Paragraph(formatted, body_style))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes