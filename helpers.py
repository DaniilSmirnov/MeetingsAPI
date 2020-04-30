import validators
import mysql.connector
from vkdata import get_user_data, get_group_data


def check_url(url):
    try:
        if url.find(' ') == -1:
            if url.find('http') == -1:
                url = 'http://' + url
            if validators.url(url):
                return True
        else:
            url = url.split(' ')
            for item in url:
                if item.find('http') == -1:
                    item = 'http://' + item
                if validators.url(item):
                    return True
    except validators.ValidationFailure:
        return False


def get_cnx():
    cnx = mysql.connector.connect(user='met', password='misha_benich228',
                                  host='0.0.0.0',
                                  database='meets')

    return cnx


def is_owner(meet, id):
    cnx = get_cnx()

    cursor = cnx.cursor(buffered=True)
    query = "select count(id) from meetings where id = %s and ownerid = %s;"
    data = (meet, id)
    cursor.execute(query, data)

    for item in cursor:
        for value in item:
            return value > 0


def is_expired(meet):
    cnx = get_cnx()

    cursor = cnx.cursor(buffered=True)
    query = "select count(id) from meetings where id = %s and current_date > finish;"
    data = (meet,)
    cursor.execute(query, data)

    for item in cursor:
        for value in item:
            return value > 0


def get_data(cursor):

    _ids = []
    for item in cursor:
        i = 0
        for value in item:
            if i == 3 and value > 0:
                _ids.append(value)
            i += 1

    def f(lst, n):
        return [lst[i:i + n] for i in range(0, len(lst), n)]

    data = []

    _ids = f(_ids, 1000)
    for item in _ids:
        data += get_user_data(item)

    return data


def prepare_meet(cursor, _id_client):
    buf = cursor.fetchall()
    data = get_data(buf)

    user = 0
    response = []

    for item in buf:
        i = 0
        meet = {}
        for value in item:
            if i == 0:
                meet.update({'id': value})
                meet.update({'ismember': is_member(value, _id_client)})
                meet.update({'isexpired': is_expired(value)})
            if i == 1:
                meet.update({'name': value})
            if i == 2:
                meet.update({'description': value})
            if i == 3:
                meet.update({'ownerid': value})
                meet.update({'isowner': value == _id_client})
                if value > 0:
                    meet.update({'owner_name': data[user].get('first_name')})
                    meet.update({'owner_surname': data[user].get('last_name')})
                    meet.update({'owner_photo': data[user].get('photo_100')})
                    user += 1
                else:
                    group_data = get_group_data(value * -1)
                    meet.update({'owner_name': group_data[0].get('name')})
                    meet.update({'owner_photo': group_data[0].get('photo')})
            if i == 4:
                meet.update({'members_amount': value})
            if i == 5:
                meet.update({'start': str(value)[0:-9]})
            if i == 6:
                meet.update({'finish': str(value)[0:-9]})
            if i == 7:
                meet.update({'approved': value == 1})
            if i == 8:
                meet.update({'photo': str(value)})

            i += 1
        response.append(meet)
    return response


def is_liked(id, comment):
    cnx = get_cnx()
    cursor = cnx.cursor()
    query = "select count(idratings) from ratings where iduser = %s and idcomment = %s;"
    data = (id, comment)
    cursor.execute(query, data)
    for item in cursor:
        for value in item:
            return value == 1

