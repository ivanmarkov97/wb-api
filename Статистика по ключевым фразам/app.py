import os
import typing as t
from pathlib import Path
from datetime import datetime, date

import httpx
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

API_URL: t.Final[str] = "https://advert-api.wildberries.ru/adv/v0/stats/keywords"  # API url
TOKEN: t.Final[str] = os.environ["WB_TOKEN"]  # token WB из файла .env
DATA_FOLDER: Path = Path(__file__).parent / "reports"  # папка с отчетами

campaign_id: int = 23827889  # кампания (задать самому)
date_from: str = "2025-03-09"  # дата начала периода (задать самому)
date_to: str = "2025-03-12"  # дата конца периода (задать самому)

NAME_MAPPING: dict[str, str] = {
    "clicks": "Количество кликов",
    "ctr": "CTR",
    "keyword": "Ключевая фраза",
    "sum": "Сумма затрат по ключевой фразе",
    "views": "Количество показов"
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


def create_rows_for_excel_report(
        campaign_id: int,
        date_from: str,
        date_to: str
) -> list[dict[str, t.Any]]:
    """Подготавливает список объектов для создания Excel таблицы.

    Args:
        campaign_id: ID кампании.
        date_from: Начало периода.
        date_to: Конец периода.
    Returns:
        Список строк для формирования Excel таблицы.
    """
    with httpx.Client() as client:
        response = client.get(
            API_URL,
            headers={"Authorization": TOKEN},
            params={
                "advert_id": campaign_id,
                "from": date_from,
                "to": date_to
            },
            timeout=60
        )
        start_date: date = datetime.strptime(date_from, "%Y-%m-%d").date()
        end_date: date = datetime.strptime(date_to, "%Y-%m-%d").date()
        if start_date >= end_date:
            raise ValueError("Дата начала периода должна быть меньше даты конца периода.")
        if (end_date - start_date).days >= 7:
            raise ValueError("Период должен быть менее 7 дней.")

        if response.status_code != 200:
            raise ValueError(f"Ошибка при отправке запроса. Статус: {response.status_code}")
        data_items: list[dict] = response.json()["keywords"]
        data_items = sorted(data_items, key=lambda v: v["date"])

        output_rows: list[dict[str, t.Any]] = []
        for report_date_data in data_items:
            report_date: str = report_date_data["date"]
            for statistics in report_date_data["stats"]:
                statistics["ID_кампании"] = campaign_id
                statistics["Отчетная дата"] = report_date
                named_statistics: dict[str, t.Any] = create_named_object_from_api(
                    statistics, name_mapping=NAME_MAPPING
                )
                output_rows.append(named_statistics)
        return output_rows


if __name__ == "__main__":
    table_rows: list[dict[str, t.Any]] = create_rows_for_excel_report(campaign_id, date_from, date_to)
    table: pd.DataFrame = pd.DataFrame(table_rows)
    report_name: str = f"Отчет_по_cтатистике_кампании_{campaign_id}_по_ключевым_фразам_{date_from}_{date_to}.xlsx"
    table.to_excel(DATA_FOLDER / report_name, index=False)
