from src.db_manager import DBManager


def insert_data(data: dict) -> None:
    """Сохраняет данные о работодателях и вакансиях в базу данных.

    Args:
        data (dict): Словарь с данными, содержащий ключи:
            - "employers": список словарей с информацией о работодателях.
            - "vacancies": список словарей с информацией о вакансиях.
    """
    with DBManager() as db:
        db.insert_data(data)
