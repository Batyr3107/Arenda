"""
Data export utilities for Excel and CSV
"""
from io import BytesIO
from typing import List, Dict, Any
from datetime import datetime
import csv


def export_to_csv(data: List[Dict[str, Any]], columns: List[str]) -> BytesIO:
    """
    Export data to CSV format

    Args:
        data: List of dictionaries containing the data
        columns: List of column names to include

    Returns:
        BytesIO buffer containing CSV data
    """
    output = BytesIO()

    # Write BOM for Excel to recognize UTF-8
    output.write('\ufeff'.encode('utf-8'))

    # Create CSV writer
    csv_writer = csv.DictWriter(
        output,
        fieldnames=columns,
        extrasaction='ignore',
        encoding='utf-8'
    )

    # Write header
    csv_writer.writeheader()

    # Write data
    for row in data:
        # Convert datetime objects to strings
        formatted_row = {}
        for key, value in row.items():
            if isinstance(value, datetime):
                formatted_row[key] = value.strftime('%Y-%m-%d %H:%M:%S')
            elif value is None:
                formatted_row[key] = ''
            else:
                formatted_row[key] = str(value)
        csv_writer.writerow(formatted_row)

    output.seek(0)
    return output


def export_to_excel(data: List[Dict[str, Any]], columns: List[str], sheet_name: str = "Sheet1") -> BytesIO:
    """
    Export data to Excel format (XLSX)

    Args:
        data: List of dictionaries containing the data
        columns: List of column names to include
        sheet_name: Name of the Excel sheet

    Returns:
        BytesIO buffer containing Excel data
    """
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, Alignment, PatternFill
        from openpyxl.utils import get_column_letter
    except ImportError:
        raise ImportError("openpyxl is required for Excel export. Install it with: pip install openpyxl")

    # Create workbook
    wb = Workbook()
    ws = wb.active
    ws.title = sheet_name

    # Write header
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF")

    for col_num, column in enumerate(columns, 1):
        cell = ws.cell(row=1, column=col_num)
        cell.value = column
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")

    # Write data
    for row_num, row_data in enumerate(data, 2):
        for col_num, column in enumerate(columns, 1):
            value = row_data.get(column, '')

            # Format datetime objects
            if isinstance(value, datetime):
                value = value.strftime('%Y-%m-%d %H:%M:%S')
            elif value is None:
                value = ''

            cell = ws.cell(row=row_num, column=col_num)
            cell.value = value
            cell.alignment = Alignment(horizontal="left", vertical="center")

    # Auto-adjust column widths
    for col_num, column in enumerate(columns, 1):
        column_letter = get_column_letter(col_num)
        max_length = len(column)

        for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=col_num, max_col=col_num):
            for cell in row:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass

        adjusted_width = min(max_length + 2, 50)
        ws.column_dimensions[column_letter].width = adjusted_width

    # Save to BytesIO
    output = BytesIO()
    wb.save(output)
    output.seek(0)

    return output


def payments_to_export_dict(payments: List[Any]) -> List[Dict[str, Any]]:
    """Convert payment objects to dictionary for export"""
    return [
        {
            'ID': payment.id,
            'Номер платежа': payment.payment_number,
            'Договор ID': payment.contract_id,
            'Тип платежа': payment.payment_type.value if hasattr(payment.payment_type, 'value') else payment.payment_type,
            'Сумма': float(payment.amount),
            'Статус': payment.status.value if hasattr(payment.status, 'value') else payment.status,
            'Срок оплаты': payment.due_date.strftime('%Y-%m-%d') if payment.due_date else '',
            'Дата оплаты': payment.payment_date.strftime('%Y-%m-%d') if payment.payment_date else '',
            'Дней просрочки': payment.days_overdue or 0,
            'Пеня': float(payment.late_fee or 0),
            'Создан': payment.created_at,
            'Описание': payment.description or ''
        }
        for payment in payments
    ]


def tenants_to_export_dict(tenants: List[Any]) -> List[Dict[str, Any]]:
    """Convert tenant objects to dictionary for export"""
    return [
        {
            'ID': tenant.id,
            'Название': tenant.name,
            'Тип': tenant.tenant_type.value if hasattr(tenant.tenant_type, 'value') else tenant.tenant_type,
            'БИН/ИИН': tenant.bin_iin,
            'Email': tenant.email or '',
            'Телефон': tenant.phone or '',
            'Адрес': tenant.address or '',
            'Активен': 'Да' if tenant.is_active else 'Нет',
            'Создан': tenant.created_at,
            'Обновлен': tenant.updated_at or ''
        }
        for tenant in tenants
    ]


def contracts_to_export_dict(contracts: List[Any]) -> List[Dict[str, Any]]:
    """Convert contract objects to dictionary for export"""
    return [
        {
            'ID': contract.id,
            'Номер договора': contract.contract_number,
            'Арендатор ID': contract.tenant_id,
            'Помещение ID': contract.premise_id,
            'Дата начала': contract.start_date.strftime('%Y-%m-%d'),
            'Дата окончания': contract.end_date.strftime('%Y-%m-%d'),
            'Ежемесячная арендная плата': float(contract.monthly_rent),
            'Депозит': float(contract.deposit_amount or 0),
            'Статус': contract.status.value if hasattr(contract.status, 'value') else contract.status,
            'Частота платежей': contract.payment_frequency.value if hasattr(contract.payment_frequency, 'value') else contract.payment_frequency,
            'День платежа': contract.payment_day,
            'Процент пени': float(contract.late_fee_percentage or 0),
            'Создан': contract.created_at,
            'Подписан': contract.signed_date.strftime('%Y-%m-%d') if contract.signed_date else ''
        }
        for contract in contracts
    ]


def properties_to_export_dict(properties: List[Any]) -> List[Dict[str, Any]]:
    """Convert property objects to dictionary for export"""
    return [
        {
            'ID': property.id,
            'Название': property.name,
            'Тип': property.property_type.value if hasattr(property.property_type, 'value') else property.property_type,
            'Адрес': property.address,
            'Город': property.city or '',
            'Общая площадь': float(property.total_area or 0),
            'Компания ID': property.company_id,
            'Создан': property.created_at,
            'Описание': property.description or ''
        }
        for property in properties
    ]


def premises_to_export_dict(premises: List[Any]) -> List[Dict[str, Any]]:
    """Convert premise objects to dictionary for export"""
    return [
        {
            'ID': premise.id,
            'Номер': premise.number,
            'Здание ID': premise.building_id,
            'Этаж': premise.floor,
            'Площадь': float(premise.area),
            'Тип': premise.premise_type.value if hasattr(premise.premise_type, 'value') else premise.premise_type,
            'Статус': premise.status.value if hasattr(premise.status, 'value') else premise.status,
            'Цена в месяц': float(premise.price_per_month),
            'Опубликован': 'Да' if premise.is_published else 'Нет',
            'Создан': premise.created_at,
            'Описание': premise.description or ''
        }
        for premise in premises
    ]
