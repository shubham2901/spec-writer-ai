"""
Export utilities for PRD spec to Markdown and PDF formats.
"""

from typing import Dict, Any, Optional
from datetime import datetime
from io import BytesIO

from src.knowledge_base import PRD_COMPONENT_NAMES


def export_to_markdown(
    components: Dict[str, Optional[str]],
    detailed_components: Optional[Dict[str, Dict[str, Any]]] = None,
    title: str = "Product Requirements Document"
) -> str:
    """
    Export components to a clean Markdown document.
    Uses detailed_components if available, otherwise uses raw components.
    """
    lines = []
    
    lines.append(f"# {title}")
    lines.append("")
    lines.append(f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}*")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    for name in PRD_COMPONENT_NAMES:
        if detailed_components and name in detailed_components:
            detail = detailed_components[name]
            text = detail.get("text") or components.get(name)
            questions = detail.get("questions", [])
        else:
            text = components.get(name)
            questions = []
        
        lines.append(f"## {name}")
        lines.append("")
        
        if text:
            lines.append(text)
        else:
            lines.append("*No information provided.*")
        
        lines.append("")
        
        if questions:
            lines.append("### Recommended Next Steps")
            lines.append("")
            for i, q in enumerate(questions, 1):
                lines.append(f"{i}. {q}")
            lines.append("")
        
        lines.append("---")
        lines.append("")
    
    return "\n".join(lines)


def export_to_pdf(
    components: Dict[str, Optional[str]],
    detailed_components: Optional[Dict[str, Dict[str, Any]]] = None,
    title: str = "Product Requirements Document"
) -> bytes:
    """
    Export components to a PDF document.
    Uses detailed_components if available, otherwise uses raw components.
    Returns PDF as bytes.
    """
    try:
        from fpdf import FPDF
    except ImportError:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.units import inch
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.75*inch, bottomMargin=0.75*inch)
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=20,
            spaceAfter=20,
        )
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceBefore=15,
            spaceAfter=8,
            textColor='#6b21a8',
        )
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['Normal'],
            fontSize=11,
            leading=16,
        )
        question_style = ParagraphStyle(
            'Question',
            parent=styles['Normal'],
            fontSize=10,
            leftIndent=20,
            textColor='#4b5563',
        )
        
        story = []
        
        story.append(Paragraph(title, title_style))
        story.append(Paragraph(f"<i>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}</i>", styles['Normal']))
        story.append(Spacer(1, 20))
        
        for name in PRD_COMPONENT_NAMES:
            if detailed_components and name in detailed_components:
                detail = detailed_components[name]
                text = detail.get("text") or components.get(name)
                questions = detail.get("questions", [])
            else:
                text = components.get(name)
                questions = []
            
            story.append(Paragraph(name, heading_style))
            
            if text:
                clean_text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                story.append(Paragraph(clean_text, body_style))
            else:
                story.append(Paragraph("<i>No information provided.</i>", body_style))
            
            if questions:
                story.append(Spacer(1, 8))
                story.append(Paragraph("<b>Recommended Next Steps:</b>", question_style))
                for i, q in enumerate(questions, 1):
                    clean_q = q.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                    story.append(Paragraph(f"{i}. {clean_q}", question_style))
            
            story.append(Spacer(1, 15))
        
        doc.build(story)
        buffer.seek(0)
        return buffer.read()
    
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 15, title, ln=True, align="C")
    
    pdf.set_font("Helvetica", "I", 10)
    pdf.cell(0, 8, f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align="C")
    pdf.ln(10)
    
    for name in PRD_COMPONENT_NAMES:
        if detailed_components and name in detailed_components:
            detail = detailed_components[name]
            text = detail.get("text") or components.get(name)
            questions = detail.get("questions", [])
        else:
            text = components.get(name)
            questions = []
        
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(107, 33, 168)
        pdf.cell(0, 10, name, ln=True)
        
        pdf.set_font("Helvetica", "", 11)
        pdf.set_text_color(0, 0, 0)
        
        if text:
            pdf.multi_cell(0, 6, text)
        else:
            pdf.set_font("Helvetica", "I", 11)
            pdf.cell(0, 6, "No information provided.", ln=True)
        
        if questions:
            pdf.ln(3)
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(75, 85, 99)
            pdf.cell(0, 6, "Recommended Next Steps:", ln=True)
            pdf.set_font("Helvetica", "", 10)
            for i, q in enumerate(questions, 1):
                pdf.multi_cell(0, 5, f"  {i}. {q}")
        
        pdf.set_text_color(0, 0, 0)
        pdf.ln(8)
    
    return pdf.output(dest='S').encode('latin-1')
