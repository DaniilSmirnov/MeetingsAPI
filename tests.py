import requests
import pytest

host = "https://vargasoff.ru:8000/"
headers = {
    'referer': 'https://stage-app7215168-2ea62ec052e4.pages.vk-apps.com/index.html?vk_access_token_settings=notify&vk_app_id=7217332&vk_are_notifications_enabled=0&vk_is_app_user=1&vk_is_favorite=0&vk_language=ru&vk_platform=mobile_android&vk_ref=other&vk_user_id=87478742&sign=mawhkNkflRJHKqBWvPwmKxnHMIX6txGV9gA0YAiznrE'}


def test_GetMeets():
    r = requests.get(host + 'GetMeets', headers=headers)
    assert r.status_code == 200, "Запрос не был успешным"  # Проверяем, что ответ вообще пришел

    r = r.json()
    for meet in r:
        assert isinstance(meet.get('id'), int), "Неверный тип поля id"
        assert isinstance(meet.get('name'), str), "Неверный тип поля name"
        assert isinstance(meet.get('description'), str), "Неверный тип поля description"
        assert isinstance(meet.get('ownerid'), int), "Неверный тип поля ownerid"
        assert isinstance(meet.get('owner_name'), str), "Неверный тип поля owner_name"
        assert isinstance(meet.get('owner_surname'), str), "Неверный тип поля owner_surname"
        assert isinstance(meet.get('owner_photo'), str), "Неверный тип поля owner_photo"
        assert isinstance(meet.get('members_amount'), int), "Неверный тип поля members_amount"
        assert isinstance(meet.get('start'), str), "Неверный тип поля start"
        assert isinstance(meet.get('finish'), str), "Неверный тип поля finish"
        assert isinstance(meet.get('approved'), int), "Неверный тип поля approved"
        assert isinstance(meet.get('photo'), str), "Неверный тип поля photo"
        assert isinstance(meet.get('ismember'), bool), "Неверный тип поля ismember"
        assert isinstance(meet.get('isowner'), bool), "Неверный тип поля isowner"
        assert isinstance(meet.get('isexpired'), bool), "Неверный тип поля isexpired"


def test_Auth():
    r = requests.get(host + 'GetMeets')  # делаем запрос без нужного хедера
    assert r.status_code == 403, "Авторизация не сработала"  # Проверяем код ответа


def isFirst():
    r = requests.get(host + 'isFirst', headers=headers)
    r = r.json()
    assert r == True, "Для известного юзера пришел False"


test_GetMeets()
test_Auth()
