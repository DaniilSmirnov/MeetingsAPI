import vk_api
import requests


#response = requests.get('https://oauth.vk.com/access_token?client_id=7217332&client_secret=kF0Pz974mrpDRYvUStPa&v=5.103&grant_type=client_credentials')
#response = response.json()
#print(response)
#token = response.get('access_token')
#vk_session = vk_api.VkApi(token=token)
vk_session = vk_api.VkApi(token='0f16c5990f16c5990f16c599570f78e52d00f160f16c59952fd11369af29f53b2417ef0')
vk = vk_session.get_api()


def get_user_data(id):
    response = vk.users.get(user_ids=id, fields='first_name,last_name,photo_100', lang='ru')
    return response


def notify(id, name):
    try:
        vk.secure.sendNotification(user_id=id, message='Ваш митинг ' + name + ' прошел модерацию', client_secret='kF0Pz974mrpDRYvUStPa')
    except BaseException as e:
        print(e)


def get_group_data(id):
    response = vk.groups.getById(group_id=id, fields='photo_100', lang='ru')
    print(response)

