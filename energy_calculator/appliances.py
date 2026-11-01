"""Бытовые приборы. Мощность задаётся в ваттах."""

from abc import ABC, abstractmethod
from math import isfinite


class Appliance(ABC):
    """Общий класс приборов с проверкой мощности."""

    def __init__(self, power_w: float) -> None:
        self.power_w = power_w

    @property
    @abstractmethod
    def name(self) -> str:
        """Название прибора, которое задаёт класс-наследник."""

    @property
    def power_w(self) -> float:
        return self._power_w

    @power_w.setter
    def power_w(self, value: float) -> None:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("Мощность должна быть числом.")
        try:
            power = float(value)
        except OverflowError as exc:
            raise ValueError("Слишком большое значение мощности.") from exc
        if not isfinite(power) or power <= 0:
            raise ValueError("Мощность должна быть конечным числом больше нуля.")
        self._power_w = power

    def __str__(self) -> str:
        return f"{self.name}: {self.power_w:g} Вт"


class Iron(Appliance):
    """Утюг."""

    def __init__(self, power_w: float = 2000) -> None:
        super().__init__(power_w)

    @property
    def name(self) -> str:
        return "Утюг"

    def __str__(self) -> str:
        return super().__str__()


class Television(Appliance):
    """Телевизор."""

    def __init__(self, power_w: float = 100) -> None:
        super().__init__(power_w)

    @property
    def name(self) -> str:
        return "Телевизор"

    def __str__(self) -> str:
        return super().__str__()


class WashingMachine(Appliance):
    """Стиральная машина."""

    def __init__(self, power_w: float = 1800) -> None:
        super().__init__(power_w)

    @property
    def name(self) -> str:
        return "Стиральная машина"

    def __str__(self) -> str:
        return super().__str__()


class Kettle(Appliance):
    """Электрический чайник."""

    def __init__(self, power_w: float = 2000) -> None:
        super().__init__(power_w)

    @property
    def name(self) -> str:
        return "Чайник"

    def __str__(self) -> str:
        return super().__str__()


class Microwave(Appliance):
    """Микроволновая печь; указывается потребляемая мощность."""

    def __init__(self, power_w: float = 1200) -> None:
        super().__init__(power_w)

    @property
    def name(self) -> str:
        return "Микроволновка"

    def __str__(self) -> str:
        return super().__str__()
