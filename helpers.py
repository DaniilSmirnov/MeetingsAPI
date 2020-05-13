import validators
import mysql.connector
from vkdata import get_user_data, get_group_data
from PIL import Image
from io import BytesIO
import base64


def check_url(url):
    try:
        if url.find(' ') == -1:
            if url.find('http') == -1:
                url = 'http://{0}'.format(url)
            return validators.url(url)
        else:
            url = url.split(' ')
            for item in url:
                if item.find('http') == -1:
                    item = 'http://{0}'.format(item)
                return validators.url(item)
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
    query = "select idmeeting from participation where idmeeting = %s and idmember = %s; "
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
    buf = cursor.fetchall()

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
                    user = get_user_data(value)[0]
                    meet.update({'owner_name': user.get('first_name')})
                    meet.update({'owner_surname': user.get('last_name')})
                    meet.update({'owner_photo': user.get('photo_100')})
                else:
                    group_data = get_group_data(value * -1)[0]
                    meet.update({'owner_name': group_data.get('name')})
                    meet.update({'owner_photo': group_data.get('photo')})
            if i == 4:
                meet.update({'members_amount': value})
            if i == 5:
                meet.update({'start': str(value)})
            if i == 6:
                meet.update({'finish': str(value)})
            if i == 7:
                meet.update({'approved': value == 1})
            if i == 8:
                meet.update({'photo': value.decode()})

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


def compress_blob(image):
    image = image.split(',')  # It's needed because weak frontend code
    image = image[1]

    image = base64.b64decode(image)
    corrected = [256 + x if x < 0 else x for x in image]

    image = Image.open(BytesIO(bytes(corrected)))
    image = image.resize((160, 300), Image.ANTIALIAS)

    buffered = BytesIO()
    image.save(buffered, format="JPEG", optimize=True, quality=85)
    image = base64.b64encode(buffered.getvalue())
    return image


def get_group_id(request):
    launch_params = request.referrer
    launch_params = dict(parse_qsl(urlparse(launch_params).query, keep_blank_values=True))
    return int(launch_params.get('vk_group_id')) * -1