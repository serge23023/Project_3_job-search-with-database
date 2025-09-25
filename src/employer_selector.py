import requests
from typing import List

# Список работодателей по умолчанию (проверенные ID)
DEFAULT_EMPLOYERS: List[tuple[str, str]] = [
    ("3529", "Сбер"),
    ("1740", "Яндекс"),
    ("78638", "Т-Банк"),
    ("2748", "ПАО Ростелеком"),
    ("3776", "МТС"),
    ("4181", "Банк ВТБ (ПАО)"),
    ("1122462", "Skyeng"),
    ("39305", "Газпром нефть"),
    ("84585", "Авито"),
    ("87021", "Wildberries"),
]


def search_employer_by_name(name: str) -> list[dict]:
    """Ищет работодателей по названию (только с вакансиями)."""
    url = "https://api.hh.ru/employers"
    params = {"text": name, "per_page": 10, "only_with_vacancies": True}
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    return resp.json()["items"]


def select_one_employer(name: str, default_id: str | None = None) -> str | None:
    """
    Выполняет поиск и позволяет пользователю выбрать работодателя.

    Args:
        name: Название компании.
        default_id: ID по умолчанию, если выбор не сделан.

    Returns:
        ID выбранной компании или default_id.
    """
    results = search_employer_by_name(name)
    if not results:
        print(f"❌ Не найдено активных компаний для '{name}'")
        return default_id

    print(f"\n🔎 Найдено совпадений для '{name}':")
    for i, emp in enumerate(results, start=1):
        print(f"{i}. {emp['name']} (ID {emp['id']}, вакансий: {emp['open_vacancies']})")

    choice = input(
        "Введите номер компании (Enter = взять из списка по умолчанию): "
    ).strip()
    if choice.isdigit() and 1 <= int(choice) <= len(results):
        return results[int(choice) - 1]["id"]

    return default_id


def choose_employer() -> list[str]:
    """
    Запрашивает у пользователя список компаний.
    Если выбрано меньше 10, добавляет недостающие из DEFAULT_EMPLOYERS.
    """
    selected_ids: list[str] = []

    raw_input = input(
        "Введите названия или ID компаний через запятую (например: Сбер, Яндекс, 3529): "
    ).strip()
    company_inputs = [c.strip() for c in raw_input.split(",") if c.strip()]

    for value in company_inputs:
        if value.isdigit():
            # пользователь ввёл ID напрямую
            emp_id = value
            print(f"✅ Использован ID компании: {emp_id}")
        else:
            # пользователь ввёл название → ищем
            emp_id = select_one_employer(value)

        if emp_id and emp_id not in selected_ids:
            selected_ids.append(emp_id)

    # добираем компаниями из DEFAULT_EMPLOYERS до 10
    if len(selected_ids) < 10:
        print(
            "\nℹ️ Добавляем компании из списка по умолчанию, чтобы получилось минимум 10..."
        )
        for def_id, name in DEFAULT_EMPLOYERS:
            if def_id not in selected_ids:
                selected_ids.append(def_id)
                print(f"✅ Добавлен {name}: ID {def_id}")
            if len(selected_ids) >= 10:
                break

    print(f"\n📊 Итоговый список работодателей ({len(selected_ids)}): {selected_ids}")
    return selected_ids
