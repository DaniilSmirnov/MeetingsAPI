from modules.database import get_cnx, get_value, get_dict, get_array


def get_meet(meet_id, user_id):
    cnx, cursor = get_cnx()
    query = "select * from meetings where id = %s and ismoderated = 1;"
    data = (meet_id,)
    cursor.execute(query, data)

    return get_object(cursor, user_id)


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


def get_object(cursor, _id_client):
    raw_data = get_array(cursor, cursor.column_names)
    user = prepare_data(buf, 3)  # NOT WORK NEED REFACTOR ITS A BULLSHIT
    response = []

    for meet in raw_data:
        _id = meet.get('owner_id')
        meet_id = meet.get('id')

        if _id > 0:
            meet.update({'owner_name': user.get(_id).get('first_name'),
                         'owner_surname': user.get(_id).get('last_name'),
                         'owner_photo': user.get(_id).get('photo_100')})
        else:
            group_data = get_group_data(_id)[0]
            meet.update({'owner_name': group_data.get('name'),
                         'owner_photo': group_data.get('photo')})

        meet.update({
                     'isMember': is_member(meet_id, _id_client),
                     'isExpired': is_expired(meet_id),
                     'isOwner': _id == _id_client,
                     'isApproved': row[7] == 1,
                     'photo': row[8].decode()})

    for row in buf:
        meet = {}

        _id = row[3]
        if _id > 0:
            meet.update({'owner_name': user.get(_id).get('first_name'),
                         'owner_surname': user.get(_id).get('last_name'),
                         'owner_photo': user.get(_id).get('photo_100')})
        else:
            group_data = get_group_data(_id)[0]
            meet.update({'owner_name': group_data.get('name'),
                         'owner_photo': group_data.get('photo')})

        meet.update({'id': row[0],
                     'isMember': is_member(row[0], _id_client),
                     'isExpired': is_expired(row[0]),
                     'name': row[1],
                     'description': row[2],
                     'ownerId': _id,
                     'isOwner': _id == _id_client,
                     'membersAmount': row[4],
                     'isApproved': row[7] == 1,
                     'photo': row[8].decode()})

        response.append(meet)
    return response
