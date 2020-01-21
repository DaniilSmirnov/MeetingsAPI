from base64 import b64encode
from collections import OrderedDict
from hashlib import sha256
from hmac import HMAC
from urllib.parse import urlparse, parse_qsl, urlencode

import mysql.connector
import validators
from flask import Flask
from flask import request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_restful import Resource, Api, reqparse
from haversine import haversine

from demo import search
from stories import prepare_storie
from vkdata import notify, get_user_data, get_group_data

app = Flask(__name__)

app.config['CORS_HEADERS'] = 'Access-Control-Allow-Origin: *'

cors = CORS(app)
api = Api(app)
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["5 per second"],
)


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
    cnx = mysql.connector.connect(user='root', password='misha_benich228',
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
            if value > 0:
                return True
            else:
                return False


def isowner(meet, id):
    cnx = get_cnx()

    cursor = cnx.cursor(buffered=True)
    query = "select count(id) from meetings where id = %s and ownerid = %s;"
    data = (meet, id)
    cursor.execute(query, data)

    for item in cursor:
        for value in item:
            if value > 0:
                return True
            else:
                return False


def isexpired(meet):
    cnx = get_cnx()

    cursor = cnx.cursor(buffered=True)
    query = "select count(id) from meetings where id = %s and current_date > finish;"
    data = (meet, )
    cursor.execute(query, data)

    for item in cursor:
        for value in item:
            if value > 0:
                return True
            else:
                return False


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
                meet.update({'owner_name': GetUser.get_owner_name(GetUser, value)})
                meet.update({'owner_surname': GetUser.get_owner_surname(GetUser, value)})
                meet.update({'owner_photo': GetUser.get_owner_photo(GetUser, value)})
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
            if value == 1:
                return True
            else:
                return False
        break


class TestConnection(Resource):
    def get(self):
        cnx = get_cnx()
        cnx.close()
        return {'status': 'success'}


class GetUser(Resource):

    def get_owner_name(self, id):
        cnx = get_cnx()
        cursor = cnx.cursor()
        query = "select name from members where idmembers = %s;"
        data = (id,)
        cursor.execute(query, data)
        for item in cursor:
            for value in item:
                cnx.close()
                return value

    def get_owner_surname(self, id):
        cnx = get_cnx()
        cursor = cnx.cursor()
        query = "select surname from members where idmembers = %s;"
        data = (id,)
        cursor.execute(query, data)
        for item in cursor:
            for value in item:
                cnx.close()
                return value

    def get_owner_photo(self, id):
        cnx = get_cnx()
        cursor = cnx.cursor()
        query = "select photo from members where idmembers = %s;"
        data = (id,)
        cursor.execute(query, data)
        for item in cursor:
            for value in item:
                cnx.close()
                return value


class UpdateUser(Resource):
    def post(self):
        _id_client = AuthUser.check_sign(AuthUser, request)
        if _id_client == -100:
            return {'failed': 403}

        data = get_user_data(_id_client)
        _name = data[0].get('first_name')
        _surname = data[0].get('last_name')
        _photo = data[0].get('photo_100')

        cnx = get_cnx()

        cursor = cnx.cursor(buffered=True)
        query = "update members set name = %s, surname = %s, photo = %s where idmembers = %s;"
        data = (_name, _surname, _photo, _id_client)
        cursor.execute(query, data)
        cnx.commit()

        cnx.close()

        return {'status': 'Успешно'}


class AddUser(Resource):
    def post(self):
        try:

            _id_client = AuthUser.check_sign(AuthUser, request)
            if _id_client == -100:
                return {'failed': 403}

            cnx = get_cnx()

            data = get_user_data(_id_client)
            _name = data[0].get('first_name')
            _surname = data[0].get('last_name')
            _photo = data[0].get('photo_100')

            cursor = cnx.cursor(buffered=True)
            query = "insert into members values(%s, default, %s, %s, %s)"
            data = (_id_client, _name, _surname, _photo)
            cursor.execute(query, data)
            cnx.commit()

            cnx.close()

            return {'status': 'Успешно'}
        except BaseException:
            return {'status': 'failed'}


class IsFirst(Resource):
    def get(self):
        try:
            _id = AuthUser.check_sign(AuthUser, request)
            if _id == -100:
                return {'failed': 403}

            cnx = get_cnx()

            cursor = cnx.cursor(buffered=True)

            query = "select count(idmembers) from members where idmembers = %s;"
            data = (_id,)
            cursor.execute(query, data)

            for item in cursor:
                for value in item:
                    data = get_user_data(_id)
                    _name = data[0].get('first_name')
                    _surname = data[0].get('last_name')
                    _photo = data[0].get('photo_100')
                    if value == 0:
                        query = "insert into members values(%s, default, %s, %s, %s)"
                        data = (_id, _name, _surname, _photo)
                        cursor.execute(query, data)
                        cnx.commit()
                        cnx.close()
                        return True
                    if value == 1:
                        query = "update members set name = %s, surname = %s, photo = %s where idmembers = %s;"
                        data = (_name, _surname, _photo, _id)
                        cursor.execute(query, data)
                        cnx.commit()
                        cnx.close()
                        return False

            cnx.close()

        except BaseException as e:
            print(e)
            return {'failed': 'error'}


class AddMeet(Resource):
    decorators = [limiter.limit("3 per day")]
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str)
        parser.add_argument('description', type=str)
        parser.add_argument('start', type=str)
        parser.add_argument('finish', type=str)
        parser.add_argument('photo', type=str)
        args = parser.parse_args()

        _name = args['name']
        _description = args['description']
        _start = args['start']
        _finish = args['finish']
        _photo = args['photo']

        _owner_id = AuthUser.check_sign(AuthUser, request)
        if _owner_id == -100:
            return {'failed': 403}

        if AuthUser.checkuser(AuthUser, _owner_id, request):
            pass
        else:
            if (len(_name) == 0) or _name.isspace() or _name.isdigit() or len(_name) > 45 or search(_name):
                return {'failed': 'Некорректное название петиции'}
            if len(_description) == 0 or _description.isspace() or _description.isdigit() or len(
                    _description) > 254 or search(_description):
                return {'failed': 'Некорректное описание петиции'}
            if len(_start) == 0 or _start.isspace() or _start == 'undefined:00' or _start == '0000-00-00 00:00:00:00':
                return {'failed': 'Некорректная дата начала петиции'}
            if len(_finish) == 0 or _finish.isspace() or str(_finish) == 'undefined:00' or _finish == '0000-00-00 00:00:00:00':
                return {'failed': 'Некорректная дата окончания петиции'}
            if len(_photo) == 0 or _photo.isspace() or _photo.isdigit():
                return {'failed': 'Некорректная обложка петиции'}
            if check_url(_description):
                return {'failed': 'Описание не можем содержать ссылку'}

        try:
            cnx = get_cnx()

            cursor = cnx.cursor(buffered=True)

            query = "insert into meetings values (default, %s, %s, %s, default, %s, %s, default, %s, null, 1)"
            data = (_name, _description, _owner_id, _start, _finish, _photo)
            cursor.execute(query, data)
            cnx.commit()

            cursor.close()
            cnx.close()
            return {'success': 'Ваша петиция отправлена на модерацию, обычно это занимает до трех часов'}

        except BaseException as e:
            cursor.close()
            cnx.close()
            print(str(e))
            return {'failed': 'Произошла ошибка на сервере. Сообщите об этом.'}


