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


def ismember(meet, id):
    cnx = get_cnx()

    cursor = cnx.cursor(buffered=True)
    query = "select count(id) from meetings where id = %s and id in (select idmeeting from participation where " \
            "idmember = %s); "
    data = (meet, id)
    cursor.execute(query, data)

    for item in cursor:
        for value in item:
            return value > 0


def isowner(meet, id):
    cnx = get_cnx()

    cursor = cnx.cursor(buffered=True)
    query = "select count(id) from meetings where id = %s and ownerid = %s;"
    data = (meet, id)
    cursor.execute(query, data)

    for item in cursor:
        for value in item:
            return value > 0


def isexpired(meet):
    cnx = get_cnx()

    cursor = cnx.cursor(buffered=True)
    query = "select count(id) from meetings where id = %s and current_date > finish;"
    data = (meet,)
    cursor.execute(query, data)

    for item in cursor:
        for value in item:
            return value > 0


def prepare_meet(cursor, _id_client):
    response = []
    for item in cursor:
        i = 0
        meet = {}
        for value in item:
            if i == 0:
                meet.update({'id': value})
                id = value
            if i == 1:
                meet.update({'name': value})
            if i == 2:
                meet.update({'description': value})
            if i == 3:
                meet.update({'ownerid': value})
                if value > 0:
                    data = get_user_data(value)
                    _name = data[0].get('first_name')
                    _surname = data[0].get('last_name')
                    _photo = data[0].get('photo_100')
                    meet.update({'owner_name': _name})
                    meet.update({'owner_surname': _surname})
                    meet.update({'owner_photo': _photo})
                else:
                    data = get_group_data(value * -1)
                    _name = data[0].get('name')
                    _photo = data[0].get('photo_100')
                    meet.update({'owner_name': _name})
                    meet.update({'owner_photo': _photo})

            if i == 4:
                meet.update({'members_amount': value})
            if i == 5:
                meet.update({'start': str(value)[0:-9]})
            if i == 6:
                meet.update({'finish': str(value)[0:-9]})
            if i == 7:
                if value == 1:
                    meet.update({'approved': True})
                if value != 1:
                    meet.update({'approved': False})
            if i == 8:
                meet.update({'photo': str(value)})
                meet.update({'ismember': ismember(id, _id_client)})
                meet.update({'isowner': isowner(id, _id_client)})
                meet.update({'isexpired': isexpired(id)})
            i += 1
        response.append(meet)
    return response


def isliked(id, comment):
    cnx = get_cnx()
    cursor = cnx.cursor()
    query = "select count(idratings) from ratings where iduser = %s and idcomment = %s;"
    data = (id, comment)
    cursor.execute(query, data)
    for item in cursor:
        for value in item:
            return value == 1

