import vk_api
from tokens import vk_token

vk_session = vk_api.VkApi(token=vk_token)
vk = vk_session.get_api()


def get_user_data(id):
    return vk.users.get(user_ids=id, fields='first_name,last_name,photo_100', lang='ru')


def get_group_data(id):
    return vk.groups.getById(group_id=id, fields='photo_100', lang='ru')
