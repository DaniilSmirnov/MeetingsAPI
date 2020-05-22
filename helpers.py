import validators
from vkdata import get_user_data, get_group_data
from PIL import Image
from io import BytesIO
import base64
from urllib.parse import urlparse, parse_qsl, urlencode
import math
from database import *


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


def prepare_data(cursor):
    users = []
    for item in cursor:
        i = 0
        for value in item:
            if i == 3:
                if value > 0:
                    users.append(int(value))
            i += 1

    users = list(set(users))
    data = get_user_data(users)

    response = {}
    for item in data:
        response.update({item.get('id'): item})

    return response


def prepare_meet(cursor, _id_client):
    try:
        buf = cursor.fetchall()
    except BaseException:  #TODO: remove when all GetMeets methods migrate to offset
        buf = cursor

    user = prepare_data(buf)
    response = []
    for row in buf:
        meet = {}

        meet.update({'id': row[0]})
        meet.update({'ismember': is_member(row[0], _id_client)})
        meet.update({'isexpired': is_expired(row[0])})
        meet.update({'name': row[1]})
        meet.update({'description': row[2]})

        _id = row[3]
        meet.update({'ownerid': _id})
        meet.update({'isowner': _id == _id_client})
        if _id > 0:
            meet.update({'owner_name': user.get(_id).get('first_name')})
            meet.update({'owner_surname': user.get(_id).get('last_name')})
            meet.update({'owner_photo': user.get(_id).get('photo_100')})
        else:
            group_data = get_group_data(_id)[0]
            meet.update({'owner_name': group_data.get('name')})
            meet.update({'owner_photo': group_data.get('photo')})

        meet.update({'members_amount': row[4]})
        meet.update({'start': str(row[5])[0:-9]})
        meet.update({'finish': str(row[6])[0:-9]})
        meet.update({'approved': row[7] == 1})
        meet.update({'photo': row[8].decode()})

        response.append(meet)
    return response


def is_liked(_id, comment):
    query = "select count(idratings) from ratings where iduser = %s and idcomment = %s;"
    data = (_id, comment)

    return select_query(query=query, data=data, decompose='value') == 1


def is_member(meet, _id):
    query = "select idmeeting from participation where idmeeting = %s and idmember = %s; "
    data = (meet, _id)

    return select_query(query=query, data=data, decompose='value') > 0


def is_expired(meet):

    query = "select count(id) from meetings where id = %s and current_date > finish;"
    data = (meet,)

    return select_query(query=query, data=data, decompose='value') > 0


def compress_blob(image):
    image = image.split(',')
    image = image[1]

    image = base64.b64decode(image)
    corrected = [256 + x if x < 0 else x for x in image]

    image = Image.open(BytesIO(bytes(corrected)))
    image = image.convert('RGB')

    buffered = BytesIO()
    x, y = image.size
    image.resize((math.floor(x - 50), math.floor(y - 20)), Image.ANTIALIAS)
    image.save(buffered, format="JPEG", optimize=True, quality=70)
    image = base64.b64encode(buffered.getvalue())
    return image


def get_group_id(request):
    launch_params = request.referrer
    launch_params = dict(parse_qsl(urlparse(launch_params).query, keep_blank_values=True))
    return int(launch_params.get('vk_group_id')) * -1