class GetMeets(Resource):

    def get(self):
        try:

            _id_client = AuthUser.check_sign(AuthUser, request)
            if _id_client == -100:
                return {'failed': 403}

            cnx = get_cnx()

            cursor = cnx.cursor(buffered=True)
            query = "select * from meetings where finish > current_date() and ismoderated = 1 order by members_amount asc;"

            cursor.execute(query)
            response = prepare_meet(cursor, _id_client)
            cursor.close()
            cnx.close()
            return response
        except BaseException as e:
            print(str(e))
            return {'failed': 'Произошла ошибка на сервере. Сообщите об этом.'}


class GetMeet(Resource):
    decorators = [limiter.limit("5 per second")]

    def get(self):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('meet', type=int)
            args = parser.parse_args()
            _meet = args['meet']

            _id_client = AuthUser.check_sign(AuthUser, request)
            if _id_client == -100:
                return {'failed': 403}

            cnx = get_cnx()

            cursor = cnx.cursor(buffered=True)
            query = "select * from meetings where id = %s and ismoderated = 1;"

            data = (_meet,)
            cursor.execute(query, data)
            response = prepare_meet(cursor, _id_client)
            cursor.close()
            cnx.close()
            return response
        except BaseException as e:
            cursor.close()
            cnx.close()
            print(str(e))
            return {'failed': 'Произошла ошибка на сервере. Сообщите об этом.'}


