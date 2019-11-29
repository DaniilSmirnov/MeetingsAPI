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
        parser.add_argument('photo_200', type=str)

        args = parser.parse_args()

        _id_client = AuthUser.check_sign(AuthUser, request)
        if _id_client == -100:
            return {'failed': 403}

        _name = args['first_name']
        _surname = args['last_name']
        _photo = args['photo_200']

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
            parser.add_argument('photo_200', type=str)

            args = parser.parse_args()

            _id_client = AuthUser.check_sign(AuthUser, request)
            if _id_client == -100:
                return {'failed': 403}

            _name = args['first_name']
            _surname = args['last_name']
            _photo = args['photo_200']

            cnx = get_cnx()

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
            return str(e)
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

        if (len(_name) == 0) or _name.isspace() or _name.isdigit():
            return {'failed': 'Некорректное название митинга'}
        if len(_description) == 0 or _description.isspace() or _description.isdigit():
            return {'failed': 'Некорректное описание митинга'}
        if len(_start) == 0 or _start.isspace():
            return {'failed': 'Некорректная дата начала митинга'}
        if len(_finish) == 0 or _finish.isspace():
            return {'failed': 'Некорректная дата окончания митинга'}
        if len(_photo) == 0 or _photo.isspace() or _photo.isdigit():
            return {'failed': 'Некорректное фото митинга или ссылка на него'}

        _owner_id = AuthUser.check_sign(AuthUser, request)
        if _owner_id == -100:
            return {'failed': 403}

        try:
            cnx = get_cnx()

            cursor = cnx.cursor(buffered=True)

            query = "insert into meetings values (default, %s, %s, %s, default, %s, %s, default, %s)"
            data = (_name, _description, _owner_id, _start, _finish, _photo)
            cursor.execute(query, data)
            cnx.commit()

            cursor.close()
            cnx.close()
            return {'success': True}

        except BaseException as e:
            cursor.close()
            cnx.close()
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
            query = "update meetings set members_amount = members_amount + 1 where id = %s"
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

        if 'xvk' in request.headers:
            launch_params = request.headers.get('xvk')
            launch_params = "https://vargasoff.com:8000?" + launch_params
            launch_params = dict(parse_qsl(urlparse(launch_params).query, keep_blank_values=True))

            if not is_valid(query=launch_params, secret="ТЫ_ПИДОР"):
                return -100
            else:
                return launch_params.get('vk_user_id')
        else:
            return -100

    def validate_user(self, id, request):
        launch_params = request.headers.get('xvk')
        launch_params = "https://vargasoff.com:8000?" + launch_params
        launch_params = dict(parse_qsl(urlparse(launch_params).query, keep_blank_values=True))

        if not str(launch_params.get('vk_user_id')) == str(id):
            return False
        else:
            return True

    def checkuser(self, id, request):
        launch_params = request.headers.get('xvk')
        launch_params = "https://vargasoff.com:8000?" + launch_params
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

        # TODO Добавить проверку что пользователь является участником митинга

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

        query = "select count(idcomments) from comments where idcomments = %s and ownerid = %s"
        data = (_comment, _id)
        cursor.execute(query, data)
        for item in cursor:
            for value in item:
                if value < 1:
                    return {'success': False, 'failed': 'Comment doesnt exists'}

        query = "delete from comments where idcomments = %s and owner_id = %s;"
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

            query = "update meetings set ismoderated = 1 where id = %s;"
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
