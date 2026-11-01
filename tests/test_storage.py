from decimal import Decimal

from openpyxl import load_workbook
import pytest

from energy_calculator.appliances import Iron, Television
from energy_calculator.calculations import Calculation
from energy_calculator.storage import HistoryRepository


def test_history_survives_reopening_and_keeps_all_values(tmp_path):
    path = tmp_path / "data" / "history.db"
    repository = HistoryRepository(path)
    assert repository.all() == []
    first_id = repository.save(Calculation(Iron(), "0,5", 30, "6,15"))
    second_id = repository.save(Calculation(Television(), 2, 10, 6))

    rows = HistoryRepository(path).all()
    assert [row["id"] for row in rows] == [second_id, first_id]
    saved = rows[1]
    assert saved["appliance_name"] == "Утюг"
    assert Decimal(saved["power_w"]) == 2000
    assert Decimal(saved["hours_per_day"]) == Decimal("0.5")
    assert Decimal(saved["days"]) == 30
    assert Decimal(saved["tariff"]) == Decimal("6.15")
    assert Decimal(saved["energy_kwh"]) == 30
    assert Decimal(saved["cost_rub"]) == Decimal("184.50")
    assert saved["created_at"]


def test_export_contains_entire_history_with_numeric_cells(tmp_path):
    repository = HistoryRepository(tmp_path / "history.db")
    repository.save(Calculation(Iron(), 1, 30, 6))
    repository.save(Calculation(Television(), 2, 10, 6))
    path = tmp_path / "history.xlsx"
    assert repository.export_excel(path) == 2

    workbook = load_workbook(path)
    try:
        sheet = workbook.active
        assert sheet.title == "История расчётов"
        assert sheet.max_row == 3
        assert sheet.max_column == 9
        assert sheet["C2"].value == "Телевизор"
        assert sheet["C3"].value == "Утюг"
        assert sheet["H3"].value == 60
        assert sheet["I3"].value == 360
        assert sheet["I3"].data_type == "n"
        assert sheet["I3"].number_format == "0.00"
        assert sheet.freeze_panes == "A2"
        assert sheet.auto_filter.ref == "A1:I3"
    finally:
        workbook.close()


def test_empty_export_preserves_existing_file(tmp_path):
    repository = HistoryRepository(tmp_path / "history.db")
    path = tmp_path / "history.xlsx"
    path.write_bytes(b"existing file")
    with pytest.raises(ValueError, match="История пуста"):
        repository.export_excel(path)
    assert path.read_bytes() == b"existing file"


def test_export_does_not_modify_database(tmp_path):
    repository = HistoryRepository(tmp_path / "history.db")
    repository.save(Calculation(Iron(), 1, 1, "1,005"))
    before = [dict(row) for row in repository.all()]
    repository.export_excel(tmp_path / "history.xlsx")
    assert [dict(row) for row in repository.all()] == before


def test_export_reports_write_error(tmp_path):
    repository = HistoryRepository(tmp_path / "history.db")
    repository.save(Calculation(Iron(), 1, 1, 6))
    with pytest.raises(OSError):
        repository.export_excel(tmp_path / "missing" / "history.xlsx")
