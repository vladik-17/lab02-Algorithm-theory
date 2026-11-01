"""Расчёт энергии и стоимости при постоянной мощности прибора."""

from decimal import Decimal, DecimalException, ROUND_HALF_UP

from energy_calculator.appliances import Appliance


def read_number(value, label: str) -> Decimal:
    """Принять число с точкой или запятой и проверить его корректность."""
    try:
        number = Decimal(str(value).strip().replace(",", "."))
    except DecimalException as exc:
        raise ValueError(f"{label}: введите число.") from exc
    if not number.is_finite():
        raise ValueError(f"{label}: введите конечное число.")
    return number


class Calculation:
    """Один расчёт; значения прибора сохраняются на момент создания."""

    def __init__(self, appliance: Appliance, hours_per_day, days, tariff) -> None:
        self.appliance_name = appliance.name
        self.power_w = Decimal(str(appliance.power_w))
        self.hours_per_day = read_number(hours_per_day, "Часы работы")
        self.days = read_number(days, "Количество дней")
        self.tariff = read_number(tariff, "Тариф")

        if not 0 <= self.hours_per_day <= 24:
            raise ValueError("Часы работы: допустимо от 0 до 24 часов в день.")
        if self.days < 1 or self.days != self.days.to_integral_value():
            raise ValueError("Количество дней должно быть целым числом от 1.")
        if self.tariff < 0:
            raise ValueError("Тариф не может быть отрицательным.")

        try:
            self.energy_kwh = self.power_w / 1000 * self.hours_per_day * self.days
            self.cost_rub = (self.energy_kwh * self.tariff).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
        except DecimalException as exc:
            raise ValueError("Слишком большие значения для расчёта.") from exc

    def __str__(self) -> str:
        return (
            f"{self.appliance_name}: {self.energy_kwh:.4f} кВт·ч, "
            f"{self.cost_rub:.2f} руб."
        )
