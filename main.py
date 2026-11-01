"""Графический интерфейс энергокалькулятора."""

import tkinter as tk
from tkinter import messagebox, ttk

from energy_calculator.appliances import (
    Iron, Kettle, Microwave, Television, WashingMachine,
)
from energy_calculator.calculations import Calculation, read_number


APPLIANCES = {
    appliance_type().name: appliance_type
    for appliance_type in (Iron, Television, WashingMachine, Kettle, Microwave)
}


def show_help() -> None:
    messagebox.showinfo(
        "Справка",
        "1. Выберите прибор. Начальная мощность — пример: уточните её "
        "по инструкции своего прибора.\n"
        "2. Укажите мощность в ваттах, часы работы в день (от 0 до 24), "
        "целое количество дней (от 1) и тариф в руб./кВт·ч.\n"
        "3. Нажмите «Рассчитать» или Enter. Дробные числа можно вводить "
        "с точкой или запятой.\n\n"
        "Энергия = мощность / 1000 × часы в день × дни.\n"
        "Стоимость = энергия × тариф.\n\n"
        "Расчёт предполагает постоянную мощность. Фактическое потребление "
        "зависит от режима работы. Для микроволновки нужна потребляемая "
        "мощность, а не мощность нагрева.\n\n"
        "Окно можно растягивать. Сохранение и экспорт пока недоступны.",
    )


def main() -> None:
    window = tk.Tk()
    window.title("Энергокалькулятор")
    window.geometry("640x560")
    window.minsize(460, 500)
    window.columnconfigure(0, weight=1)
    window.rowconfigure(0, weight=1)

    content = ttk.Frame(window, padding=20)
    content.grid(sticky="nsew")
    content.columnconfigure(0, weight=1)
    content.rowconfigure(5, weight=1)

    ttk.Label(content, text="Бытовая техника", font=("Segoe UI", 22)).grid(
        row=0, column=0, sticky="w", pady=(0, 8)
    )
    ttk.Label(content, text="Оценка энергопотребления и стоимости").grid(
        row=1, column=0, sticky="w", pady=(0, 16)
    )

    fields = {
        "Прибор": tk.StringVar(value="Утюг"),
        "Мощность, Вт": tk.StringVar(value="2000"),
        "Часы работы в день": tk.StringVar(value="1"),
        "Количество дней": tk.StringVar(value="30"),
        "Тариф, руб./кВт·ч": tk.StringVar(value="6"),
    }
    form = ttk.Frame(content)
    form.grid(row=2, column=0, sticky="ew")
    form.columnconfigure(1, weight=1)
    for row, (label, variable) in enumerate(fields.items()):
        ttk.Label(form, text=label).grid(row=row, column=0, sticky="w", padx=(0, 16), pady=6)
        if row == 0:
            selector = ttk.Combobox(
                form, textvariable=variable, values=list(APPLIANCES), state="readonly", width=20
            )
            selector.grid(row=row, column=1, sticky="ew", pady=6)
        else:
            ttk.Entry(form, textvariable=variable, width=20).grid(
                row=row, column=1, sticky="ew", pady=6
            )

    result_text = tk.StringVar(value="Заполните поля и нажмите «Рассчитать».")
    error_text = tk.StringVar()

    def clear_result(*_args) -> None:
        result_text.set("Данные изменены. Нажмите «Рассчитать».")
        error_text.set("")

    def select_appliance(_event) -> None:
        appliance = APPLIANCES[fields["Прибор"].get()]()
        fields["Мощность, Вт"].set(f"{appliance.power_w:g}")

    selector.bind("<<ComboboxSelected>>", select_appliance)
    for variable in fields.values():
        variable.trace_add("write", clear_result)

    def calculate(_event=None) -> None:
        try:
            power = read_number(fields["Мощность, Вт"].get(), "Мощность")
            appliance = APPLIANCES[fields["Прибор"].get()](float(power))
            result = Calculation(
                appliance,
                fields["Часы работы в день"].get(),
                fields["Количество дней"].get(),
                fields["Тариф, руб./кВт·ч"].get(),
            )
        except ValueError as exc:
            result_text.set("Расчёт не выполнен.")
            error_text.set(str(exc))
            return
        error_text.set("")
        result_text.set(
            f"{result.appliance_name} · {result.power_w:g} Вт\n"
            f"Энергия за {result.days:g} дн.: {result.energy_kwh:.4f} кВт·ч\n"
            f"Стоимость: {result.cost_rub:.2f} руб."
        )

    buttons = ttk.Frame(content)
    buttons.grid(row=3, column=0, sticky="ew", pady=(16, 12))
    buttons.columnconfigure(0, weight=1)
    buttons.columnconfigure(1, weight=1)
    ttk.Button(buttons, text="Рассчитать", command=calculate).grid(
        row=0, column=0, sticky="ew", padx=(0, 6)
    )
    ttk.Button(buttons, text="Справка", command=show_help).grid(
        row=0, column=1, sticky="ew", padx=(6, 0)
    )

    result_frame = ttk.LabelFrame(content, text="Результат", padding=12)
    result_frame.grid(row=4, column=0, sticky="ew")
    result_frame.columnconfigure(0, weight=1)
    result_label = ttk.Label(result_frame, textvariable=result_text, wraplength=360)
    result_label.grid(sticky="ew")
    error_label = ttk.Label(content, textvariable=error_text, foreground="#b91c1c", wraplength=360)
    error_label.grid(row=5, column=0, sticky="new", pady=(10, 0))
    content.bind(
        "<Configure>",
        lambda event: (
            result_label.configure(wraplength=max(100, event.width - 64)),
            error_label.configure(wraplength=max(100, event.width - 40)),
        ),
    )
    window.bind("<Return>", calculate)
    window.mainloop()


if __name__ == "__main__":
    main()
