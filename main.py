import time

import requests
from environs import Env
from terminaltables import AsciiTable


PROGRAM_LANGUAGES = ['Java', 'Javascript', 'Python', 'TypeScript', 'Swift', 'Scala', 'Objective-C', 'Shell', 'Go', 'C',
                     'PHP', 'Ruby']


def predict_salary(salary_from, salary_to):
    average_salary = 0
    if salary_from > 0 and salary_to > 0:
        average_salary = int((salary_from+salary_to) / 2)
    elif salary_from > 0:
        average_salary = int(salary_from * 1.2)
    elif salary_to > 0:
        average_salary = int(salary_to * 0.8)
    return average_salary


def predict_rub_salary_hh(vacancy):
    hh_rub_salary = 0
    if vacancy['salary'] and vacancy["salary"]["currency"] == "RUR":
        salary_from = vacancy["salary"]["from"] or 0
        salary_to = vacancy["salary"]["to"] or 0
        hh_rub_salary = predict_salary(salary_from, salary_to)
    return hh_rub_salary


def predict_rub_salary_sj(vacancy):
    sj_rub_salary = 0
    if vacancy["currency"] == "rub":
        salary_from = vacancy["payment_from"] or 0
        salary_to = vacancy["payment_to"] or 0
        sj_rub_salary = predict_salary(salary_from, salary_to)
    return sj_rub_salary


def get_vacancies_hh(program_language):
    hh_url = "https://api.hh.ru/vacancies"
    page = 0
    page_number = 1
    vacancies = []
    while page < page_number:
        headers = {'User-Agent': 'HH-User-Agent'}
        params = {
            "text": "программист" + program_language,
            "area": 1,
            "currency": "RUR",
            "page": page
        }
        response = requests.get(hh_url, headers=headers, params=params)
        time.sleep(0.5)
        page += 1
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError:
            continue
        page_paylord = response.json()
        vacancies.extend(page_paylord["items"])
        page_number = page_paylord["pages"] - 1
    return vacancies


def get_vacancies_sj(program_language, secret_key):
    sj_url = "https://api.superjob.ru/2.0/vacancies/"
    page = 0
    next_page = True
    vacancies = []
    while next_page:
        headers = {
            "X-Api-App-Id": secret_key
        }
        params = {
            "keyword": program_language,
            "catalogues": 48,
            "town": 4,
            "page": page
        }
        responce = requests.get(sj_url, headers=headers, params=params)
        page += 1
        time.sleep(0.5)
        try:
            responce.raise_for_status()
        except requests.exceptions.HTTPError:
            continue
        page_paylord = responce.json()
        vacancies.extend(page_paylord["objects"])
        next_page = page_paylord["more"]
    return vacancies


def get_hh_stats(vacancies):
    if vacancies:
        number_of_vacancies = len(vacancies)
        salaries = [predict_rub_salary_hh(vacancy) for vacancy in vacancies if predict_rub_salary_hh(vacancy) != 0]
        vacancies_processed = len(salaries)
        average_salary = int(sum(salaries)/vacancies_processed) if vacancies_processed > 0 else 0
        hh_stats = {
            "vacancies_found": number_of_vacancies,
            "vacancies_processed": vacancies_processed,
            "average_salary": average_salary
        }
        return hh_stats
    else:
        return {
            "vacancies_found": 0,
            "vacancies_processed": 0,
            "average_salary": 0
        }


def get_sj_stats(vacancies):
    if vacancies:
        number_of_vacancies = len(vacancies)
        salaries = [predict_rub_salary_sj(vacancy) for vacancy in vacancies if predict_rub_salary_sj(vacancy) != 0]
        vacancies_processed = len(salaries)
        average_salary = int(sum(salaries)/vacancies_processed) if vacancies_processed > 0 else 0
        hh_stats = {
            "vacancies_found": number_of_vacancies,
            "vacancies_processed": vacancies_processed,
            "average_salary": average_salary
        }
        return hh_stats
    else:
        return {
            "vacancies_found": 0,
            "vacancies_processed": 0,
            "average_salary": 0
        }


def get_stats_program_languages_hh(program_languages):
    stat = {}
    for program_language in program_languages:
        vacancies = get_vacancies_hh(program_language)
        stat[program_language] = get_hh_stats(vacancies)
    return stat


def get_stats_program_languages_sj(program_languages, secret_key):
    stat = {}
    for program_language in program_languages:
        vacancies = get_vacancies_sj(program_language, secret_key)
        stat[program_language] = get_sj_stats(vacancies)
    return stat


def get_tabular_statistics(title, stats):


    table_data = (
        ("Язык программирования", "Вакансий найдено", "Вакансий обработано", "Средняя зарплата"),
        (get_stats_program_languages_sj(PROGRAM_LANGUAGES, secret_key_sj).keys(),)
    )
    table_instance = AsciiTable(table_data, title)
    table_instance.justify_columns[4] = 'right'
    print(table_instance)


def main():
    env = Env()
    env.read_env()
    secret_key_sj = env.str("SECRET_KEY_SJ")
    title_sj = "SuperJob Moscow"
    print(get_tabular_statistics(title_sj, get_stats_program_languages_sj(PROGRAM_LANGUAGES, secret_key_sj)))
    print()
    title_hh = "HeadHunter Moscow"
    print(get_tabular_statistics(title_hh, get_stats_program_languages_hh(PROGRAM_LANGUAGES)))


if __name__ == "__main__":
    main()