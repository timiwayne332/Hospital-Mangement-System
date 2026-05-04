"""
PDF generation utility for discharge summaries and reports
"""
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from datetime import datetime
import os


def generate_discharge_summary_pdf(discharge_summary, patient, doctor, admission, output_path=None):
    """
    Generate a discharge summary PDF
    
    Args:
        discharge_summary: DischargeSummary object
        patient: Patient object
        doctor: Doctor object
        admission: Admission object
        output_path: Path to save PDF (if None, uses app uploads folder)
    
    Returns:
        str: Path to generated PDF file
    """
    if not output_path:
        from flask import current_app
        output_folder = current_app.config['UPLOAD_FOLDER']
        os.makedirs(output_folder, exist_ok=True)
        filename = f"discharge_{discharge_summary.id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
        output_path = os.path.join(output_folder, filename)
    
    # Create PDF
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1f4788'),
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#1f4788'),
        spaceAfter=8,
        spaceBefore=8,
        fontName='Helvetica-Bold'
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6,
        alignment=TA_JUSTIFY
    )
    
    # Header
    story.append(Paragraph("HOSPITAL DISCHARGE SUMMARY", title_style))
    story.append(Spacer(1, 0.2 * inch))
    
    # Patient Information Section
    story.append(Paragraph("PATIENT INFORMATION", heading_style))
    patient_data = [
        ['Full Name:', f"{patient.user.get_full_name()}"],
        ['MRN:', patient.patient_id],
        ['Date of Birth:', str(patient.date_of_birth) if patient.date_of_birth else 'N/A'],
        ['Gender:', patient.gender or 'N/A'],
        ['Blood Group:', patient.blood_group or 'N/A'],
        ['Contact:', patient.user.phone or 'N/A'],
    ]
    
    patient_table = Table(patient_data, colWidths=[1.5*inch, 4.5*inch])
    patient_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica', 10),
        ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 10),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('RIGHTPADDING', (0, 0), (0, -1), 10),
    ]))
    story.append(patient_table)
    story.append(Spacer(1, 0.15 * inch))
    
    # Admission Information
    story.append(Paragraph("ADMISSION DETAILS", heading_style))
    admission_data = [
        ['Admission Date:', admission.admission_date.strftime('%d %b %Y, %H:%M') if admission.admission_date else 'N/A'],
        ['Discharge Date:', discharge_summary.discharge_date.strftime('%d %b %Y, %H:%M') if discharge_summary.discharge_date else 'N/A'],
        ['Reason for Admission:', admission.reason or 'N/A'],
        ['Attending Doctor:', f"Dr. {doctor.user.get_full_name()}"],
        ['Bed Number:', admission.bed.bed_number if admission.bed else 'N/A'],
    ]
    
    admission_table = Table(admission_data, colWidths=[1.5*inch, 4.5*inch])
    admission_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica', 10),
        ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 10),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('RIGHTPADDING', (0, 0), (0, -1), 10),
    ]))
    story.append(admission_table)
    story.append(Spacer(1, 0.15 * inch))
    
    # Clinical Information
    story.append(Paragraph("CLINICAL INFORMATION", heading_style))
    
    story.append(Paragraph("Chief Complaint:", styles['Normal']))
    story.append(Paragraph(discharge_summary.chief_complaint or 'N/A', normal_style))
    story.append(Spacer(1, 0.1 * inch))
    
    story.append(Paragraph("Diagnosis:", styles['Normal']))
    story.append(Paragraph(discharge_summary.diagnosis or 'N/A', normal_style))
    story.append(Spacer(1, 0.1 * inch))
    
    story.append(Paragraph("Treatment Given:", styles['Normal']))
    story.append(Paragraph(discharge_summary.treatment_given or 'N/A', normal_style))
    story.append(Spacer(1, 0.1 * inch))
    
    if discharge_summary.procedures_performed:
        story.append(Paragraph("Procedures Performed:", styles['Normal']))
        story.append(Paragraph(discharge_summary.procedures_performed, normal_style))
        story.append(Spacer(1, 0.1 * inch))
    
    story.append(Paragraph("Final Status:", styles['Normal']))
    story.append(Paragraph(discharge_summary.final_status or 'Stable', normal_style))
    story.append(Spacer(1, 0.15 * inch))
    
    # Discharge Instructions
    story.append(Paragraph("DISCHARGE ADVICE & INSTRUCTIONS", heading_style))
    
    if discharge_summary.discharge_advice:
        story.append(Paragraph(discharge_summary.discharge_advice, normal_style))
    
    if discharge_summary.medications_on_discharge:
        story.append(Spacer(1, 0.1 * inch))
        story.append(Paragraph("Medications on Discharge:", styles['Normal']))
        story.append(Paragraph(discharge_summary.medications_on_discharge, normal_style))
    
    if discharge_summary.follow_up_instructions:
        story.append(Spacer(1, 0.1 * inch))
        story.append(Paragraph("Follow-up Instructions:", styles['Normal']))
        story.append(Paragraph(discharge_summary.follow_up_instructions, normal_style))
    
    story.append(Spacer(1, 0.3 * inch))
    
    # Signature Section
    story.append(Paragraph("Doctor's Signature", heading_style))
    signature_data = [
        ['Signature:', '_' * 30],
        ['Name:', f"Dr. {doctor.user.get_full_name()}"],
        ['Date:', discharge_summary.discharge_date.strftime('%d %b %Y') if discharge_summary.discharge_date else ''],
    ]
    
    signature_table = Table(signature_data, colWidths=[1.5*inch, 4.5*inch])
    signature_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica', 10),
        ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 10),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    story.append(signature_table)
    
    # Build PDF
    doc.build(story)
    return output_path


