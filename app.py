from base64 import b64encode
from collections import OrderedDict
from hashlib import sha256
from hmac import HMAC
from urllib.parse import urlparse, parse_qsl, urlencode
import mysql.connector
from flask import Flask
from flask import request
from flask_cors import CORS
from flask_restful import Resource, Api, reqparse
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from vkdata import notify, get_user_data
from haversine import haversine, Unit
from demo import search

app = Flask(__name__)

app.config['CORS_HEADERS'] = 'Access-Control-Allow-Origin: *'

cors = CORS(app)
api = Api(app)
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["5 per second"],
)


def get_cnx():
    cnx = mysql.connector.connect(user='root', password='misha_benich228',
                                  host='0.0.0.0',
                                  database='meets')

    return cnx


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
        query = "select surname from members where idmembers = %s;"
        data = (id,)
        cursor.execute(query, data)
        for item in cursor:
            for value in item:
                cnx.close()
                return value


class UpdateUser(Resource):
    decorators = [limiter.limit("5 per second")]
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('first_name', type=str)
        parser.add_argument('last_name', type=str)
        parser.add_argument('photo_100', type=str)

        args = parser.parse_args()

        _id_client = AuthUser.check_sign(AuthUser, request)
        if _id_client == -100:
            return {'failed': 403}

        try:
            data = get_user_data(_id_client)
            _name = data.get('first_name')
            _surname = data.get('last_name')
            _photo = data.get('photo_200')
        except BaseException:
            _name = args['first_name']
            _surname = args['last_name']
            _photo = args['photo_100']

        cnx = get_cnx()

        cursor = cnx.cursor(buffered=True)
        query = "update members set name = %s, surname = %s, photo = %s where idmembers = %s;"
        data = (_name, _surname, _photo, _id_client)
        cursor.execute(query, data)
        cnx.commit()

        cnx.close()

        return {'status': 'Успешно'}


class AddUser(Resource):
    decorators = [limiter.limit("5 per second")]
    def post(self):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('first_name', type=str)
            parser.add_argument('last_name', type=str)
            parser.add_argument('photo_100', type=str)

            args = parser.parse_args()

            _id_client = AuthUser.check_sign(AuthUser, request)
            if _id_client == -100:
                return {'failed': 403}

            cnx = get_cnx()

            try:
                data = get_user_data(_id_client)
                _name = data.get('first_name')
                _surname = data.get('last_name')
                _photo = data.get('photo_200')
            except BaseException:
                _name = args['first_name']
                _surname = args['last_name']
                _photo = args['photo_100']

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
    decorators = [limiter.limit("5 per second")]
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
                    if value == 1:
                        return False
                    if value == 0:
                        return True

            cnx.close()

        except BaseException as e:
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

        if (len(_name) == 0) or _name.isspace() or _name.isdigit() or len(_name) > 45 or search(_name):
            return {'failed': 'Некорректное название митинга'}
        if len(_description) == 0 or _description.isspace() or _description.isdigit() or len(_description) > 254 or search(_description):
            return {'failed': 'Некорректное описание митинга'}
        if len(_start) == 0 or _start.isspace() or _start == 'undefined:00' or _start == '0000-00-00 00:00:00:00':
            return {'failed': 'Некорректная дата начала митинга'}
        if len(_finish) == 0 or _finish.isspace() or str(_finish) == 'undefined:00' or _finish == '0000-00-00 00:00:00:00':
            return {'failed': 'Некорректная дата окончания митинга'}
        if len(_photo) == 0 or _photo.isspace() or _photo.isdigit():
            return {'failed': 'Некорректное фото митинга или ссылка на него'}

        _owner_id = AuthUser.check_sign(AuthUser, request)
        if _owner_id == -100:
            return {'failed': 403}

        try:
            cnx = get_cnx()

            cursor = cnx.cursor(buffered=True)

            query = "insert into meetings values (default, %s, %s, %s, default, %s, %s, default, %s, null)"
            data = (_name, _description, _owner_id, _start, _finish, _photo)
            cursor.execute(query, data)
            cnx.commit()

            cursor.close()
            cnx.close()
            return {'success': 'Ваш митинг отправлен на модерацию, обычно это занимает до трех часов'}

        except BaseException as e:
            cursor.close()
            cnx.close()
            print(str(e))
            return {'failed': 'Произошла ошибка на сервере. Сообщите об этом.'}


