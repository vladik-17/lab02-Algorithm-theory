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


def show_help(parent=None) -> None:
    help_window = tk.Toplevel(parent)
    help_window.title("Справка")
    help_window.geometry("720x560")
    help_window.minsize(540, 380)
    help_window.configure(background="#EEF3F9")
    help_window.columnconfigure(0, weight=1)
    help_window.rowconfigure(1, weight=1)
    ttk.Label(help_window, text="Как пользоваться", style="Section.TLabel").grid(
        row=0, column=0, sticky="w", padx=20, pady=(18, 12)
    )
    text = tk.Text(
        help_window, wrap="word", font="TkTextFont", background="#FFFFFF",
        foreground="#23364D", relief="flat", padx=18, pady=16,
        spacing3=12, width=48, height=16,
    )
    text.grid(row=1, column=0, sticky="nsew", padx=(20, 0))
    scroll = ttk.Scrollbar(help_window, command=text.yview)
    scroll.grid(row=1, column=1, sticky="ns", padx=(0, 20))
    text.configure(yscrollcommand=scroll.set)
    text.insert("1.0", (
        "1. Выберите прибор. Проверьте потребляемую мощность в ваттах "
        "по его инструкции — начальное значение приведено для примера.\n\n"
        "2. Введите часы работы в день (0–24), количество дней "
        "(целое число от 1) и тариф в руб./кВт·ч. "
        "Мощность должна быть больше нуля, тариф — не меньше нуля. "
        "Дробные числа можно вводить с точкой или запятой.\n\n"
        "3. Нажмите «Рассчитать» или Enter. Появятся расход энергии "
        "и стоимость. Расчёт сохранится автоматически.\n\n"
        "4. Чтобы сохранить все расчёты в файл, откройте «История» "
        "и нажмите «Экспорт в Excel».\n\n"
        "Результат — примерная оценка: реальный расход зависит от режима работы."
    ))
    text.configure(state="disabled")
    ttk.Button(help_window, text="Понятно", command=help_window.destroy).grid(
        row=2, column=0, columnspan=2, pady=16
    )
    help_window.bind("<Escape>", lambda _event: help_window.destroy())


