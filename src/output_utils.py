from tabulate import tabulate
from typing import Any


def _print_paginated(
    rows: list[tuple[Any, ...]], headers: list[str], title: str, limit: int = 10
) -> None:
    """Форматированный постраничный вывод с управлением через Enter/q."""
    print(f"\n{title}")
    if not rows:
        print("Нет данных.")
        return

    total = len(rows)
    index = 0

    while index < total:
        chunk = rows[index : index + limit]
        print(
            tabulate(
                chunk,
                headers=headers,
                tablefmt="fancy_grid",
                showindex=range(index + 1, index + len(chunk) + 1),
            )
        )

        index += limit
        print(f"Показано {min(index, total)} из {total} строк.")

        if index >= total:
            break

        # меню управления
        while True:
            choice = input("[Enter] продолжить | [q] выход: ").strip().lower()
            if choice == "q":
                print("👋 Выход из списка")
                return
            elif choice == "":  # просто Enter
                break
            else:
                print("❓ Нажмите Enter для продолжения или 'q' для выхода")


def print_companies(
    companies: list[tuple[str, int, float | None]], limit: int = 10
) -> None:
    """Выводит список компаний и количество их вакансий."""
    headers = ["Компания", "Количество вакансий", "Средняя зарплата в RUB"]
    _print_paginated(companies, headers, "📊 Компании и количество вакансий:", limit)


def print_vacancies(
    vacancies: list[
        tuple[str, str, float | None, float | None, str | None, float | None, str]
    ],
    limit: int = 10,
) -> None:
    """Выводит список вакансий с зарплатой и ссылкой."""
    headers = [
        "Компания",
        "Вакансия",
        "От",
        "До",
        "Валюта",
        "Средняя зарплата в RUB",
        "Ссылка",
    ]
    _print_paginated(vacancies, headers, "💼 Все вакансии:", limit)


def print_avg_salary(avg: float | None) -> None:
    """Выводит среднюю зарплату по всем вакансиям."""
    print("\n💰 Средняя зарплата:")
    if avg:
        print(f"{avg:,.0f} руб.".replace(",", " "))
    else:
        print("Нет данных для расчета.")


def print_higher_salary_vacancies(
    vacancies: list[
        tuple[str, str, float | None, float | None, str | None, float | None, str]
    ],
    limit: int = 10,
) -> None:
    """Выводит вакансии, где зарплата выше средней."""
    headers = [
        "Вакансия",
        "Компания",
        "От",
        "До",
        "Валюта",
        "Средняя зарплата в RUB",
        "Ссылка",
    ]
    _print_paginated(vacancies, headers, "⬆️ Вакансии с зарплатой выше средней:", limit)


def print_keyword_vacancies(
    vacancies: list[
        tuple[str, str, float | None, float | None, str | None, float | None, str]
    ],
    keyword: str,
    limit: int = 10,
) -> None:
    """Выводит вакансии, найденные по ключевому слову."""
    headers = [
        "Вакансия",
        "Компания",
        "От",
        "До",
        "Валюта",
        "Средняя зарплата в RUB",
        "Ссылка",
    ]
    title = f"🔎 Вакансии по ключевому слову '{keyword}':"
    _print_paginated(vacancies, headers, title, limit)
