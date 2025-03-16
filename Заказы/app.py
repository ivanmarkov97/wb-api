import os
import typing as t
from pathlib import Path

import httpx
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

API_URL: t.Final[str] = "https://statistics-api.wildberries.ru/api/v1/supplier/orders"  # API url
TOKEN: t.Final[str] = os.environ["WB_TOKEN"]  # token WB из файла .env
DATA_FOLDER: Path = Path(__file__).parent / "reports"  # папка с отчетами

report_date: str = "2025-03-09"  # отчетная дата (задать самому)

NAME_MAPPING: dict[str, str] = {
    "incomeId": "Номер поставки",
    "number": "Номер УПД",
    "date": "Дата поступления",
    "lastChangeDate": "Дата и время обновления информации в сервисе",
    "supplierArticle": "Артикул продавца",
    "techSize": "Размер товара",
    "barcode": "Баркод",
    "quantity": "Количество",
    "totalPrice": "Цена из УПД",
    "dateClose": "Дата принятия (закрытия) в WB",
    "warehouseName": "Склад отгрузки",
    "warehouseType": "Тип склада хранения товаров",
    "countryName": "Страна",
    "oblastOkrugName": "Округ",
    "regionName": "Регион",
    "category": "Категория",
    "subject": "Товар",
    "brand": "Бренд",
    "nmId": "Артикул WB",
    "status": "Текущий статус поставки",
    "isSupply": "Договор поставки",
    "isRealization": "Договор реализации",
    "isCancel": "Отменен ли",
    "cancelDate": "Дата отмены",
    "orderType": "Тип заказа",
    "discountPercent": "Скидка продавца",
    "spp": "Скидка WB",
    "finishedPrice": "Фактическая цена с учетом всех скидок",
    "priceWithDisc": "Цена со скидкой продавца",
    "sticker": "ID стикера",
    "gNumber": "Номер заказа",
    "srid": "Уникальный ID заказа"
}


def create_named_object_from_api(
        data_item: dict[str, t.Any],
        name_mapping: dict[str, str]
) -> dict:
    """Создает переименованный объект на оснвое таблицы перевода.

    Args:
        data_item: Объект для переименовая.
        name_mapping: Таблица перевода.
    Returns:
        Переименованный объект.
    """
    named_object: dict[str, t.Any] = {}
    for name, any_value in data_item.items():
        new_name: str = name_mapping.get(name, name)
        named_object[new_name] = any_value
    return named_object


def create_rows_for_excel_report(date_from: str) -> list[dict[str, t.Any]]:
    """Подготавливает список объектов для создания Excel таблицы.

    Args:
        date_from: Дата в формате RFC3339 (yyyy-mm-dd) для поиска поставок.
    Returns:
        Список строк для формирования Excel таблицы.
    """
    with httpx.Client() as client:
        response = client.get(
            API_URL,
            headers={"Authorization": TOKEN},
            params={"dateFrom": date_from},
            timeout=60
        )
        if response.status_code != 200:
            raise ValueError(f"Ошибка при отправке запроса. Статус: {response.status_code}")
        data_items: list[dict[str, t.Any]] = response.json()
        named_items: list[dict[str, t.Any]] = [
            create_named_object_from_api(data_item, name_mapping=NAME_MAPPING)
            for data_item in data_items
        ]
        return named_items


if __name__ == "__main__":
    table_rows: list[dict[str, t.Any]] = create_rows_for_excel_report(report_date)
    table: pd.DataFrame = pd.DataFrame(table_rows)
    report_name: str = f"Отчет_по_заказам_{report_date}.xlsx"
    table.to_excel(DATA_FOLDER / report_name, index=False)