class GetUserMeets(Resource):
    decorators = [limiter.limit("5 per second")]

    def get(self):
        try:
            _id_client = AuthUser.check_sign(AuthUser, request)
            if _id_client == -100:
                return {'failed': 403}

            cnx = get_cnx()

            cursor = cnx.cursor(buffered=True)
            query = "select * from meetings where finish > current_date() and ismoderated = 1 and id in (select idmeeting from participation where idmember = %s) order by members_amount asc;"
            data = (_id_client,)
            cursor.execute(query, data)
            response = prepare_meet(cursor, _id_client)
            cursor.close()
            cnx.close()
            return response
        except BaseException as e:
            cursor.close()
            cnx.close()
            return {'failed': 'Произошла ошибка на сервере. Сообщите об этом.'}


class GetOwneredMeets(Resource):
    decorators = [limiter.limit("5 per second")]

    def get(self):
        try:
            _id_client = AuthUser.check_sign(AuthUser, request)
            if _id_client == -100:
                return {'failed': 403}

            cnx = get_cnx()

            cursor = cnx.cursor(buffered=True)
            query = "select * from meetings where ownerid = %s;"
            data = (_id_client,)
            cursor.execute(query, data)
            response = prepare_meet(cursor, _id_client)
            cursor.close()
            cnx.close()
            return response
        except BaseException as e:
            print(e)
            cursor.close()
            cnx.close()
            return {'failed': 'Произошла ошибка на сервере. Сообщите об этом.'}


class GetExpiredUserMeets(Resource):
    decorators = [limiter.limit("5 per second")]

    def get(self):
        try:
            _id_client = AuthUser.check_sign(AuthUser, request)
            if _id_client == -100:
                return {'failed': 403}

            cnx = get_cnx()

            cursor = cnx.cursor(buffered=True)
            query = "select * from meetings where finish < current_date() and ismoderated = 1 and id in (select idmeeting from participation where idmember = %s) order by members_amount asc;"
            data = (_id_client,)
            cursor.execute(query, data)
            response = prepare_meet(cursor, _id_client)
            cursor.close()
            cnx.close()
            return response
        except BaseException as e:
            cursor.close()
            cnx.close()
            return {'failed': 'Произошла ошибка на сервере. Сообщите об этом.'}


class AddMeetMember(Resource):
    decorators = [limiter.limit("5 per second")]

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('meet', type=int)
        args = parser.parse_args()

        _meet = args['meet']

        _id_client = AuthUser.check_sign(AuthUser, request)
        if _id_client == -100:
            return {'failed': 403}

        try:
            cnx = get_cnx()

            cursor = cnx.cursor(buffered=True)

            query = "select count(id) from meetings where id = %s and ismoderated = 1;"
            data = (_meet,)
            cursor.execute(query, data)
            for item in cursor:
                for value in item:
                    if value != 1:
                        return {'failed': 'Meet is unavaible'}

            query = "select count(idmember) from participation where idmember = %s and idmeeting = %s;"
            data = (_id_client, _meet,)
            cursor.execute(query, data)

            for item in cursor:
                for value in item:
                    if value != 0:
                        return {'failed': 'User is in meeting yet'}

            query = "insert into participation values (default, %s, %s);"
            data = (_meet, _id_client,)
            cursor.execute(query, data)
            query = "update meetings set members_amount = members_amount + 1 where id = %s;"
            data = (_meet,)
            cursor.execute(query, data)
            cnx.commit()

            cursor.close()
            cnx.close()
            return {'success': True}

        except BaseException as e:
            cursor.close()
            cnx.close()
            return {'failed': 'Произошла ошибка на сервере. Сообщите об этом.'}


