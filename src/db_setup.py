import psycopg2
from src.config import load_config


def create_database() -> None:
    """Создаёт базу данных hh_db, если она ещё не существует."""
    config = load_config()
    conn = psycopg2.connect(
        dbname="postgres",
        user=config["user"],
        password=config["password"],
        host=config["host"],
        port=config["port"],
    )
    conn.autocommit = True
    cur = conn.cursor()

    cur.execute("SELECT 1 FROM pg_database WHERE datname = 'hh_db'")
    exists = cur.fetchone()

    if not exists:
        cur.execute("CREATE DATABASE hh_db")
        print("✅ База данных hh_db создана")
    else:
        print("⚠️ База данных hh_db уже существует — пропускаем создание")

    cur.close()
    conn.close()


def create_tables() -> None:
    """Создаёт таблицы employers, vacancies и currency_rates (или очищает, если структура совпадает)."""
    config = load_config()
    conn = psycopg2.connect(
        dbname="hh_db",
        user=config["user"],
        password=config["password"],
        host=config["host"],
        port=config["port"],
    )
    cur = conn.cursor()

    # Эталонные CREATE TABLE
    employers_def = """
        CREATE TABLE employers (
            employer_id VARCHAR(50) PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            url TEXT NOT NULL,
            open_vacancies INT
        )
    """
    vacancies_def = """
        CREATE TABLE vacancies (
            vacancy_id VARCHAR(50) PRIMARY KEY,
            employer_id VARCHAR(50) REFERENCES employers(employer_id) ON DELETE CASCADE,
            name VARCHAR(255) NOT NULL,
            salary_from BIGINT,
            salary_to BIGINT,
            salary_currency VARCHAR(3),
            salary_rub NUMERIC(14,2),
            url TEXT NOT NULL
        )
    """
    currency_rates_def = """
        CREATE TABLE currency_rates (
            code VARCHAR(3) PRIMARY KEY,
            rate NUMERIC(14,6) NOT NULL
        )
    """

    def table_exists(table_name: str) -> bool:
        """Проверяет, существует ли таблица в схеме public."""
        cur.execute(
            """
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = %s
            )
            """,
            (table_name,),
        )
        return cur.fetchone()[0]

    def table_structure_matches(
        table_name: str, expected_columns: list[tuple[str, str]]
    ) -> bool:
        """Сравнивает структуру таблицы с эталонным списком колонок."""
        cur.execute(
            """
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = %s
            ORDER BY ordinal_position
            """,
            (table_name,),
        )
        actual = [(row[0], row[1]) for row in cur.fetchall()]
        return actual == expected_columns

    # employers
    if table_exists("employers"):
        if table_structure_matches(
            "employers",
            [
                ("employer_id", "character varying"),
                ("name", "character varying"),
                ("url", "text"),
                ("open_vacancies", "integer"),
            ],
        ):
            cur.execute("TRUNCATE TABLE employers RESTART IDENTITY CASCADE")
            print("🔄 Таблица employers очищена (структура совпала)")
        else:
            cur.execute("DROP TABLE employers CASCADE")
            cur.execute(employers_def)
            print("♻️ Таблица employers пересоздана (структура изменилась)")
    else:
        cur.execute(employers_def)
        print("✅ Таблица employers создана")

    # vacancies
    if table_exists("vacancies"):
        if table_structure_matches(
            "vacancies",
            [
                ("vacancy_id", "character varying"),
                ("employer_id", "character varying"),
                ("name", "character varying"),
                ("salary_from", "bigint"),
                ("salary_to", "bigint"),
                ("salary_currency", "character varying"),
                ("salary_rub", "numeric"),
                ("url", "text"),
            ],
        ):
            cur.execute("TRUNCATE TABLE vacancies RESTART IDENTITY CASCADE")
            print("🔄 Таблица vacancies очищена (структура совпала)")
        else:
            cur.execute("DROP TABLE vacancies CASCADE")
            cur.execute(vacancies_def)
            print("♻️ Таблица vacancies пересоздана (структура изменилась)")
    else:
        cur.execute(vacancies_def)
        print("✅ Таблица vacancies создана")

    # currency_rates
    if table_exists("currency_rates"):
        if table_structure_matches(
            "currency_rates",
            [
                ("code", "character varying"),
                ("rate", "numeric"),
            ],
        ):
            cur.execute("TRUNCATE TABLE currency_rates RESTART IDENTITY CASCADE")
            print("🔄 Таблица currency_rates очищена (структура совпала)")
        else:
            cur.execute("DROP TABLE currency_rates CASCADE")
            cur.execute(currency_rates_def)
            print("♻️ Таблица currency_rates пересоздана (структура изменилась)")
    else:
        cur.execute(currency_rates_def)
        print("✅ Таблица currency_rates создана")

    conn.commit()
    cur.close()
    conn.close()
