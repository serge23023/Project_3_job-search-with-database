import random
import time
from datetime import datetime, timedelta
from typing import Any

import requests


class HeadHunterAPI:
    BASE_URL = "https://api.hh.ru"

    def __init__(self, employers: list[str]) -> None:
        self.employers = employers
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "Mozilla/5.0 (compatible; HH-Parser/1.0)"}
        )

    def _get(self, url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Выполняет GET-запрос с retry, throttling и backoff."""
        retries = 8
        base_delay = 0.2  # базовая задержка между запросами

        for attempt in range(retries):
            try:
                response = self.session.get(url, params=params)

                # если временные ошибки или блокировка
                if response.status_code in (500, 502, 503, 504, 429, 403):
                    wait = (2**attempt) + random.random()
                    print(
                        f"⚠️ Ошибка {response.status_code} при запросе {url}, "
                        f"повтор через {wait:.1f} сек..."
                    )
                    time.sleep(wait)
                    continue

                response.raise_for_status()
                time.sleep(base_delay)  # пауза между успешными запросами
                return response.json()

            except requests.RequestException as e:
                wait = (2**attempt) + random.random()
                print(f"⚠️ Ошибка {e}, повтор через {wait:.1f} сек...")
                time.sleep(wait)

        raise RuntimeError(
            f"❌ Не удалось получить данные после {retries} попыток: {url}"
        )

    def get_employer(self, employer_id: str) -> dict[str, Any]:
        """Получение информации о работодателе по id."""
        url = f"{self.BASE_URL}/employers/{employer_id}"
        return self._get(url)

    def get_vacancies(
        self, employer_id: str, employer_name: str, found: int
    ) -> list[dict[str, Any]]:
        url = f"{self.BASE_URL}/vacancies"
        vacancies = []
        seen_ids = set()

        # 1. Первая партия (до 2000, без интервалов)
        for page in range(20):
            params = {
                "employer_id": employer_id,
                "per_page": 100,
                "page": page,
                "order_by": "publication_time",
            }
            data = self._get(url, params)
            items = data.get("items", [])
            if not items:
                break
            for item in items:
                if item["id"] not in seen_ids:
                    vacancies.append(item)
                    seen_ids.add(item["id"])

        if len(vacancies) >= found or not vacancies:
            return vacancies

        print(f"🔎 {employer_name}: собрано {len(vacancies)} / {found}")

        # 2. Дальше идём по времени
        last_date = vacancies[-1]["published_at"]
        date_to = datetime.fromisoformat(last_date.replace("Z", "+00:00"))

        step = timedelta(days=30)
        min_step = timedelta(minutes=30)  # минимальный шаг
        max_step = timedelta(days=90)

        while len(vacancies) < found:
            remaining = found - len(vacancies)

            # если остаток меньше 2000 → берём max_days и собираем хвост
            if remaining <= 2000:
                date_from = date_to - max_step
                probe_params = {
                    "employer_id": employer_id,
                    "per_page": 1,
                    "page": 0,
                    "order_by": "publication_time",
                    "date_from": date_from.isoformat(),
                    "date_to": date_to.isoformat(),
                }
                probe_data = self._get(url, probe_params)
                interval_found = probe_data.get("found", 0)

                if interval_found > 2000 and step > min_step:
                    step = step / 2
                    continue

                for page in range(min(20, probe_data.get("pages", 0))):
                    params = {
                        "employer_id": employer_id,
                        "per_page": 100,
                        "page": page,
                        "order_by": "publication_time",
                        "date_from": date_from.isoformat(),
                        "date_to": date_to.isoformat(),
                    }
                    data = self._get(url, params)
                    items = data.get("items", [])
                    if not items:
                        break
                    for item in items:
                        if item["id"] not in seen_ids:
                            vacancies.append(item)
                            seen_ids.add(item["id"])
                break

            # пробный запрос
            date_from = date_to - step
            probe_params = {
                "employer_id": employer_id,
                "per_page": 1,
                "page": 0,
                "order_by": "publication_time",
                "date_from": date_from.isoformat(),
                "date_to": date_to.isoformat(),
            }
            probe_data = self._get(url, probe_params)
            interval_found = probe_data.get("found", 0)

            if interval_found > 2000 and step > min_step:
                step = step / 2
                continue

            if interval_found < 1500 and step < max_step:
                step = step * 1.5
                continue

            # если 1–2000 → сразу собираем
            for page in range(min(20, probe_data.get("pages", 0))):
                params = {
                    "employer_id": employer_id,
                    "per_page": 100,
                    "page": page,
                    "order_by": "publication_time",
                    "date_from": date_from.isoformat(),
                    "date_to": date_to.isoformat(),
                }
                data = self._get(url, params)
                items = data.get("items", [])
                if not items:
                    break
                for item in items:
                    if item["id"] not in seen_ids:
                        vacancies.append(item)
                        seen_ids.add(item["id"])

            print(f"🔎 {employer_name}: собрано {len(vacancies)} / {found}")

            # смещаем окно назад
            date_to = date_from + timedelta(seconds=1)

        vacancies = list({v["id"]: v for v in vacancies}.values())

        return vacancies

    def collect_data(self) -> dict[str, list[dict[str, Any]]]:
        """Загрузка работодателей и их вакансий."""
        data: dict[str, list[dict[str, Any]]] = {"employers": [], "vacancies": []}

        for emp_id in self.employers:
            employer = self.get_employer(emp_id)
            if not employer:
                print(f"❌ Работодатель {emp_id} не найден")
                continue

            emp_name = employer["name"]
            declared_open = employer.get("open_vacancies", 0)

            # сначала делаем пробный запрос, чтобы узнать found
            url = f"{self.BASE_URL}/vacancies"
            probe_params = {"employer_id": emp_id, "per_page": 1}
            probe_data = self._get(url, probe_params)
            found = probe_data.get("found", 0)

            vacancies = self.get_vacancies(emp_id, emp_name, found)

            data["employers"].append(
                {
                    "employer_id": employer["id"],
                    "name": emp_name,
                    "url": employer["alternate_url"],
                    "open_vacancies": found,  # сохраняем именно то, что реально вернул API
                }
            )

            for vac in vacancies:
                salary = vac.get("salary") or {}
                currency = salary.get("currency")
                if currency == "RUR":
                    currency = "RUB"

                data["vacancies"].append(
                    {
                        "vacancy_id": vac["id"],
                        "employer_id": emp_id,
                        "name": vac["name"],
                        "salary_from": salary.get("from"),
                        "salary_to": salary.get("to"),
                        "salary_currency": currency,
                        "url": vac["alternate_url"],
                    }
                )
            if declared_open and declared_open != found:
                print(
                    f"⚠️ У работодателя {emp_name} заявлено {declared_open} вакансий, "
                    f"но API вернул {found}"
                )
            else:
                print(
                    f"✅ {emp_name}: собрано {len(vacancies)} / {found} (заявлено {declared_open})"
                )
        return data
