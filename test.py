import requests
import pytest

host = "http://127.0.0.1:5000/"
headers = {'referer': 'https://stage-app7215168-2ea62ec052e4.pages.vk-apps.com/index.html?vk_access_token_settings=notify&vk_app_id=7217332&vk_are_notifications_enabled=0&vk_is_app_user=1&vk_is_favorite=0&vk_language=ru&vk_platform=mobile_android&vk_ref=other&vk_user_id=87478742&sign=mawhkNkflRJHKqBWvPwmKxnHMIX6txGV9gA0YAiznrE'}


def test_GetMeets():
    r0 = {'id': 402,
          'name': 'Сырки дорогие',
          'description': 'Требуем, понизить цену на сырки ',
          'ownerid': 257140604,
          'owner_name': 'Максим',
          'owner_surname': 'Шапкин',
          'owner_photo': 'https://sun9-48.userapi.com/c851532/v851532382/5361b/56EBG7_AL5A.jpg?ava=1',
          'members_amount': 23,
          'start': '2019-12-29',
          'finish': '2021-01-01',
          'approved': 1,
          'photo': 'https://sun9-13.userapi.com/c206620/v206620089/23db5/u6Z062iPGfU.jpg',
          'ismember': False,
          'isowner': False,
          'isexpired': False}

    r = requests.get(host + 'GetMeets', headers=headers)
    assert r.status_code, 200  # Проверяем, что ответ вообще пришел

    r = r.json()
    r = r[0]

    assert isinstance(r.get('id'), int)
    assert isinstance(r.get('name'), str)
    assert isinstance(r.get('description'), str)
    assert isinstance(r.get('ownerid'), int)
    assert isinstance(r.get('owner_name'), str)
    assert isinstance(r.get('owner_surname'), str)
    assert isinstance(r.get('owner_photo'), str)
    assert isinstance(r.get('members_amount'), int)
    assert isinstance(r.get('start'), str)
    assert isinstance(r.get('finish'), str)
    assert isinstance(r.get('approved'), int)
    assert isinstance(r.get('photo'), str)
    assert isinstance(r.get('ismember'), bool)
    assert isinstance(r.get('isowner'), bool)
    assert isinstance(r.get('isexpired'), bool)


test_GetMeets()
