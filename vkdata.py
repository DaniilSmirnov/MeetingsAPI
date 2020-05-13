import vk_api
from tokens import vk_token


def get_user_data(id):
    vk = get_service_vk()
    return vk.users.get(user_ids=id, fields='first_name,last_name,photo_100', lang='ru')


def get_group_data(id):
    vk = get_service_vk()
    return vk.groups.getById(group_id=id, fields='photo_100', lang='ru')


def get_service_vk():
    vk_session = vk_api.VkApi(token=vk_token)
    vk = vk_session.get_api()
    return vk


def send_log(text):
    vk = get_vk()
    vk.messages.send(
        peer_id=2000000003,
        message=text,
        random_id=random.randint(0, 2 ** 64))


def send_error(text):
    vk = get_vk()
    vk.messages.send(
        peer_id=2000000002,
        message="Митинги \n" + text,
        random_id=random.randint(0, 2 ** 64))