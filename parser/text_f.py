import requests

perem = []
for i in range(40):
    url = f'https://raw.githubusercontent.com/etspring/pdd_russia/refs/heads/master/questions/A_B/tickets/Билет%20{i+1}.json'
    response = requests.get(url)

    # Проверяем статус ответа
    if response.status_code == 200:
        try:
            data = response.json()  # Пробуем разобрать как JSON
            perem.append(data)
        except requests.exceptions.JSONDecodeError:
            print(f"Ошибка декодирования JSON для {url}")
            print(f"Ответ сервера: {response.text[:200]}")  # Выведет первые 200 символов
    else:
        print(f"Ошибка {response.status_code} при получении {url}")

print(f"Успешно загружено {len(perem)} файлов")