class RemoveMeetMember(Resource):
    decorators = [limiter.limit("5 per second")]

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('meet', type=int)
        args = parser.parse_args()
        try:
            cnx = get_cnx()

            cursor = cnx.cursor()

            _meet = args['meet']

            _id_client = AuthUser.check_sign(AuthUser, request)
            if _id_client == -100:
                return {'failed': 403}

            query = "select count(idmember) from participation where idmember = %s and idmeeting = %s;"
            data = (_id_client, _meet,)
            cursor.execute(query, data)

            for item in cursor:
                for value in item:
                    print(value)
                    if value == 0:
                        return {'failed': 'user is not in meet'}

            query = "delete from participation where idmember = %s and idmeeting = %s;"
            data = (_id_client, _meet,)
            cursor.execute(query, data)
            cnx.commit()
            query = "update meetings set members_amount = members_amount -1 where id = %s and members_amount > 0"
            data = (_meet,)
            cursor.execute(query, data)
            cnx.commit()

            cursor.close()
            cnx.close()
            return {'success': True}
        except BaseException:
            return {'failed': 'Произошла ошибка на сервере. Сообщите об этом.'}


class AuthUser(Resource):
    def check_vk_viewer_group_role(self, request):
        launch_params = request.referrer
        print(request.referrer)
        launch_params = dict(parse_qsl(urlparse(launch_params).query, keep_blank_values=True))
        role = launch_params.get('vk_viewer_group_role')
        if role == 'admin':
            return True
        else:
            return False

    def check_sign(self, request):

        def is_valid(*, query: dict, secret: str) -> bool:
            vk_subset = OrderedDict(sorted(x for x in query.items() if x[0][:3] == "vk_"))
            hash_code = b64encode(HMAC(secret.encode(), urlencode(vk_subset, doseq=True).encode(), sha256).digest())
            decoded_hash_code = hash_code.decode('utf-8')[:-1].replace('+', '-').replace('/', '_')
            try:
                return query["sign"] == decoded_hash_code
            except KeyError:
                return query.get("sign") == decoded_hash_code

        launch_params = request.referrer
        print(request.referrer)
        launch_params = dict(parse_qsl(urlparse(launch_params).query, keep_blank_values=True))

        if not is_valid(query=launch_params, secret="VUc7I09bHOUYWjfFhx20"):
            return -100
        else:
            return launch_params.get('vk_user_id')

    def checkuser(self, id, request):
        launch_params = request.referrer
        launch_params = dict(parse_qsl(urlparse(launch_params).query, keep_blank_values=True))

        if not str(launch_params.get('vk_user_id')) == str(id):
            return {'failed': '403'}

        cnx = mysql.connector.connect(user='root', password='misha_benich228',
                                      host='0.0.0.0',
                                      database='meets')

        cursor = cnx.cursor(buffered=True)

        query = "select rights_level from members where idmembers = %s;"
        data = (id,)
        cursor.execute(query, data)
        for item in cursor:
            for value in item:
                if str(value) == "admin":
                    cursor.close()
                    cnx.close()
                    return True
                else:
                    cursor.close()
                    cnx.close()
                    return False


