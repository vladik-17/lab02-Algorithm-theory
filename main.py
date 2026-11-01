"""Первое окно энергокалькулятора."""

import tkinter as tk
from tkinter import messagebox, ttk


def show_help() -> None:
    messagebox.showinfo(
        "Справка",
        "Энергокалькулятор бытовой техники\n\n"
        "Приложение предназначено для оценки потребления электроэнергии "
        "и стоимости работы утюга, телевизора и стиральной машины.\n\n"
        "Сейчас доступно начальное окно. Расчёт пока недоступен.\n"
        "Размер окна можно менять, растягивая его границы.",
    )


def main() -> None:
    window = tk.Tk()
    window.title("Энергокалькулятор")
    window.geometry("640x400")
    window.minsize(420, 280)
    window.columnconfigure(0, weight=1)
    window.rowconfigure(0, weight=1)

    content = ttk.Frame(window, padding=24)
    content.grid(sticky="nsew")
    content.columnconfigure(0, weight=1)
    content.rowconfigure(2, weight=1)

    ttk.Label(content, text="Бытовая техника", font=("Segoe UI", 22)).grid(
        row=0, column=0, sticky="w", pady=(0, 16)
    )
    description = ttk.Label(
        content,
        text="Расчёт потребления электроэнергии и стоимости работы приборов.\n\n"
        "Расчёт пока недоступен.",
        justify="left",
        wraplength=360,
    )
    description.grid(row=1, column=0, sticky="ew")
    content.bind(
        "<Configure>",
        lambda event: description.configure(wraplength=max(100, event.width - 48)),
    )
    ttk.Button(content, text="Справка", command=show_help).grid(
        row=3, column=0, sticky="w", pady=(16, 0)
    )
    window.mainloop()


if __name__ == "__main__":
    main()
