from modules.database import get_cnx, get_value, get_dict, get_array
from user.user_functions import get_owner


def get_meet(meet_id, user_id):
    cnx, cursor = get_cnx()
    query = "select * from meetings where id = %s and ismoderated = 1;"
    data = (meet_id,)
    cursor.execute(query, data)

    return generate_meet_object(cursor, user_id)


def is_liked(_id, comment):
    query = "select count(idratings) from ratings where iduser = %s and idcomment = %s;"
    data = (_id, comment)
    cursor.execute(query, data)

    return get_value(cursor)


def is_member(meet, _id):
    query = "select idmeeting from participation where idmeeting = %s and idmember = %s; "
    data = (meet, _id)
    cursor.execute(query, data)

    return get_value(cursor)


def is_expired(meet):
    query = "select count(id) from meetings where id = %s and current_date > finish;"
    data = (meet,)
    cursor.execute(query, data)

    return get_value(cursor)


def generate_meet_object(cursor, _id_client):
    raw_data = get_array(cursor, cursor.column_names)
    response = []

    for meet in raw_data:
        _id = meet.get('ownerId')
        meet_id = meet.get('id')
        meet.pop('OwnerId')
        meet.update({'owner': get_owner(_id)})

        meet.update({
            'isMember': is_member(meet_id, _id_client),
            'isExpired': is_expired(meet_id) == 1,
            'isOwner': _id == _id_client,
            'isApproved': meet.get('isApproved') == 1,
            'photo': meet.get('photo').decode()})

        response.append(meet)
    return response
