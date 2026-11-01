"""История расчётов в SQLite и экспорт сохранённых результатов в Excel."""

from contextlib import closing
from datetime import datetime
from pathlib import Path
import sqlite3

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill

from energy_calculator.calculations import Calculation


class HistoryRepository:
    """Хранит числовые значения как текст без потери точности Decimal."""

    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.database_path)) as connection:
            with connection:
                connection.execute("""
                    CREATE TABLE IF NOT EXISTS calculations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        created_at TEXT NOT NULL,
                        appliance_name TEXT NOT NULL,
                        power_w TEXT NOT NULL,
                        hours_per_day TEXT NOT NULL,
                        days TEXT NOT NULL,
                        tariff TEXT NOT NULL,
                        energy_kwh TEXT NOT NULL,
                        cost_rub TEXT NOT NULL
                    )
                """)

    def __str__(self) -> str:
        return f"История расчётов: {self.database_path}"

    def save(self, calculation: Calculation) -> int:
        values = (
            datetime.now().astimezone().isoformat(timespec="seconds"),
            calculation.appliance_name,
            str(calculation.power_w), str(calculation.hours_per_day),
            str(calculation.days), str(calculation.tariff),
            str(calculation.energy_kwh), str(calculation.cost_rub),
        )
        with closing(sqlite3.connect(self.database_path)) as connection:
            with connection:
                cursor = connection.execute("""
                    INSERT INTO calculations
                    (created_at, appliance_name, power_w, hours_per_day,
                     days, tariff, energy_kwh, cost_rub)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, values)
                return cursor.lastrowid

    def all(self) -> list[sqlite3.Row]:
        """Вернуть всю историю, начиная с последнего расчёта."""
        with closing(sqlite3.connect(self.database_path)) as connection:
            connection.row_factory = sqlite3.Row
            return connection.execute(
                "SELECT * FROM calculations ORDER BY id DESC"
            ).fetchall()

    def export_excel(self, file_path: str | Path) -> int:
        """Выгрузить снимок всей истории; вернуть количество записей."""
        rows = self.all()
        if not rows:
            raise ValueError("История пуста. Сначала выполните расчёт.")

        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "История расчётов"
        sheet.append([
            "№", "Дата и время", "Прибор", "Мощность, Вт",
            "Часы в день", "Дни", "Тариф, руб./кВт·ч",
            "Энергия, кВт·ч", "Стоимость, руб.",
        ])
        for row in rows:
            sheet.append([
                row["id"], row["created_at"], row["appliance_name"],
                *[float(row[key]) for key in (
                    "power_w", "hours_per_day", "days", "tariff",
                    "energy_kwh", "cost_rub",
                )],
            ])

        for cell in sheet[1]:
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill("solid", fgColor="24527A")
        for column, width in zip("ABCDEFGHI", [8, 30, 24, 20, 18, 12, 24, 22, 22]):
            sheet.column_dimensions[column].width = width
        for cells in sheet.iter_rows(min_row=2, min_col=4, max_col=9):
            for cell in cells:
                cell.number_format = "0.####"
            cells[-1].number_format = "0.00"
        sheet.freeze_panes = "A2"
        sheet.auto_filter.ref = sheet.dimensions
        try:
            workbook.save(file_path)
        finally:
            workbook.close()
        return len(rows)
