from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
from datetime import date
from typing import Optional


def create_invoice_pdf(
    contract_number: str,
    tenant_name: str,
    tenant_address: str,
    premise_number: str,
    amount: float,
    period_start: date,
    period_end: date,
    company_name: str,
    company_address: str,
    company_bank: str,
    company_account: str,
    invoice_number: str,
    invoice_date: date
) -> BytesIO:
    """
    Generate invoice PDF

    Returns:
        BytesIO buffer with PDF content
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    story = []

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=30,
        alignment=1  # Center
    )

    # Title
    story.append(Paragraph(f"СЧЕТ НА ОПЛАТУ №{invoice_number}", title_style))
    story.append(Paragraph(f"от {invoice_date.strftime('%d.%m.%Y')}", styles['Normal']))
    story.append(Spacer(1, 20))

    # Company info
    story.append(Paragraph("<b>Поставщик:</b>", styles['Heading2']))
    company_info = f"""
    {company_name}<br/>
    Адрес: {company_address}<br/>
    Банк: {company_bank}<br/>
    Счет: {company_account}
    """
    story.append(Paragraph(company_info, styles['Normal']))
    story.append(Spacer(1, 15))

    # Tenant info
    story.append(Paragraph("<b>Плательщик:</b>", styles['Heading2']))
    tenant_info = f"""
    {tenant_name}<br/>
    Адрес: {tenant_address}
    """
    story.append(Paragraph(tenant_info, styles['Normal']))
    story.append(Spacer(1, 15))

    # Payment details table
    story.append(Paragraph("<b>Детали платежа:</b>", styles['Heading2']))

    data = [
        ['Наименование услуги', 'Период', 'Сумма (тенге)'],
        [
            f'Аренда помещения №{premise_number}\n(Договор №{contract_number})',
            f'{period_start.strftime("%d.%m.%Y")} - {period_end.strftime("%d.%m.%Y")}',
            f'{amount:,.2f}'
        ],
        ['', '<b>ИТОГО:</b>', f'<b>{amount:,.2f}</b>']
    ]

    table = Table(data, colWidths=[8*cm, 5*cm, 4*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))

    story.append(table)
    story.append(Spacer(1, 30))

    # Footer
    story.append(Paragraph(
        "Оплату произвести в срок, указанный в договоре.",
        styles['Normal']
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer


def create_contract_pdf(
    contract_number: str,
    contract_date: date,
    company_name: str,
    company_director: str,
    tenant_name: str,
    tenant_director: str,
    premise_number: str,
    premise_area: float,
    premise_address: str,
    start_date: date,
    end_date: date,
    monthly_rent: float,
    deposit_amount: Optional[float],
    special_conditions: Optional[str]
) -> BytesIO:
    """
    Generate contract PDF

    Returns:
        BytesIO buffer with PDF content
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2*cm)
    story = []

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=20,
        alignment=1  # Center
    )

    # Title
    story.append(Paragraph(f"ДОГОВОР АРЕНДЫ №{contract_number}", title_style))
    story.append(Paragraph(f"г. Алматы, {contract_date.strftime('%d.%m.%Y')}", styles['Normal']))
    story.append(Spacer(1, 20))

    # Parties
    parties = f"""
    <b>{company_name}</b>, именуемое в дальнейшем "Арендодатель",
    в лице {company_director}, действующего на основании Устава, с одной стороны, и
    <b>{tenant_name}</b>, именуемое в дальнейшем "Арендатор",
    в лице {tenant_director}, действующего на основании Устава, с другой стороны,
    заключили настоящий Договор о нижеследующем:
    """
    story.append(Paragraph(parties, styles['Normal']))
    story.append(Spacer(1, 15))

    # 1. Subject
    story.append(Paragraph("<b>1. ПРЕДМЕТ ДОГОВОРА</b>", styles['Heading2']))
    subject = f"""
    1.1. Арендодатель предоставляет, а Арендатор принимает в аренду нежилое помещение
    №{premise_number}, общей площадью {premise_area} кв.м, расположенное по адресу: {premise_address}.
    """
    story.append(Paragraph(subject, styles['Normal']))
    story.append(Spacer(1, 10))

    # 2. Term
    story.append(Paragraph("<b>2. СРОК ДЕЙСТВИЯ ДОГОВОРА</b>", styles['Heading2']))
    term = f"""
    2.1. Настоящий Договор вступает в силу с {start_date.strftime('%d.%m.%Y')}
    и действует до {end_date.strftime('%d.%m.%Y')}.
    """
    story.append(Paragraph(term, styles['Normal']))
    story.append(Spacer(1, 10))

    # 3. Payment
    story.append(Paragraph("<b>3. АРЕНДНАЯ ПЛАТА</b>", styles['Heading2']))
    payment = f"""
    3.1. Размер ежемесячной арендной платы составляет {monthly_rent:,.2f} (тенге).<br/>
    """
    if deposit_amount:
        payment += f"3.2. Обеспечительный депозит составляет {deposit_amount:,.2f} (тенге).<br/>"

    payment += """
    3.3. Арендная плата вносится Арендатором ежемесячно, не позднее 1-го числа текущего месяца.<br/>
    3.4. При просрочке оплаты начисляется пеня в размере 0.1% от суммы задолженности за каждый день просрочки.
    """
    story.append(Paragraph(payment, styles['Normal']))
    story.append(Spacer(1, 10))

    # 4. Special conditions
    if special_conditions:
        story.append(Paragraph("<b>4. ОСОБЫЕ УСЛОВИЯ</b>", styles['Heading2']))
        story.append(Paragraph(special_conditions, styles['Normal']))
        story.append(Spacer(1, 10))

    # Signatures
    story.append(Spacer(1, 30))
    signatures = """
    <b>АРЕНДОДАТЕЛЬ:</b><br/>
    {company_name}<br/>
    ___________________ {company_director}<br/>
    <br/>
    <b>АРЕНДАТОР:</b><br/>
    {tenant_name}<br/>
    ___________________ {tenant_director}
    """.format(
        company_name=company_name,
        company_director=company_director,
        tenant_name=tenant_name,
        tenant_director=tenant_director
    )
    story.append(Paragraph(signatures, styles['Normal']))

    doc.build(story)
    buffer.seek(0)
    return buffer


