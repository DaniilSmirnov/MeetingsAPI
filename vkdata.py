import vk_api

token = '239e8c8b239e8c8b239e8c8b6223f0ac3f2239e239e8c8b7e480a25ad6237c98b649b61'
vk_session = vk_api.VkApi(token=token)
vk = vk_session.get_api()


def get_user_data(id):
    response = (vk.users.get(user_ids=id, fields='first_name,last_name,photo_100', lang='ru'))
    return response


def notify(id, name):
    try:
        vk.secure.sendNotification(user_id=id, message='Ваш митинг ' + name + ' прошел модерацию' )
    except BaseException as e:
        print(e)
