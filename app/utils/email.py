from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from typing import List
from app.core.config import settings
from jinja2 import Template


# Email configuration
conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=settings.MAIL_TLS,
    MAIL_SSL_TLS=settings.MAIL_SSL,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

fm = FastMail(conf)


async def send_email(
    email_to: List[str],
    subject: str,
    body: str,
    subtype: MessageType = MessageType.html
):
    """Send email"""
    message = MessageSchema(
        subject=subject,
        recipients=email_to,
        body=body,
        subtype=subtype
    )

    await fm.send_message(message)


# Email templates
PAYMENT_DUE_TEMPLATE = """
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; }}
        .container {{ padding: 20px; }}
        .header {{ background-color: #4CAF50; color: white; padding: 10px; }}
        .content {{ padding: 20px; }}
        .footer {{ background-color: #f1f1f1; padding: 10px; text-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>Напоминание об оплате</h2>
        </div>
        <div class="content">
            <p>Уважаемый(ая) {tenant_name},</p>
            <p>Напоминаем, что приближается срок оплаты по договору аренды:</p>
            <ul>
                <li>Договор: {contract_number}</li>
                <li>Помещение: {premise_number}</li>
                <li>Сумма: {amount} тг</li>
                <li>Срок оплаты: {due_date}</li>
            </ul>
            <p>Просим произвести оплату в указанный срок.</p>
        </div>
        <div class="footer">
            <p>С уважением,<br>Команда Arenda</p>
        </div>
    </div>
</body>
</html>
"""

PAYMENT_OVERDUE_TEMPLATE = """
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; }}
        .container {{ padding: 20px; }}
        .header {{ background-color: #f44336; color: white; padding: 10px; }}
        .content {{ padding: 20px; }}
        .warning {{ color: #f44336; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>Просрочка оплаты</h2>
        </div>
        <div class="content">
            <p>Уважаемый(ая) {tenant_name},</p>
            <p class="warning">Обнаружена просрочка платежа:</p>
            <ul>
                <li>Договор: {contract_number}</li>
                <li>Сумма: {amount} тг</li>
                <li>Срок оплаты: {due_date}</li>
                <li>Дней просрочки: {days_overdue}</li>
                <li>Пеня: {late_fee} тг</li>
            </ul>
            <p>Просим срочно произвести оплату для избежания дополнительных штрафов.</p>
        </div>
    </div>
</body>
</html>
"""

NEW_LEAD_TEMPLATE = """
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; }}
        .container {{ padding: 20px; }}
        .header {{ background-color: #2196F3; color: white; padding: 10px; }}
        .content {{ padding: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>Новая заявка</h2>
        </div>
        <div class="content">
            <p>Получена новая заявка от клиента:</p>
            <ul>
                <li>ФИО: {full_name}</li>
                <li>Компания: {company_name}</li>
                <li>Телефон: {phone}</li>
                <li>Email: {email}</li>
                <li>Желаемая площадь: {desired_area} кв.м</li>
                <li>Бюджет: {budget} тг</li>
                <li>Комментарий: {message}</li>
            </ul>
            <p>Необходимо связаться с клиентом в ближайшее время.</p>
        </div>
    </div>
</body>
</html>
"""

CONTRACT_EXPIRING_TEMPLATE = """
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; }}
        .container {{ padding: 20px; }}
        .header {{ background-color: #FF9800; color: white; padding: 10px; }}
        .content {{ padding: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>Срок действия договора истекает</h2>
        </div>
        <div class="content">
            <p>Уважаемый(ая) {tenant_name},</p>
            <p>Напоминаем, что срок действия договора аренды истекает:</p>
            <ul>
                <li>Договор: {contract_number}</li>
                <li>Помещение: {premise_number}</li>
                <li>Дата окончания: {end_date}</li>
            </ul>
            <p>Для продления договора свяжитесь с нашим менеджером.</p>
        </div>
    </div>
</body>
</html>
"""


async def send_payment_due_notification(
    email_to: str,
    tenant_name: str,
    contract_number: str,
    premise_number: str,
    amount: float,
    due_date: str
):
    """Send payment due notification"""
    template = Template(PAYMENT_DUE_TEMPLATE)
    body = template.render(
        tenant_name=tenant_name,
        contract_number=contract_number,
        premise_number=premise_number,
        amount=amount,
        due_date=due_date
    )

    await send_email(
        email_to=[email_to],
        subject="Напоминание об оплате аренды",
        body=body
    )


async def send_payment_overdue_notification(
    email_to: str,
    tenant_name: str,
    contract_number: str,
    amount: float,
    due_date: str,
    days_overdue: int,
    late_fee: float
):
    """Send payment overdue notification"""
    template = Template(PAYMENT_OVERDUE_TEMPLATE)
    body = template.render(
        tenant_name=tenant_name,
        contract_number=contract_number,
        amount=amount,
        due_date=due_date,
        days_overdue=days_overdue,
        late_fee=late_fee
    )

    await send_email(
        email_to=[email_to],
        subject="ПРОСРОЧКА ОПЛАТЫ - Требуется срочная оплата",
        body=body
    )


async def send_new_lead_notification(
    email_to: List[str],
    full_name: str,
    company_name: str,
    phone: str,
    email: str,
    desired_area: float,
    budget: float,
    message: str
):
    """Send new lead notification to managers"""
    template = Template(NEW_LEAD_TEMPLATE)
    body = template.render(
        full_name=full_name,
        company_name=company_name or "Не указана",
        phone=phone,
        email=email,
        desired_area=desired_area or "Не указана",
        budget=budget or "Не указан",
        message=message or "Нет комментария"
    )

    await send_email(
        email_to=email_to,
        subject="Новая заявка на аренду",
        body=body
    )


async def send_contract_expiring_notification(
    email_to: str,
    tenant_name: str,
    contract_number: str,
    premise_number: str,
    end_date: str
):
    """Send contract expiring notification"""
    template = Template(CONTRACT_EXPIRING_TEMPLATE)
    body = template.render(
        tenant_name=tenant_name,
        contract_number=contract_number,
        premise_number=premise_number,
        end_date=end_date
    )

    await send_email(
        email_to=[email_to],
        subject="Истекает срок действия договора аренды",
        body=body
    )
