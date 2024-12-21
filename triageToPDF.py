import json
import tempfile
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_CENTER

# xsoar imports
from typing import Dict, Any
import traceback

def generate_pdf_report(data, output_file):
    doc = SimpleDocTemplate(
        output_file,
        pagesize=A4,
        rightMargin=20*mm,
        leftMargin=20*mm,
        topMargin=20*mm,
        bottomMargin=20*mm
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Heading1Center', parent=styles['Heading1'], alignment=TA_CENTER))
    styles.add(ParagraphStyle(name='Heading2Bold', parent=styles['Heading2'], textColor=colors.darkblue))
    styles.add(ParagraphStyle(name='BodyTextIndented', parent=styles['BodyText'], leftIndent=10))

    elements = []

    # extract main sections
    sample = data.get('sample', {})
    analysis = data.get('analysis', {})
    targets = data.get('targets', [])
    extracted = data.get('extracted', [])

    # title page
    elements.append(Paragraph("Hatching Triage Sandbox Report", styles['Heading1Center']))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"Sample ID: {sample.get('id', 'N/A')}", styles['Normal']))
    elements.append(Paragraph(f"Target File: {sample.get('target', 'N/A')}", styles['Normal']))
    elements.append(Paragraph(f"Overall Score: {analysis.get('score', 'N/A')}", styles['Normal']))
    elements.append(Spacer(1, 24))

    # sample metadata
    elements.append(Paragraph("Sample Metadata", styles['Heading2Bold']))
    elements.append(Spacer(1, 6))
    metadata_table_data = [
        ['MD5', sample.get('md5', 'N/A')],
        ['SHA1', sample.get('sha1', 'N/A')],
        ['SHA256', sample.get('sha256', 'N/A')],
        ['SHA512', sample.get('sha512', 'N/A')],
        ['Size (bytes)', str(sample.get('size', 'N/A'))]
    ]
    metadata_table = Table(metadata_table_data, colWidths=[70*mm, 100*mm])
    metadata_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('BOX', (0,0), (-1,-1), 0.25, colors.black),
        ('INNERGRID', (0,0), (-1,-1), 0.25, colors.black),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    elements.append(metadata_table)
    elements.append(Spacer(1, 12))

    # targets
    for idx, t in enumerate(targets, start=1):
        elements.append(Paragraph(f"Target #{idx}", styles['Heading2Bold']))
        elements.append(Spacer(1, 6))

        target_table_data = [
            ['Target Name', t.get('target', 'N/A')],
            ['Score', str(t.get('score', 'N/A'))],
            ['Size', str(t.get('size', 'N/A'))],
            ['MD5', t.get('md5', 'N/A')],
            ['SHA1', t.get('sha1', 'N/A')],
            ['SHA256', t.get('sha256', 'N/A')]
        ]
        target_table = Table(target_table_data, colWidths=[70*mm, 100*mm])
        target_table.setStyle(TableStyle([
            ('BOX', (0,0), (-1,-1), 0.25, colors.black),
            ('INNERGRID', (0,0), (-1,-1), 0.25, colors.black),
        ]))
        elements.append(target_table)
        elements.append(Spacer(1, 12))

        # tags
        tags = t.get('tags', [])
        if tags:
            elements.append(Paragraph("Tags:", styles['BodyText']))
            elements.append(Paragraph(", ".join(tags), styles['BodyTextIndented']))
            elements.append(Spacer(1, 12))

        # family
        family = t.get('family', [])
        if family:
            elements.append(Paragraph("Family:", styles['BodyText']))
            elements.append(Paragraph(", ".join(family), styles['BodyTextIndented']))
            elements.append(Spacer(1, 12))

        # signatures
        signatures = t.get('signatures', [])
        if signatures:
            elements.append(Paragraph("Signatures:", styles['Heading2Bold']))
            elements.append(Spacer(1, 6))
            for sig in signatures:
                sig_name = sig.get('name', 'Unknown')
                sig_desc = sig.get('desc', 'No description.')
                sig_score = sig.get('score', 'N/A')
                sig_tags = sig.get('tags', [])

                elements.append(Paragraph(f"Signature: {sig_name} (Score: {sig_score})", styles['BodyText']))
                elements.append(Paragraph(f"Description: {sig_desc}", styles['BodyTextIndented']))
                if sig_tags:
                    elements.append(Paragraph("Tags: " + ", ".join(sig_tags), styles['BodyTextIndented']))
                elements.append(Spacer(1, 12))

        elements.append(PageBreak())

    # extracted configs / payloads
    if extracted:
        elements.append(Paragraph("Extracted Artifacts & Configurations", styles['Heading2Bold']))
        elements.append(Spacer(1, 12))

        for item in extracted:
            tasks = item.get('tasks', [])
            dumped_file = item.get('dumped_file', 'N/A')
            resource = item.get('resource', 'N/A')
            config = item.get('config', {})
            family = config.get('family', 'N/A')
            c2_servers = config.get('c2', [])
            version = config.get('version', 'N/A')
            botnet = config.get('botnet', 'N/A')
            keys = config.get('keys', [])

            elements.append(Paragraph(f"Dumped File: {dumped_file}", styles['BodyText']))
            elements.append(Paragraph(f"Resource: {resource}", styles['BodyTextIndented']))
            elements.append(Paragraph(f"Family: {family}", styles['BodyTextIndented']))
            elements.append(Paragraph(f"Version: {version}", styles['BodyTextIndented']))
            elements.append(Paragraph(f"Botnet: {botnet}", styles['BodyTextIndented']))

            if c2_servers:
                elements.append(Paragraph("C2 Servers:", styles['BodyText']))
                for c2 in c2_servers:
                    elements.append(Paragraph(c2, styles['BodyTextIndented']))

            if keys:
                elements.append(Paragraph("Keys:", styles['BodyText']))
                for keyobj in keys:
                    elements.append(Paragraph(f"Type: {keyobj.get('kind', 'N/A')} | Key: {keyobj.get('value', 'N/A')}", styles['BodyTextIndented']))

            elements.append(Spacer(1, 12))

    doc.build(elements)


def main():
    args = demisto.args()
    triage_json = args.get('triage_json')
    entry_id = args.get('entry_id')

    # load the JSON data
    data = {}
    if triage_json:
        # if JSON is provided directly as a string
        data = json.loads(triage_json)
    elif entry_id:
        # if an entry_id is provided, fetch the file and load JSON
        file_info = demisto.getFilePath(entry_id)
        file_path = file_info.get('path')
        with open(file_path, 'r') as f:
            data = json.load(f)
    else:
        return_error("No triage JSON data provided. Please supply 'triage_json' or 'entry_id'.")

    # create a temporary PDF file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
        pdf_path = tmp_pdf.name

    # generate the PDF report
    generate_pdf_report(data, pdf_path)

    # read the PDF and return as a file result to the war room
    with open(pdf_path, 'rb') as f:
        file_data = f.read()

    # clean up temp file after reading
    os.remove(pdf_path)

    return_results(fileResult("triage_report.pdf", file_data, file_type=9))  # file_type=9 for PDF

if __name__ in ("__main__", "__builtin__", "builtins"):
    main()