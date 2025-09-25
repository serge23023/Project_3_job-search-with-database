from src.api_hh import HeadHunterAPI
from src.currency import update_currency_rates
from src.db_setup import create_database, create_tables
from src.loader import insert_data
from src.db_manager import DBManager
from src.employer_selector import choose_employer
from src.output_utils import (
    print_companies, print_vacancies,
    print_avg_salary, print_higher_salary_vacancies, print_keyword_vacancies
)


def main() -> None:
    """Точка входа в приложение.

    Последовательно выполняет шаги:
    1. Создаёт базу данных и таблицы.
    2. Загружает курсы валют.
    3. Запрашивает список работодателей у пользователя (или использует дефолтный).
    4. Скачивает данные о работодателях и вакансиях с hh.ru.
    5. Сохраняет данные в БД.
    6. Предоставляет интерфейс для работы с БД:
       - список компаний и количество вакансий,
       - все вакансии,
       - средняя зарплата,
       - вакансии выше средней,
       - вакансии по ключевому слову.
    """
    # Создаём БД и таблицы
    create_database()
    create_tables()
    update_currency_rates()

    # выбор работодателей
    employers = choose_employer()

    # Скачиваем данные и загружаем в БД
    hh = HeadHunterAPI(employers)
    data = hh.collect_data()
    insert_data(data)

    # Работа через DBManager
    with DBManager() as db:
        limit = 15
        print_companies(db.get_companies_and_vacancies_count(), limit=limit)
        print_vacancies(db.get_all_vacancies(), limit=limit)
        print_avg_salary(db.get_avg_salary())
        print_higher_salary_vacancies(db.get_vacancies_with_higher_salary(), limit=limit)
        keyword = "Python"
        print_keyword_vacancies(db.get_vacancies_with_keyword(keyword), keyword, limit=limit)


if __name__ == "__main__":
    main()
