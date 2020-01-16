import vk_api


vk_session = vk_api.VkApi(token='239e8c8b239e8c8b239e8c8b6223f0ac3f2239e239e8c8b7e480a25ad6237c98b649b61')
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

response = vk.secure.setCounter(user_id=87478742, counter=-9)
print(response)