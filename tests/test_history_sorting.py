from main import sort_history_rows


def test_numbers_are_sorted_by_value_in_both_directions():
    rows = [{"cost_rub": value} for value in ("100.00", "2.50", "10.01")]
    assert [r["cost_rub"] for r in sort_history_rows(rows, "cost_rub")] == [
        "2.50", "10.01", "100.00",
    ]
    assert [r["cost_rub"] for r in sort_history_rows(rows, "cost_rub", True)] == [
        "100.00", "10.01", "2.50",
    ]
    assert rows[0]["cost_rub"] == "100.00"


def test_integer_ids_and_equal_values():
    rows = [{"id": 10}, {"id": 2}, {"id": 1}]
    assert [r["id"] for r in sort_history_rows(rows, "id")] == [1, 2, 10]
    rows = [{"cost_rub": "1.0", "id": 2}, {"cost_rub": "1.00", "id": 1}]
    assert [r["id"] for r in sort_history_rows(rows, "cost_rub")] == [2, 1]


def test_names_are_sorted_without_case_sensitivity():
    rows = [{"appliance_name": name} for name in ("чайник", "Утюг", "Телевизор")]
    assert [r["appliance_name"] for r in sort_history_rows(rows, "appliance_name")] == [
        "Телевизор", "Утюг", "чайник",
    ]


def test_dates_are_sorted_chronologically_with_timezones():
    rows = [{"created_at": value} for value in (
        "2026-11-01T10:00:00+00:00", "2026-11-01T12:00:00+03:00",
    )]
    assert sort_history_rows(rows, "created_at")[0] == rows[1]


def test_empty_history_can_be_sorted():
    assert sort_history_rows([], "id") == []
