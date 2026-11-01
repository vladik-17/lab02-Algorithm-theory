from decimal import Decimal

import pytest

from energy_calculator.appliances import (
    Appliance, Iron, Kettle, Microwave, Television, WashingMachine,
)
from energy_calculator.calculations import Calculation


def test_reference_calculation():
    result = Calculation(Iron(), 1, 30, 6)
    assert result.energy_kwh == Decimal("60")
    assert result.cost_rub == Decimal("360.00")


def test_decimal_comma_and_money_rounding():
    result = Calculation(Television(1000), "0,5", "1", "1,01")
    assert result.energy_kwh == Decimal("0.5")
    assert result.cost_rub == Decimal("0.51")


def test_result_preserves_original_power():
    appliance = Iron()
    result = Calculation(appliance, 1, 1, 6)
    appliance.power_w = 1000
    assert result.power_w == 2000
    assert result.energy_kwh == 2


@pytest.mark.parametrize("hours, tariff", [(0, 6), (24, 0)])
def test_zero_usage_or_free_tariff(hours, tariff):
    result = Calculation(Television(), hours, 1, tariff)
    assert result.cost_rub == 0


@pytest.mark.parametrize("hours, days, tariff", [
    (-1, 1, 6), (25, 1, 6), (1, 0, 6), (1, "1.5", 6),
    (1, 1, -1), ("", 1, 6), (1, "abc", 6), (1, 1, "NaN"),
    ("Infinity", 1, 6), (1, 1, "1e1000"),
])
def test_invalid_calculation_inputs(hours, days, tariff):
    with pytest.raises(ValueError):
        Calculation(Iron(), hours, days, tariff)


def test_base_class_is_abstract():
    with pytest.raises(TypeError):
        Appliance(100)


@pytest.mark.parametrize("appliance_type", [
    Iron, Television, WashingMachine, Kettle, Microwave,
])
def test_all_appliances_support_custom_power(appliance_type):
    appliance = appliance_type(500)
    assert Calculation(appliance, 2, 10, 6).energy_kwh == 10
    appliance.power_w = 750
    assert appliance.power_w == 750
    assert "750" in str(appliance)


@pytest.mark.parametrize("power", [0, -1, True, "100", float("inf"), float("nan")])
def test_invalid_power_does_not_change_previous_value(power):
    appliance = Iron(1000)
    with pytest.raises(ValueError):
        appliance.power_w = power
    assert appliance.power_w == 1000
