"""Графический интерфейс энергокалькулятора."""

import tkinter as tk
from tkinter import filedialog, font, messagebox, ttk
from datetime import datetime
from decimal import Decimal
from pathlib import Path
import sqlite3

from energy_calculator.appliances import (
    Iron, Kettle, Microwave, Television, WashingMachine,
)
from energy_calculator.calculations import Calculation, read_number
from energy_calculator.storage import HistoryRepository


APPLIANCES = {
    appliance_type().name: appliance_type
    for appliance_type in (Iron, Television, WashingMachine, Kettle, Microwave)
}


def sort_history_rows(rows, column: str, descending: bool = False):
    """Сортировать числа как числа, даты по времени, названия по алфавиту."""
    def sort_key(row):
        value = row[column]
        if column == "appliance_name":
            return value.casefold()
        if column == "created_at":
            return datetime.fromisoformat(value)
        return Decimal(str(value))

    return sorted(rows, key=sort_key, reverse=descending)


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
        "Каждый успешный расчёт автоматически сохраняется. Во вкладке "
        "«История» можно просмотреть записи и выгрузить всю историю "
        "кнопкой «Экспорт в Excel». Выберите место сохранения файла .xlsx.\n\n"
        "Окно можно растягивать. Ширина столбцов подбирается по содержимому. "
        "Нажмите заголовок столбца для сортировки; повторный клик меняет "
        "направление. Стрелка показывает выбранный порядок. "
        "Сортировка таблицы не меняет порядок записей в Excel.",
    )