class GetMeets(Resource):
    decorators = [limiter.limit("5 per second")]
    def get(self):
        try:

            def ismember(meet, id):
                cnx = get_cnx()

                cursor = cnx.cursor(buffered=True)
                query = "select count(id) from meetings where id = %s and id in (select idmeeting from participation where idmember = %s);"
                data = (meet, id)
                cursor.execute(query, data)

                for item in cursor:
                    for value in item:
                        if value > 0:
                            return 1
                        else:
                            return 0

                cnx.close()

            _id_client = AuthUser.check_sign(AuthUser, request)
            if _id_client == -100:
                return {'failed': 403}

            cnx = get_cnx()

            cursor = cnx.cursor(buffered=True)
            query = "select * from meetings where finish > current_date() and ismoderated = 1;"

            response = []
            cursor.execute(query)
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
                        meet.update({'start': str(value)})
                    if i == 6:
                        meet.update({'finish': str(value)})
                    if i == 8:
                        meet.update({'photo': str(value)})
                        meet.update({'ismember': ismember(id, _id_client)})
                    i += 1
                response.append(meet)
            cursor.close()
            cnx.close()
            return response
        except BaseException as e:
            cursor.close()
            cnx.close()
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
            query = "select * from meetings where finish > current_date() and ismoderated = 1 and id in (select idmeeting from participation where idmember = %s);"
            data = (_id_client,)
            response = []
            cursor.execute(query, data)
            for item in cursor:
                i = 0
                meet = {}
                for value in item:
                    if i == 0:
                        meet.update({'id': value})
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
                        meet.update({'start': str(value)})
                    if i == 6:
                        meet.update({'finish': str(value)})
                    if i == 8:
                        meet.update({'photo': str(value)})
                    i += 1
                response.append(meet)
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
            data = (_meet, )
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
    def check_sign(self, request):
        def is_valid(*, query: dict, secret: str) -> bool:
            """Check VK Apps signature"""
            vk_subset = OrderedDict(sorted(x for x in query.items() if x[0][:3] == "vk_"))
            hash_code = b64encode(HMAC(secret.encode(), urlencode(vk_subset, doseq=True).encode(), sha256).digest())
            decoded_hash_code = hash_code.decode('utf-8')[:-1].replace('+', '-').replace('/', '_')
            try:
                return query["sign"] == decoded_hash_code
            except KeyError:
                return query.get("sign") == decoded_hash_code

        launch_params = request.referrer
        launch_params = dict(parse_qsl(urlparse(launch_params).query, keep_blank_values=True))

        if not is_valid(query=launch_params, secret="VUc7I09bHOUYWjfFhx20"):
            return -100
        else:
            return launch_params.get('vk_user_id')

    def validate_user(self, id, request):
        launch_params = request.referrer
        launch_params = dict(parse_qsl(urlparse(launch_params).query, keep_blank_values=True))

        if not str(launch_params.get('vk_user_id')) == str(id):
            return False
        else:
            return True

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
    decorators = [limiter.limit("5 per second")]
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('meet', type=int)
        parser.add_argument('comment', type=str)
        args = parser.parse_args()

        cnx = get_cnx()

        cursor = cnx.cursor(buffered=True)

        _meet = args['meet']
        _comment = args['comment']

        _id_client = AuthUser.check_sign(AuthUser, request)
        if _id_client == -100:
            return {'failed': 403}

        query = "insert into comments values (default, %s, %s, %s);"
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
        parser.add_argument('meet', type=str)
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
                    id = str(value)
                if i == 1:
                    comment.update({'comment': value})
                if i == 2:
                    comment.update({'ownerid': value})
                if i == 3:
                    comment.update({'meetingid': value})

                i += 1
            response.append(comment)

        cursor.close()
        cnx.close()
        return response