def create_payment_act_pdf(
    contract_number: str,
    payment_number: str,
    payment_date: date,
    amount: float,
    period_start: date,
    period_end: date,
    company_name: str,
    tenant_name: str
) -> BytesIO:
    """
    Generate payment act PDF

    Returns:
        BytesIO buffer with PDF content
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    story = []

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=20,
        alignment=1
    )

    # Title
    story.append(Paragraph(f"АКТ ОБ ОКАЗАНИИ УСЛУГ №{payment_number}", title_style))
    story.append(Paragraph(f"к Договору №{contract_number}", styles['Normal']))
    story.append(Paragraph(f"от {payment_date.strftime('%d.%m.%Y')}", styles['Normal']))
    story.append(Spacer(1, 20))

    # Body
    body = f"""
    <b>Исполнитель:</b> {company_name}<br/>
    <b>Заказчик:</b> {tenant_name}<br/>
    <br/>
    Исполнитель оказал, а Заказчик принял следующие услуги:
    """
    story.append(Paragraph(body, styles['Normal']))
    story.append(Spacer(1, 15))

    # Services table
    data = [
        ['№', 'Наименование услуги', 'Период', 'Сумма (тенге)'],
        [
            '1',
            'Аренда нежилого помещения',
            f'{period_start.strftime("%d.%m.%Y")} - {period_end.strftime("%d.%m.%Y")}',
            f'{amount:,.2f}'
        ],
        ['', '', '<b>ИТОГО:</b>', f'<b>{amount:,.2f}</b>']
    ]

    table = Table(data, colWidths=[1*cm, 8*cm, 5*cm, 3*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))

    story.append(table)
    story.append(Spacer(1, 30))

    # Signatures
    signatures = f"""
    <b>ИСПОЛНИТЕЛЬ:</b><br/>
    {company_name}<br/>
    ___________________<br/>
    <br/>
    <b>ЗАКАЗЧИК:</b><br/>
    {tenant_name}<br/>
    ___________________
    """
    story.append(Paragraph(signatures, styles['Normal']))

    doc.build(story)
    buffer.seek(0)
    return buffer