class AddComment(Resource):
    decorators = [limiter.limit("5 per minute")]

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('meet', type=int)
        parser.add_argument('comment', type=str)
        args = parser.parse_args()

        cnx = get_cnx()

        cursor = cnx.cursor(buffered=True)

        _meet = args['meet']
        _comment = args['comment']

        if search(_comment) or _comment.isspace() or _comment.isdigit():
            return {'failed': 'Некорректный текст комментария'}
        if (_comment.find(" ") == -1) and (len(_comment) > 15) or (len(_comment) > 45):
            return {'failed': 'Некорректный текст комментария'}
        if check_url(_comment):
            return {'failed': 'Нельзя отправлять ссылки в комментарии'}
        if (len(_comment) < 4) and (_comment[0] == " " or _comment[len(_comment) - 1] == " "):
            return {'failed': 'Вам не кажется, что комментарий слишком короткий?'}

        _id_client = AuthUser.check_sign(AuthUser, request)
        if _id_client == -100:
            return {'failed': 403}

        query = "select count(id) from meetings where id = %s;"
        data = (_meet,)
        cursor.execute(query, data)
        for item in cursor:
            for value in item:
                if value < 1:
                    return {'failed': 'Meet is not exist'}

        query = "insert into comments values (default, %s, %s, %s, default);"
        data = (_comment, _id_client, _meet)
        cursor.execute(query, data)
        cnx.commit()

        cursor.close()
        cnx.close()
        return {'success': True}


class GetMeetComments(Resource):
    decorators = [limiter.limit("5 per second")]

    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('meet', type=int)
        args = parser.parse_args()

        cnx = get_cnx()

        cursor = cnx.cursor(buffered=True)

        _meet = args['meet']

        _id_client = AuthUser.check_sign(AuthUser, request)
        if _id_client == -100:
            return {'failed': 403}

        query = "select * from comments where meetingid = %s"
        data = (_meet,)

        response = []
        cursor.execute(query, data)
        for item in cursor:
            i = 0
            comment = {}
            for value in item:
                if i == 0:
                    comment.update({'id': value})
                    id = value
                if i == 1:
                    comment.update({'comment': value})
                if i == 2:
                    comment.update({'ownerid': value})
                    comment.update({'owner_name': GetUser.get_owner_name(GetUser, value)})
                    comment.update({'owner_surname': GetUser.get_owner_surname(GetUser, value)})
                    comment.update({'owner_photo': GetUser.get_owner_photo(GetUser, value)})
                if i == 3:
                    comment.update({'meetingid': value})
                if i == 4:
                    comment.update({'rating': value})
                    comment.update({'isliked': isliked(_id_client, id)})
                i += 1
            response.append(comment)

        cursor.close()
        cnx.close()
        return response


class RateComment(Resource):
    decorators = [limiter.limit("1 per second")]

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('comment', type=int)
        parser.add_argument('act', type=int)
        args = parser.parse_args()

        cnx = get_cnx()

        cursor = cnx.cursor(buffered=True)

        _comment = args['comment']
        _act = args['act']

        _id_client = AuthUser.check_sign(AuthUser, request)
        if _id_client == -100:
            return {'failed': 403}

        query = "select count(idcomments) from comments where idcomments = %s;"
        data = (_comment,)
        cursor.execute(query, data)
        for item in cursor:
            for value in item:
                if value < 1:
                    return {'failed': 'Comment is not exist'}
        query = "select count(idratings) from ratings where iduser = %s and idcomment = %s;"
        data = (_id_client, _comment)
        cursor.execute(query, data)
        for item in cursor:
            for value in item:
                if value == 1:
                    if _act == 0:
                        query = "delete from ratings where iduser = %s and idcomment = %s;"
                        cursor.execute(query, data)
                        query = "update comments set rating = rating - 1 where idcomments = %s;"
                        data = (_comment,)
                        cursor.execute(query, data)
                        cnx.commit()
                        return {'status': 'already liked'}
                if value == 0:
                    if _act == 1:
                        query = "update comments set rating = rating + 1 where idcomments = %s;"
                        data = (_comment,)
                        cursor.execute(query, data)
                        query = "insert into ratings values (default, %s, %s);"
                        data = (_id_client, _comment)
                        cursor.execute(query, data)
                        cnx.commit()
                        return {'status': 'success'}


