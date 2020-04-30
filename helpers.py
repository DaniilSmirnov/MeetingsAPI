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


def is_member(meet, id):
    cnx = get_cnx()

    cursor = cnx.cursor(buffered=True)
    query = "select count(id) from meetings where id = %s and id in (select idmeeting from participation where " \
            "idmember = %s); "
    data = (meet, id)
    cursor.execute(query, data)

    for item in cursor:
        for value in item:
            return value > 0


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


def prepare_meet(cursor, _id_client):
    response = []

    for item in cursor:
        i = 0
        meet = {}
        for value in item:
            if i == 0:
                meet.update({'id': value})
                _id = value
            if i == 1:
                meet.update({'name': value})
            if i == 2:
                meet.update({'description': value})
            if i == 3:
                meet.update({'ownerid': value})
                if value > 0:
                    data = get_user_data(value)
                    meet.update({'owner_name': data[0].get('first_name')})
                    meet.update({'owner_surname': data[0].get('last_name')})
                    meet.update({'owner_photo': data[0].get('photo_100')})
                else:
                    data = get_group_data(value * -1)
                    meet.update({'owner_name': data[0].get('name')})
                    meet.update({'owner_photo': data[0].get('photo')})

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
                meet.update({'ismember': is_member(_id, _id_client)})
                meet.update({'isowner': is_owner(_id, _id_client)})
                meet.update({'isexpired': is_expired(_id)})
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