def generate_prescription_pdf(prescription, output_path=None):
    """
    Generate a prescription PDF
    
    Args:
        prescription: Prescription object
        output_path: Path to save PDF
    
    Returns:
        str: Path to generated PDF
    """
    if not output_path:
        from flask import current_app
        output_folder = current_app.config['UPLOAD_FOLDER']
        os.makedirs(output_folder, exist_ok=True)
        filename = f"prescription_{prescription.id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
        output_path = os.path.join(output_folder, filename)
    
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#1f4788'),
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading3'],
        fontSize=11,
        textColor=colors.HexColor('#1f4788'),
        spaceAfter=8,
        fontName='Helvetica-Bold'
    )
    
    # Header
    story.append(Paragraph("PRESCRIPTION FORM", title_style))
    story.append(Spacer(1, 0.2 * inch))
    
    # Patient Info
    story.append(Paragraph("PATIENT INFORMATION", heading_style))
    patient_data = [
        ['Name:', prescription.patient.user.get_full_name()],
        ['MRN:', prescription.patient.patient_id],
        ['Date of Prescription:', prescription.prescription_date.strftime('%d %b %Y')],
    ]
    patient_table = Table(patient_data, colWidths=[1.5*inch, 4.5*inch])
    patient_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica', 10),
        ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 10),
    ]))
    story.append(patient_table)
    story.append(Spacer(1, 0.2 * inch))
    
    # Medications Section
    story.append(Paragraph("PRESCRIBED MEDICATIONS", heading_style))
    
    med_data = [['Medicine', 'Dosage', 'Frequency', 'Route', 'Quantity']]
    for item in prescription.prescription_items:
        med_data.append([
            item.medicine.name,
            item.dosage or '',
            item.frequency,
            item.route or '',
            f"{item.quantity} {item.unit}"
        ])
    
    med_table = Table(med_data, colWidths=[1.8*inch, 1.2*inch, 1.2*inch, 0.8*inch, 0.8*inch])
    med_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
    ]))
    story.append(med_table)
    story.append(Spacer(1, 0.2 * inch))
    
    # Instructions
    if prescription.instructions:
        story.append(Paragraph("SPECIAL INSTRUCTIONS", heading_style))
        story.append(Paragraph(prescription.instructions, styles['Normal']))
    
    story.append(Spacer(1, 0.3 * inch))
    
    # Doctor Signature
    story.append(Paragraph("Prescribed by:", heading_style))
    doctor_data = [
        ['Signature:', '_' * 30],
        ['Name:', f"Dr. {prescription.doctor.user.get_full_name()}"],
        ['Specialization:', prescription.doctor.specialization],
    ]
    doctor_table = Table(doctor_data, colWidths=[1.5*inch, 4.5*inch])
    doctor_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica', 10),
        ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 10),
    ]))
    story.append(doctor_table)
    
    doc.build(story)
    return output_path