def main() -> None:
    window = tk.Tk()
    window.title("Энергокалькулятор")
    base_width, base_height = 940, 660
    window.geometry(f"{base_width}x{base_height}")
    window.minsize(base_width, base_height)
    window.configure(background="#EEF3F9")
    window.columnconfigure(0, weight=1)
    window.rowconfigure(1, weight=1)

    family = "Segoe UI" if "Segoe UI" in font.families(window) else "DejaVu Sans"
    ui_fonts = {
        "body": font.Font(window, family=family, size=14),
        "small": font.Font(window, family=family, size=11),
        "section": font.Font(window, family=family, size=16, weight="bold"),
        "title": font.Font(window, family=family, size=26, weight="bold"),
        "number": font.Font(window, family=family, size=24, weight="bold"),
        "heading": font.Font(window, family=family, size=13, weight="bold"),
        "row": font.Font(window, family=family, size=13),
    }
    base_sizes = {key: value.cget("size") for key, value in ui_fonts.items()}
    default_fonts = [font.nametofont(name, root=window) for name in
                     ("TkDefaultFont", "TkTextFont", "TkMenuFont")]
    for named_font in default_fonts:
        named_font.configure(family=family, size=14)
    window.option_add("*TCombobox*Listbox.font", ui_fonts["body"])

    style = ttk.Style(window)
    style.theme_use("clam")
    style.configure(".", font=ui_fonts["body"], foreground="#23364D")
    style.configure("App.TFrame", background="#EEF3F9")
    style.configure("Header.TFrame", background="#183754")
    style.configure("Card.TFrame", background="#FFFFFF")
    style.configure("Result.TFrame", background="#E3EDF9")
    style.configure("Header.TLabel", background="#183754", foreground="#FFFFFF", font=ui_fonts["title"])
    style.configure("HeaderNote.TLabel", background="#183754", foreground="#CBDBEC", font=ui_fonts["small"])
    style.configure("TLabel", background="#EEF3F9")
    style.configure("Section.TLabel", background="#EEF3F9", font=ui_fonts["section"])
    style.configure("Card.TLabel", background="#FFFFFF")
    style.configure("CardTitle.TLabel", background="#FFFFFF", font=ui_fonts["section"])
    style.configure("Muted.TLabel", background="#EEF3F9", foreground="#53677E", font=ui_fonts["small"])
    style.configure("Result.TLabel", background="#E3EDF9", foreground="#334F6D")
    style.configure("ResultTitle.TLabel", background="#E3EDF9", font=ui_fonts["section"])
    style.configure("Number.TLabel", background="#E3EDF9", foreground="#174B8C", font=ui_fonts["number"])
    style.configure("Saved.TLabel", background="#E3EDF9", foreground="#266343", font=ui_fonts["small"])
    style.configure("Error.TLabel", background="#EEF3F9", foreground="#B42335", font=ui_fonts["small"])
    style.configure("TEntry", padding=(8, 5), fieldbackground="#F8FAFD", bordercolor="#B9C9DA")
    style.configure("TCombobox", padding=(8, 5), arrowsize=18)
    style.map("TCombobox", fieldbackground=[("readonly", "#F8FAFD")],
              selectbackground=[("readonly", "#F8FAFD")], selectforeground=[("readonly", "#23364D")])
    style.configure("TButton", padding=(16, 9), background="#E0E9F3", bordercolor="#C6D4E3")
    style.map("TButton", background=[("active", "#CFDEED")])
    style.configure("Primary.TButton", background="#2862B8", foreground="#FFFFFF", bordercolor="#2862B8")
    style.map("Primary.TButton", background=[("active", "#1B4B91"), ("pressed", "#153E79")],
              foreground=[("active", "#FFFFFF")])
    style.configure("TNotebook", background="#EEF3F9", borderwidth=0)
    style.configure("TNotebook.Tab", padding=(24, 10), background="#DDE7F2", foreground="#435A73")
    style.map("TNotebook.Tab", background=[("selected", "#FFFFFF")], foreground=[("selected", "#174B8C")])
    row_font, heading_font = ui_fonts["row"], ui_fonts["heading"]
    style.configure("History.Treeview", font=row_font, background="#FFFFFF", fieldbackground="#FFFFFF",
                    borderwidth=0, rowheight=row_font.metrics("linespace") + 14)
    style.configure("History.Treeview.Heading", font=heading_font, padding=(10, 10),
                    background="#DDE9F6", foreground="#284C73", relief="flat")
    style.map("History.Treeview", background=[("selected", "#CFE1F6")], foreground=[("selected", "#143B67")])
    style.map("History.Treeview.Heading", background=[("active", "#CCDDF1")])

    header = ttk.Frame(window, style="Header.TFrame", padding=(24, 18))
    header.grid(row=0, column=0, sticky="ew")
    header.columnconfigure(0, weight=1)
    ttk.Label(header, text="Энергокалькулятор", style="Header.TLabel").grid(row=0, column=0, sticky="w")
    ttk.Label(header, text="Вариант 12", style="HeaderNote.TLabel").grid(
        row=1, column=0, sticky="w", pady=(4, 0)
    )
    ttk.Button(header, text="Справка", command=lambda: show_help(window)).grid(row=0, column=1, rowspan=2)

    try:
        repository = HistoryRepository(Path(__file__).resolve().parent / "data" / "history.db")
    except (OSError, sqlite3.Error):
        window.withdraw()
        messagebox.showerror("Ошибка", "Не удалось открыть историю. Проверьте права доступа к папке data.")
        window.destroy()
        return

    notebook = ttk.Notebook(window)
    notebook.grid(row=1, column=0, sticky="nsew", padx=20, pady=(16, 20))
    content = ttk.Frame(notebook, padding=20, style="App.TFrame")
    notebook.add(content, text="Расчёт")
    content.columnconfigure(0, weight=1)
    content.columnconfigure(1, weight=1)
    content.rowconfigure(0, weight=1)

    history_tab = ttk.Frame(notebook, padding=16, style="App.TFrame")
    notebook.add(history_tab, text="История")
    history_tab.columnconfigure(0, weight=1)
    history_tab.rowconfigure(1, weight=1)
    toolbar = ttk.Frame(history_tab, style="App.TFrame")
    toolbar.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 14))
    toolbar.columnconfigure(0, weight=1)
    history_count = tk.StringVar(value="История пуста")
    ttk.Label(toolbar, text="История расчётов", style="Section.TLabel").grid(row=0, column=0, sticky="w")
    ttk.Label(toolbar, textvariable=history_count, style="Muted.TLabel").grid(row=1, column=0, sticky="w", pady=(5, 0))
    ttk.Label(toolbar, text="Нажмите заголовок для сортировки ↑↓", style="Muted.TLabel").grid(
        row=2, column=0, columnspan=2, sticky="w", pady=(8, 0)
    )
    columns = ("id", "created_at", "appliance_name", "power_w", "hours_per_day",
               "days", "tariff", "energy_kwh", "cost_rub")
    titles = dict(zip(columns, (
        "№", "Дата и время", "Прибор", "Мощность, Вт", "Часы в день",
        "Дни", "Тариф, руб./кВт·ч", "Энергия, кВт·ч", "Стоимость, руб.",
    )))
    table = ttk.Treeview(history_tab, columns=columns, show="headings", height=8, style="History.Treeview")
    table.tag_configure("even", background="#FFFFFF")
    table.tag_configure("odd", background="#F0F5FB")
    table.grid(row=1, column=0, sticky="nsew")
    vertical = ttk.Scrollbar(history_tab, orient="vertical", command=table.yview)
    vertical.grid(row=1, column=1, sticky="ns")
    horizontal = ttk.Scrollbar(history_tab, orient="horizontal", command=table.xview)
    horizontal.grid(row=2, column=0, sticky="ew")
    table.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
    history_rows = []
    sort_state = {"column": "id", "descending": True}

    def fit_columns() -> None:
        for key in columns:
            heading_width = heading_font.measure(titles[key] + " ▼") + 28
            values_width = max(
                (row_font.measure(table.set(item, key)) + 28 for item in table.get_children()), default=0,
            )
            table.column(key, width=max(heading_width, values_width), minwidth=heading_width,
                         stretch=False, anchor="w" if key in columns[1:3] else "e")

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
            export_directory = Path(__file__).resolve().parent / "exports"
            export_directory.mkdir(parents=True, exist_ok=True)
            file_path = filedialog.asksaveasfilename(
                title="Сохранить всю историю", defaultextension=".xlsx",
                filetypes=[("Книга Excel", "*.xlsx")], initialfile="energy_history.xlsx",
                initialdir=str(export_directory), parent=window,
            )
            if not file_path:
                return
            count = repository.export_excel(file_path)
        except (OSError, sqlite3.Error, ValueError):
            messagebox.showerror("Ошибка экспорта", "Не удалось сохранить файл. Закройте его в Excel "
                                 "и проверьте доступ к выбранной папке.")
            return
        messagebox.showinfo("Экспорт завершён", f"В Excel сохранено расчётов: {count}.")

    ttk.Button(toolbar, text="Экспорт в Excel", style="Primary.TButton", command=export_history).grid(
        row=0, column=1, rowspan=2, sticky="e", padx=(16, 0)
    )
    try:
        refresh_history()
    except (OSError, sqlite3.Error):
        messagebox.showerror("Ошибка", "Не удалось прочитать историю расчётов.")

    form = ttk.Frame(content, padding=20, style="Card.TFrame")
    form.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
    form.columnconfigure(0, weight=1)
    form.columnconfigure(1, weight=0)
    ttk.Label(form, text="Параметры прибора", style="CardTitle.TLabel").grid(
        row=0, column=0, columnspan=2, sticky="w", pady=(0, 18)
    )
    fields = {
        "Прибор": tk.StringVar(value="Утюг"),
        "Мощность, Вт": tk.StringVar(value="2000"),
        "Часы работы в день": tk.StringVar(value="1"),
        "Количество дней": tk.StringVar(value="30"),
        "Тариф, руб./кВт·ч": tk.StringVar(value="6"),
    }
    ttk.Label(form, text="Прибор", style="Card.TLabel").grid(row=1, column=0, columnspan=2, sticky="w")
    selector = ttk.Combobox(form, textvariable=fields["Прибор"], values=list(APPLIANCES),
                            state="readonly", font=ui_fonts["body"], width=23)
    selector.grid(row=2, column=0, columnspan=2, sticky="w", pady=(6, 16))
    for row, (label, variable) in enumerate(list(fields.items())[1:], start=3):
        ttk.Label(form, text=label, style="Card.TLabel").grid(row=row, column=0, sticky="w", padx=(0, 14), pady=8)
        ttk.Entry(form, textvariable=variable, font=ui_fonts["body"], width=9).grid(
            row=row, column=1, sticky="e", pady=8
        )

    result_frame = ttk.Frame(content, padding=20, style="Result.TFrame")
    result_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
    result_frame.columnconfigure(0, weight=1)
    result_text = tk.StringVar(value="Заполните параметры и нажмите «Рассчитать».")
    energy_text = tk.StringVar(value="— кВт·ч")
    cost_text = tk.StringVar(value="— руб.")
    save_text = tk.StringVar()
    error_text = tk.StringVar()
    ttk.Label(result_frame, text="Ваш результат", style="ResultTitle.TLabel").grid(row=0, column=0, sticky="w")
    result_label = ttk.Label(result_frame, textvariable=result_text, style="Result.TLabel", wraplength=260)
    result_label.grid(row=1, column=0, sticky="ew", pady=(14, 20))
    save_label = ttk.Label(result_frame, textvariable=save_text, style="Saved.TLabel", wraplength=260)
    save_label.grid(row=6, column=0, sticky="ew")
    error_label = ttk.Label(content, textvariable=error_text, style="Error.TLabel", wraplength=760)
    error_label.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 0))
    footer = ttk.Label(content, text="Каждый успешный расчёт сохраняется во вкладке «История».",
                       style="Muted.TLabel", wraplength=760)
    footer.grid(row=2, column=0, columnspan=2, sticky="w", pady=(8, 0))

    def clear_result(*_args) -> None:
        result_text.set("Данные изменены. Нажмите «Рассчитать».")
        energy_text.set("— кВт·ч")
        cost_text.set("— руб.")
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
            result = Calculation(appliance, fields["Часы работы в день"].get(),
                                 fields["Количество дней"].get(), fields["Тариф, руб./кВт·ч"].get())
        except ValueError as exc:
            clear_result()
            result_text.set("Проверьте введённые параметры.")
            error_text.set(str(exc))
            return
        error_text.set("")
        result_text.set(f"{result.appliance_name} · {result.power_w:g} Вт\nЗа {result.days:g} дн.")
        energy_text.set(f"{result.energy_kwh:.4f} кВт·ч")
        cost_text.set(f"{result.cost_rub:.2f} руб.")
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
            error_text.set("Расчёт сохранён, но историю не удалось обновить. Перезапустите программу.")

    ttk.Button(form, text="Рассчитать", style="Primary.TButton", command=calculate).grid(
        row=7, column=0, columnspan=2, sticky="ew", pady=(18, 0)
    )
    window.bind("<Return>", calculate)

    resize_state = {"job": None, "scale": 1.0}

    def resize_text() -> None:
        resize_state["job"] = None
        scale = round(min(1.35, max(1.0, min(window.winfo_width() / base_width,
                                            window.winfo_height() / base_height))), 2)
        if scale != resize_state["scale"]:
            resize_state["scale"] = scale
            for key, named_font in ui_fonts.items():
                named_font.configure(size=round(base_sizes[key] * scale))
            for named_font in default_fonts:
                named_font.configure(size=round(14 * scale))
            style.configure("History.Treeview", rowheight=row_font.metrics("linespace") + 14)
            fit_columns()
        result_width = max(200, result_frame.winfo_width() - 40)
        result_label.configure(wraplength=result_width)
        save_label.configure(wraplength=result_width)
        error_label.configure(wraplength=max(400, content.winfo_width() - 40))
        footer.configure(wraplength=max(400, content.winfo_width() - 40))

    def schedule_resize(event) -> None:
        if event.widget is not window:
            return
        if resize_state["job"] is not None:
            window.after_cancel(resize_state["job"])
        resize_state["job"] = window.after(100, resize_text)

    # Минимум учитывает реальную высоту элементов при текущем шрифте и DPI.
    # Эта же высота служит базой масштабирования, чтобы текст не обрезался.
    window.update_idletasks()
    base_height = max(base_height, window.winfo_reqheight() + 16)
    window.minsize(base_width, base_height)
    window.geometry(f"{base_width}x{base_height}")
    window.bind("<Configure>", schedule_resize)
    window.mainloop()


if __name__ == "__main__":
    main()
