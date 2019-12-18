import requests
import pytest

host = "http://127.0.0.1:5000/"
headers = {'referer': 'https://stage-app7215168-2ea62ec052e4.pages.vk-apps.com/index.html?vk_access_token_settings=notify&vk_app_id=7217332&vk_are_notifications_enabled=0&vk_is_app_user=1&vk_is_favorite=0&vk_language=ru&vk_platform=mobile_android&vk_ref=other&vk_user_id=87478742&sign=mawhkNkflRJHKqBWvPwmKxnHMIX6txGV9gA0YAiznrE'}


def test_GetMeets():
    r = requests.get(host + 'GetMeets', headers=headers)
    r = r.json()
    r = r[0]

    for key in r:
        print(key)
        #print(r.get(key))
test_GetMeets()