def main() -> None:
    window = tk.Tk()
    window.title("Энергокалькулятор")
    window.geometry("780x620")
    window.minsize(520, 540)
    window.columnconfigure(0, weight=1)
    window.rowconfigure(0, weight=1)

    try:
        repository = HistoryRepository(Path(__file__).resolve().parent / "data" / "history.db")
    except (OSError, sqlite3.Error):
        window.withdraw()
        messagebox.showerror("Ошибка", "Не удалось открыть историю. Проверьте права доступа к папке data.")
        window.destroy()
        return

    notebook = ttk.Notebook(window)
    notebook.grid(sticky="nsew", padx=12, pady=12)
    content = ttk.Frame(notebook, padding=20)
    notebook.add(content, text="Расчёт")
    content.columnconfigure(0, weight=1)
    content.rowconfigure(6, weight=1)

    history_tab = ttk.Frame(notebook, padding=12)
    notebook.add(history_tab, text="История")
    history_tab.columnconfigure(0, weight=1)
    history_tab.rowconfigure(2, weight=1)
    history_count = tk.StringVar(value="История пуста")
    toolbar = ttk.Frame(history_tab)
    toolbar.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
    toolbar.columnconfigure(0, weight=1)
    ttk.Label(toolbar, textvariable=history_count).grid(row=0, column=0, sticky="w")

    columns = ("id", "created_at", "appliance_name", "power_w", "hours_per_day",
               "days", "tariff", "energy_kwh", "cost_rub")
    titles = dict(zip(columns, (
        "№", "Дата и время", "Прибор", "Мощность, Вт", "Часы в день",
        "Дни", "Тариф, руб./кВт·ч", "Энергия, кВт·ч", "Стоимость, руб.",
    )))
    row_font = font.Font(window, family="Segoe UI", size=10)
    heading_font = font.Font(window, family="Segoe UI", size=10, weight="bold")
    style = ttk.Style(window)
    style.configure("History.Treeview", font=row_font,
                    rowheight=row_font.metrics("linespace") + 12)
    style.configure("History.Treeview.Heading", font=heading_font, padding=(8, 8))
    style.map("History.Treeview", background=[("selected", "#DCEBFA")],
              foreground=[("selected", "#153653")])
    table = ttk.Treeview(history_tab, columns=columns, show="headings", height=12,
                         style="History.Treeview")
    table.tag_configure("even", background="#FFFFFF")
    table.tag_configure("odd", background="#F0F5FA")
    ttk.Label(toolbar, text="Нажмите заголовок для сортировки ↑↓", foreground="#526475").grid(
        row=1, column=0, columnspan=2, sticky="w", pady=(6, 0)
    )
    table.grid(row=2, column=0, sticky="nsew")
    vertical = ttk.Scrollbar(history_tab, orient="vertical", command=table.yview)
    vertical.grid(row=2, column=1, sticky="ns")
    horizontal = ttk.Scrollbar(history_tab, orient="horizontal", command=table.xview)
    horizontal.grid(row=3, column=0, sticky="ew")
    table.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)

    history_rows = []
    sort_state = {"column": "id", "descending": True}

    def fit_columns() -> None:
        for key in columns:
            # Резервируем место под стрелку, чтобы клик не менял ширину заголовка.
            heading_width = heading_font.measure(titles[key] + " ▼") + 24
            values_width = max(
                (row_font.measure(table.set(item, key)) + 24 for item in table.get_children()),
                default=0,
            )
            table.column(key, width=max(heading_width, values_width),
                         minwidth=heading_width, stretch=False,
                         anchor="w" if key in columns[1:3] else "e")

    def render_history() -> None:
        selected = table.selection()
        table.delete(*table.get_children())
        rows = sort_history_rows(history_rows, sort_state["column"], sort_state["descending"])
        for index, row in enumerate(rows):
            values = [row[key] for key in columns]
            values[1] = row["created_at"][:19].replace("T", " ")
            values[-2] = f"{Decimal(row['energy_kwh']):.4f}"
            values[-1] = f"{Decimal(row['cost_rub']):.2f}"
            table.insert("", "end", iid=str(row["id"]), values=values,
                         tags=("even" if index % 2 == 0 else "odd",))
        for key in columns:
            arrow = (" ▼" if sort_state["descending"] else " ▲") if key == sort_state["column"] else ""
            table.heading(key, text=titles[key] + arrow)
        table.selection_set([item for item in selected if table.exists(item)])
        fit_columns()
        history_count.set(f"Сохранено расчётов: {len(rows)}")

    def sort_column(key: str) -> None:
        sort_state["descending"] = not sort_state["descending"] if sort_state["column"] == key else False
        sort_state["column"] = key
        render_history()

    for key in columns:
        table.heading(key, command=lambda column=key: sort_column(column))

    def refresh_history() -> None:
        history_rows[:] = repository.all()
        render_history()

    def export_history() -> None:
        try:
            if not repository.all():
                messagebox.showinfo("Экспорт", "История пуста. Сначала выполните расчёт.")
                return
            file_path = filedialog.asksaveasfilename(
                title="Сохранить всю историю", defaultextension=".xlsx",
                filetypes=[("Книга Excel", "*.xlsx")], initialfile="energy_history.xlsx",
                parent=window,
            )
            if not file_path:
                return
            count = repository.export_excel(file_path)
        except (OSError, sqlite3.Error, ValueError):
            messagebox.showerror(
                "Ошибка экспорта", "Не удалось сохранить файл. Закройте его в Excel "
                "и проверьте доступ к выбранной папке.",
            )
            return
        messagebox.showinfo("Экспорт завершён", f"В Excel сохранено расчётов: {count}.")

    ttk.Button(toolbar, text="Экспорт в Excel", command=export_history).grid(
        row=0, column=1, sticky="e", padx=(10, 0)
    )
    try:
        refresh_history()
    except (OSError, sqlite3.Error):
        messagebox.showerror("Ошибка", "Не удалось прочитать историю расчётов.")

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
    save_text = tk.StringVar()

    def clear_result(*_args) -> None:
        result_text.set("Данные изменены. Нажмите «Рассчитать».")
        error_text.set("")
        save_text.set("")

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
            save_text.set("")
            return
        error_text.set("")
        result_text.set(
            f"{result.appliance_name} · {result.power_w:g} Вт\n"
            f"Энергия за {result.days:g} дн.: {result.energy_kwh:.4f} кВт·ч\n"
            f"Стоимость: {result.cost_rub:.2f} руб."
        )
        try:
            record_id = repository.save(result)
        except (OSError, sqlite3.Error):
            save_text.set("")
            error_text.set("Результат рассчитан, но не сохранён. Проверьте доступ к папке data.")
            return
        save_text.set(f"Сохранено в истории: № {record_id}")
        try:
            refresh_history()
        except (OSError, sqlite3.Error):
            error_text.set("Расчёт сохранён, но таблицу истории не удалось обновить. Перезапустите программу.")

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
    ttk.Label(result_frame, textvariable=save_text).grid(sticky="ew", pady=(6, 0))
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