class RemoveComment(Resource):
    decorators = [limiter.limit("5 per second")]
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('comment', type=int)

        args = parser.parse_args()

        cnx = get_cnx()

        cursor = cnx.cursor(buffered=True)

        _comment = args['comment']

        _id = AuthUser.check_sign(AuthUser, request)
        if _id == -100:
            return {'failed': 403}

        query = "select count(idcomments) from comments where idcomments = %s and ownerid = %s;"
        data = (_comment, _id)
        cursor.execute(query, data)
        for item in cursor:
            for value in item:
                if value < 1:
                    if not AuthUser.checkuser(_id, request):
                        return {'success': False, 'failed': 'Comment doesnt exists'}

        query = "delete from comments where idcomments = %s"
        cursor.execute(query, data)
        cnx.commit()

        cursor.close()
        cnx.close()
        return {'success': True}


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
            data = (_id, )
            cursor.execute(query, data)
            i = 0
            for item in cursor:
                for value in item:
                    if i == 0:
                        name = str(value)
                    if i == 1:
                        id = str(value)
                        notify(id, name)
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

                response = []
                cursor.execute(query)
                for item in cursor:
                    i = 0
                    meet = {}
                    for value in item:
                        if i == 0:
                            meet.update({'id': value})
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
                            meet.update({'start': str(value)})
                        if i == 6:
                            meet.update({'finish': str(value)})
                        if i == 7:
                            meet.update({'approved': int(value)})
                        if i == 8:
                            meet.update({'photo': str(value)})
                        i += 1
                    response.append(meet)

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

        cnx = get_cnx()
        cursor = cnx.cursor(buffered=True)

        query = "select lat, lon from geoposition where id = %s;"
        data = (_id, )
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

        query = "select lat, lon from geoposition where id in (select idmember from participation where idmeetings = %s and idmember is not %s)"
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
                i += 1
            if lat != 0 and lon != 0:
                another_user = (lat, lon)
                if haversine(user, another_user) < 5:
                    return {'status': 'success'}
                else:
                    return {'failed': 'Никого нет рядом'}

    def post(self):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('lat', type=str)
            parser.add_argument('long', type=str)
            args = parser.parse_args()

            _lat = args['lat']
            _lon = args['long']

            if len(_lat) > 2 or len(_lon) > 3 or float(_lat) not in range(-90, 90) or float(_lon) not in range(-180, 180):
                return {'failed': 'wrong data'}

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


api.add_resource(TestConnection, '/TestConnection')

api.add_resource(IsFirst, '/IsFirst')
api.add_resource(UpdateUser, '/UpdateUser')
api.add_resource(AddUser, '/AddUser')

api.add_resource(GetMeets, '/GetMeets')
api.add_resource(AddMeet, '/AddMeet')

api.add_resource(AddMeetMember, '/AddMeetMember')
api.add_resource(RemoveMeetMember, '/RemoveMeetMember')
api.add_resource(GetUserMeets, '/GetUserMeets')

api.add_resource(GetMeetComments, '/GetMeetComments')
api.add_resource(AddComment, '/AddComment')
api.add_resource(RemoveComment, '/RemoveComment')

api.add_resource(ApproveMeet, '/admin/Approve')
api.add_resource(DeApproveMeet, '/admin/DeApprove')
api.add_resource(GetAllMeets, '/admin/GetAllMeets')

if __name__ == '__main__':
    context = ('/etc/ssl/vargasoff.ru.crt', '/etc/ssl/private.key')
    app.run(host='0.0.0.0', port='8000', ssl_context=context)
