from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
import pandas as pd
import re

def generate_pdf(selected_tracks, selected_components, scan_results_df):
    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=A4)
    story = []
    styles = getSampleStyleSheet()

    link_style = ParagraphStyle(
        name='LinkStyle',
        parent=styles['Normal'],
        textColor=colors.blue,
        underline=True
    )

    current_date = datetime.now().strftime("%Y-%m-%d %H:%M")
    story.append(Paragraph("ATW Scan Report", styles['Title']))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Date: {current_date}", styles['Normal']))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Scan Results:", styles['Heading2']))

    if scan_results_df is not None and not scan_results_df.empty:
        df = scan_results_df.copy()

        def extract_url_and_format(cell):
            if isinstance(cell, str) and '<a href="' in cell:
                match = re.search(r'<a href="([^"]+)"', cell)
                if match:
                    url = match.group(1)
                    return f'<link href="{url}">ATW Link</link>'
            return cell

        df = df.map(extract_url_and_format)

        table_data = [list(df.columns)] + df.values.tolist()

        table_data_paragraphs = []
        for row in table_data:
            new_row = []
            for cell in row:
                if isinstance(cell, str) and '<link' in cell:
                    new_row.append(Paragraph(cell, link_style))
                else:
                    new_row.append(Paragraph(str(cell), styles['Normal']))
            table_data_paragraphs.append(new_row)

        table = Table(table_data_paragraphs, hAlign='LEFT')

        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ]))

        story.append(table)
    else:
        story.append(Paragraph("No errors found in the selected tracks and components.", styles['Heading3']))

    story.append(Paragraph("Selected Support Tracks:", styles['Heading2']))
    if selected_tracks:
        track_list = ListFlowable(
            [ListItem(Paragraph(track, styles['Normal'])) for track in selected_tracks],
            bulletType='bullet'
        )
        story.append(track_list)
    else:
        story.append(Paragraph("No tracks selected.", styles['Normal']))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Selected Components:", styles['Heading2']))
    if selected_components:
        component_list = ListFlowable(
            [ListItem(Paragraph(component, styles['Normal'])) for component in selected_components],
            bulletType='bullet'
        )
        story.append(component_list)
    else:
        story.append(Paragraph("No components selected.", styles['Normal']))
    story.append(Spacer(1, 12))


    doc.build(story)
    pdf_buffer.seek(0)
    return pdf_buffer, f"ATW_Scan_Results_{current_date}.pdf"
