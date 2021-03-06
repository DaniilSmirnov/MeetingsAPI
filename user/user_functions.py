from modules.database import get_cnx, get_value
from modules.vkdata import get_user_data, get_group_data


def get_id(_id):
    launch_params = request.headers.get('x-vk')

    launch_params = dict(parse_qsl(urlparse(launch_params).query, keep_blank_values=True))
    return launch_params.get('vk_user_id')


def get_user(_id):
    response = {}

    response.update({'is_first': is_first(_id)})

    return response


def is_first(_id):
    cnx, cursor = get_cnx()

    data = (_id,)

    query = 'select count(idmembers) from members where idmembers = %s;'
    cursor.execute(query, data)

    return get_value(cursor) == 0


def create_user():
    cnx, cursor = get_cnx()

    data = (_id,)

    query = 'insert into members values(%s, default);'
    cursor.execute(query, data)
    cnx.commit()


def get_owner(_id):
    meet = {}
    if _id > 0:
        meet.update({'ownerId': _id,
                     'ownerName': get_user_data(_id).get('first_name'),
                     'ownerSurname': get_user_data(_id).get('last_name'),
                     'ownerPhoto': get_user_data(_id).get('photo_100')})
    else:
        meet.update({'ownerId': _id,
                     'ownerName': get_group_data.get('name'),
                     'ownerPhoto': get_group_data.get('photo_100')})

    return meet