class RemoveComment(Resource):
    decorators = [limiter.limit("5 per second")]

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('comment', type=int)
        args = parser.parse_args()
        _comment = args['comment']

        cnx = get_cnx()
        cursor = cnx.cursor(buffered=True)

        _id = AuthUser.check_sign(AuthUser, request)
        if _id == -100:
            return {'failed': 403}

        query = "select count(idcomments) from comments where idcomments = %s and ownerid = %s;"
        data = (_comment, _id)
        cursor.execute(query, data)
        for item in cursor:
            for value in item:
                if value < 1:
                    if not AuthUser.checkuser(AuthUser, _id, request):
                        return {'failed': 'Comment doesnt exists'}

        query = "delete from comments where idcomments = %s"
        data = (_comment,)
        cursor.execute(query, data)
        cnx.commit()

        cursor.close()
        cnx.close()
        return {'status': True}


class ApproveMeet(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('meet', type=int)
        args = parser.parse_args()
        cnx = get_cnx()

        cursor = cnx.cursor(buffered=True)

        _id = AuthUser.check_sign(AuthUser, request)
        if _id == -100:
            return {'failed': 403}

        _meet = args['meet']
        if AuthUser.checkuser(AuthUser, _id, request):
            query = "select ismoderated from meetings where id = %s;"
            data = (_meet,)
            cursor.execute(query, data)
            for item in cursor:
                for value in item:
                    if value == 1:
                        return {'failed': 'already approved'}

            query = "update meetings set ismoderated = 1, approver = %s where id = %s;"
            data = (_id, _meet)
            cursor.execute(query, data)
            cnx.commit()

            query = "select name, ownerid from meetings where id = %s"
            data = (_meet,)
            cursor.execute(query, data)
            i = 0
            for item in cursor:
                for value in item:
                    if i == 0:
                        name = str(value)
                    if i == 1:
                        id = int(value)
                        notify(id, name)
                        query = "insert into participation values (default, %s, %s);"
                        data = (_meet, id)
                        cursor.execute(query, data)
                        query = "update meetings set members_amount = members_amount + 1 where id = %s;"
                        data = (_meet,)
                        cursor.execute(query, data)
                        cnx.commit()

                    i += 1

            cursor.close()
            cnx.close()
            return {'success': True}
        else:
            cursor.close()
            cnx.close()
            return {'success': False}


class DeApproveMeet(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('meet', type=int)
        args = parser.parse_args()

        cnx = get_cnx()

        cursor = cnx.cursor(buffered=True)

        _meet = args['meet']
        _id = AuthUser.check_sign(AuthUser, request)
        if _id == -100:
            return {'failed': 403}

        if AuthUser.checkuser(AuthUser, _id, request):
            query = "select ismoderated from meetings where id = %s;"
            data = (_meet,)
            cursor.execute(query, data)
            for item in cursor:
                for value in item:
                    if value == 0:
                        return {'failed': 'already deapproved'}

            query = "update meetings set ismoderated = 0 where id = %s;"
            data = (_meet,)
            cursor.execute(query, data)
            query = "update meetings set isvisible = 0 where id = %s;"
            data = (_meet,)
            cursor.execute(query, data)
            cnx.commit()
            cursor.close()
            cnx.close()
            return {'success': True}
        else:
            cursor.close()
            cnx.close()
            return {'success': False}


class DenyMeet(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('meet', type=int)
        args = parser.parse_args()

        cnx = get_cnx()

        cursor = cnx.cursor(buffered=True)

        _meet = args['meet']
        _id = AuthUser.check_sign(AuthUser, request)
        if _id == -100:
            return {'failed': 403}

        if AuthUser.checkuser(AuthUser, _id, request):
            query = "select isvisible from meetings where id = %s;"
            data = (_meet,)
            cursor.execute(query, data)
            for item in cursor:
                for value in item:
                    if value == 0:
                        return {'failed': 'already deapproved'}

            query = "update meetings set isvisible = 0 where id = %s;"
            data = (_meet,)
            cursor.execute(query, data)
            cnx.commit()
            cursor.close()
            cnx.close()
            return {'success': True}
        else:
            cursor.close()
            cnx.close()
            return {'success': False}


class GetAllMeets(Resource):
    def get(self):
        try:

            _id = AuthUser.check_sign(AuthUser, request)
            if _id == -100:
                return {'failed': 403}

            if AuthUser.checkuser(AuthUser, _id, request):

                cnx = get_cnx()

                cursor = cnx.cursor(buffered=True)
                query = "select * from meetings;"
                cursor.execute(query)
                response = prepare_meet(cursor, _id)

                cursor.close()
                cnx.close()
                return response
            else:

                return {'success': False}
        except BaseException as e:
            return str(e)


class GeoPosition(Resource):
    def get(self):
        _id = AuthUser.check_sign(AuthUser, request)
        if _id == -100:
            return {'failed': 403}

        parser = reqparse.RequestParser()
        parser.add_argument('meet', type=str)
        args = parser.parse_args()

        _meet = args['meet']
        dist = []

        cnx = get_cnx()
        cursor = cnx.cursor(buffered=True)

        query = "select lat, lon from geoposition where userid = %s;"
        data = (_id,)
        cursor.execute(query, data)

        i = 0
        for item in cursor:
            lat = 0
            lon = 0
            for value in item:
                if i == 0:
                    lat = float(value)
                if i == 1:
                    lon = float(value)
                i += 1
            if lat != 0 and lon != 0:
                user = (lat, lon)
            else:
                return {'failed': 'Мы не можем вас найти'}

        query = "select count(lat) from geoposition where userid in (select idmember from participation where idmeeting = %s and idmember <> %s);"
        data = (_meet, int(_id))
        cursor.execute(query, data)

        for item in cursor:
            for value in item:
                if int(value == 0):
                    return {'failed': "Единомышленников поблизости не найдено"}

        query = "select lat, lon from geoposition where userid in (select idmember from participation where idmeeting = %s and idmember <> %s)"
        data = (_meet, _id)
        cursor.execute(query, data)

        i = 0
        for item in cursor:
            lat = 0
            lon = 0
            for value in item:
                if i == 0:
                    lat = float(value)
                if i == 1:
                    lon = float(value)
                    another_user = (lat, lon)
                    dist.append(int(haversine(user, another_user)))
                i += 1

        print(dist)
        print(min(dist))
        if min(dist) < 1:
            return {'status': "Ближайший единомышленник находится меньше чем в километре от вас"}
        else:
            return {'status': "Ближайший единомышленник находится в " + str(min(dist)) + " км от вас"}

    def post(self):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('lat', type=str)
            parser.add_argument('long', type=str)
            args = parser.parse_args()

            _lat = args['lat']
            _lon = args['long']

            _id = AuthUser.check_sign(AuthUser, request)
            if _id == -100:
                return {'failed': 403}

            cnx = get_cnx()
            cursor = cnx.cursor(buffered=True)

            try:
                query = 'insert into geoposition values (%s, %s, %s);'
                data = (_id, _lat, _lon)
                cursor.execute(query, data)
            except BaseException:
                query = 'update geoposition set lat = %s, lon = %s where userid = %s;'
                data = (_lat, _lon, _id)
                cursor.execute(query, data)

            cnx.commit()
            cnx.close()
            return {'status': 'success'}
        except BaseException:
            return {'status': 'failed'}


class getStory(Resource):
    def get(self):
        _id = AuthUser.check_sign(AuthUser, request)
        if _id == -100:
            return {'failed': 403}

        parser = reqparse.RequestParser()
        parser.add_argument('meet', type=str)
        args = parser.parse_args()

        _meet = args['meet']

        cnx = get_cnx()
        cursor = cnx.cursor(buffered=True)

        query = 'select name, photo from meetings where id = %s;'
        data = (_meet,)
        cursor.execute(query, data)

        i = 0
        for item in cursor:
            for value in item:
                if i == 0:
                    name = value
                if i == 1:
                    photo = value
                    image = prepare_storie(photo, name)
                    return image
                i += 1


class GetGroupInfo(Resource):
    def get(self):
        _id = AuthUser.check_sign(AuthUser, request)
        if _id == -100:
            return {'failed': 403}

        if AuthUser.check_vk_viewer_group_role(AuthUser, request):
            launch_params = request.referrer
            print(request.referrer)
            launch_params = dict(parse_qsl(urlparse(launch_params).query, keep_blank_values=True))
            group_id = launch_params.get('vk_group_id')
            data = get_group_data(group_id)
            _name = data[0].get('name')
            _photo = data[0].get('photo_100')
            return {'name': _name, 'photo': _photo}
        else:
            return False, 403


class GetByGroup(Resource):
    pass


class getWidget(Resource):
    def get(self):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('meet', type=int)
            args = parser.parse_args()
            _meet = args['meet']

            _id_client = AuthUser.check_sign(AuthUser, request)
            if _id_client == -100:
                return {'failed': 403}

            cnx = get_cnx()

            cursor = cnx.cursor(buffered=True)
            query = "select * from meetings where id = %s and ismoderated = 1;"

            data = (_meet,)
            cursor.execute(query, data)
            i = 0
            meet = {}
            response = {}
            rows = []
            for item in cursor:
                for value in item:
                    if i == 0:
                        meet.update({'id': value})
                    if i == 1:
                        meet.update({'title': value})
                    if i == 2:
                        meet.update({'descr': value})
                    if i == 3:
                        meet.update({'button': "Открыть"})
                    if i == 8:
                        meet.update({'cover_id': str(value)})
                    i += 1
                rows.append(meet)
            response.update({"title": 'Петиции'})
            response.update({'rows': rows})

            cnx.close()
            return response
        except BaseException as e:
            cursor.close()
            cnx.close()
            print(str(e))
            return {'failed': 'Произошла ошибка на сервере. Сообщите об этом.'}


api.add_resource(TestConnection, '/TestConnection')

api.add_resource(IsFirst, '/IsFirst')
api.add_resource(UpdateUser, '/UpdateUser')
api.add_resource(AddUser, '/AddUser')
api.add_resource(GetGroupInfo, '/GetGroupInfo')

api.add_resource(GetMeets, '/GetMeets')
api.add_resource(AddMeet, '/AddMeet')

api.add_resource(AddMeetMember, '/AddMeetMember')
api.add_resource(RemoveMeetMember, '/RemoveMeetMember')
api.add_resource(GetUserMeets, '/GetUserMeets')
api.add_resource(GetExpiredUserMeets, '/GetExpiredUserMeets')
api.add_resource(GetOwneredMeets, '/GetOwneredMeets')
api.add_resource(GetMeet, '/GetMeet')

api.add_resource(GetMeetComments, '/GetMeetComments')
api.add_resource(AddComment, '/AddComment')
api.add_resource(RemoveComment, '/RemoveComment')
api.add_resource(RateComment, '/RateComment')

api.add_resource(ApproveMeet, '/admin/Approve')
api.add_resource(DeApproveMeet, '/admin/DeApprove')
api.add_resource(GetAllMeets, '/admin/GetAllMeets')
api.add_resource(DenyMeet, '/admin/DenyMeet')

api.add_resource(getStory, '/getStory')
api.add_resource(GeoPosition, '/GeoPosition')

if __name__ == '__main__':
    #context = ('/etc/ssl/vargasoff.ru.crt', '/etc/ssl/private.key')
    #app.run(host='0.0.0.0', port='8000', ssl_context=context)
    app.run(host='0.0.0.0', port='8000')

