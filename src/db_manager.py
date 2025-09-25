import psycopg2
from typing import Any
from src.config import load_config


class DBManager:
    """Класс для управления базой данных вакансий и работодателей."""

    def __init__(self) -> None:
        """Инициализация подключения к базе данных."""
        config = load_config()
        self.conn = psycopg2.connect(
            dbname="hh_db",
            user=config["user"],
            password=config["password"],
            host=config["host"],
            port=config["port"],
        )
        self.conn.autocommit = True

    def __enter__(self) -> "DBManager":
        """Поддержка контекстного менеджера (`with DBManager() as db:`)."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Закрывает соединение при выходе из контекстного менеджера."""
        self.close()

    def insert_data(self, data: dict[str, list[dict[str, Any]]]) -> None:
        """Загружает данные о работодателях и вакансиях в БД.

        Args:
            data (dict[str, list[dict[str, Any]]]): словарь с данными,
                где ключи: "employers" и "vacancies".
        """
        with self.conn.cursor() as cur:
            # --- работодатели ---
            for emp in data["employers"]:
                cur.execute(
                    """
                    INSERT INTO employers (employer_id, name, url, open_vacancies)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (employer_id) DO NOTHING
                    """,
                    (
                        emp["employer_id"],
                        emp["name"],
                        emp["url"],
                        emp["open_vacancies"],
                    ),
                )

            # --- вакансии ---
            for vac in data["vacancies"]:
                salary_from = vac["salary_from"]
                salary_to = vac["salary_to"]
                currency = vac["salary_currency"]

                # берём курс для валюты
                cur.execute(
                    "SELECT rate FROM currency_rates WHERE code = %s", (currency,)
                )
                rate_row = cur.fetchone()
                rate = float(rate_row[0]) if rate_row else 1.0

                # считаем зарплату в рублях
                if salary_from or salary_to:
                    salary_rub = (
                        ((salary_from or salary_to) + (salary_to or salary_from))
                        / 2
                        / rate
                    )
                else:
                    salary_rub = None
                cur.execute(
                    """
                    INSERT INTO vacancies (
                        vacancy_id, employer_id, name,
                        salary_from, salary_to, salary_currency, salary_rub, url
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (vacancy_id) DO NOTHING
                    """,
                    (
                        vac["vacancy_id"],
                        vac["employer_id"],
                        vac["name"],
                        salary_from,
                        salary_to,
                        currency,
                        salary_rub,
                        vac["url"],
                    ),
                )

    def get_companies_and_vacancies_count(self) -> list[tuple[str, int, float | None]]:
        """Возвращает список компаний с количеством вакансий и средней зарплатой.

        Returns:
            list[tuple[str, int, float | None]]: список кортежей вида
                (название компании, количество вакансий, средняя зарплата в рублях).
        """
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT e.name,
                       COUNT(v.vacancy_id),
                       ROUND(AVG(v.salary_rub), 2)
                FROM employers e
                LEFT JOIN vacancies v ON e.employer_id = v.employer_id
                GROUP BY e.name
                ORDER BY AVG(v.salary_rub) DESC, COUNT(v.vacancy_id) DESC NULLS LAST
                """
            )
            return cur.fetchall()

    def get_all_vacancies(
        self,
    ) -> list[
        tuple[str, str, float | None, float | None, str | None, float | None, str]
    ]:
        """Возвращает все вакансии с указанием компании и зарплаты.

        Returns:
            list[tuple[str, str, float | None, float | None, str | None, float | None, str]]:
                Список кортежей:
                (название компании, вакансия, зарплата от, зарплата до, валюта, средняя зарплата, ссылка).
        """
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT e.name, v.name, v.salary_from, v.salary_to,
                       v.salary_currency, v.salary_rub, v.url
                FROM vacancies v
                JOIN employers e ON v.employer_id = e.employer_id
                ORDER BY v.salary_rub DESC NULLS LAST
                """
            )
            return cur.fetchall()

    def get_avg_salary(self) -> float | None:
        """Вычисляет среднюю зарплату по всем вакансиям в рублях.

        Returns:
            float | None: среднее значение зарплаты (в рублях) или None.
        """
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT AVG(salary_rub) FROM vacancies WHERE salary_rub IS NOT NULL"
            )
            return cur.fetchone()[0]

    def get_vacancies_with_higher_salary(
        self,
    ) -> list[
        tuple[str, str, float | None, float | None, str | None, float | None, str]
    ]:
        """Возвращает вакансии, где зарплата (в рублях) выше средней.

        Returns:
            list[tuple[str, str, float | None, float | None, str | None, float | None, str]]:
                Список кортежей:
                (название компании, вакансия, зарплата от, зарплата до, валюта, средняя зарплата, ссылка).
        """
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT v.name, e.name, v.salary_from, v.salary_to,
                       v.salary_currency, v.salary_rub, v.url
                FROM vacancies v
                JOIN employers e ON v.employer_id = e.employer_id
                WHERE v.salary_rub > (SELECT AVG(salary_rub) FROM vacancies WHERE salary_rub IS NOT NULL)
                ORDER BY v.salary_rub DESC
                """
            )
            return cur.fetchall()

    def get_vacancies_with_keyword(
        self, keyword: str
    ) -> list[
        tuple[str, str, float | None, float | None, str | None, float | None, str]
    ]:
        """Ищет вакансии по ключевому слову в названии.

        Args:
            keyword (str): слово для поиска.

        Returns:
            list[tuple[str, str, float | None, float | None, str | None, float | None, str]]:
                Список кортежей:
                (название компании, вакансия, зарплата от, зарплата до, валюта, средняя зарплата, ссылка).
        """
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT v.name, e.name, v.salary_from, v.salary_to,
                       v.salary_currency, v.salary_rub, v.url
                FROM vacancies v
                JOIN employers e ON v.employer_id = e.employer_id
                WHERE v.name ILIKE %s
                ORDER BY v.salary_rub DESC NULLS LAST
                """,
                (f"%{keyword}%",),
            )
            return cur.fetchall()

    def close(self) -> None:
        """Закрывает соединение с базой данных."""
        self.conn.close()
