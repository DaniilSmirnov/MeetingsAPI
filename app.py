from flask import Flask
from flask_restful import Resource, Api, reqparse
from flask import request
import mysql.connector
from flask_cors import CORS
import hashlib
from base64 import b64encode
from collections import OrderedDict
from hashlib import sha256
from hmac import HMAC
from urllib.parse import urlparse, parse_qsl, urlencode

app = Flask(__name__)

app.config['CORS_HEADERS'] = 'Access-Control-Allow-Origin: *'

cors = CORS(app)
api = Api(app)


class TestConnection(Resource):
    def get(self):
        return {'status': 'success'}


class AddMeet(Resource):
    def post(self):

        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str)
        parser.add_argument('description', type=str)
        parser.add_argument('owner_id', type=int)
        parser.add_argument('start', type=str)
        parser.add_argument('finish', type=str)
        parser.add_argument('photo', type=str)
        args = parser.parse_args()

        _name = args['name']
        _description = args['description']
        _owner_id = args['owner_id']
        _start = args['start']
        _finish = args['finish']
        _photo = args['photo']

        if (len(_name) == 0) or _name.isspace() or _name.isdigit():
            return {'failed': 'invalid name'}
        if len(_description) == 0 or _description.isspace() or _description.isdigit():
            return {'failed': 'invalid name'}

        if 'xvk' in request.headers:
            if not AuthUser.check_sign(AuthUser, request):
                return {'failed': '403'}
        else:
            return {'failed': '403'}

        if not AuthUser.validate_user(self, _owner_id, request):
            return {'failed': '403'}

        try:
            cnx = mysql.connector.connect(user='root', password='misha_benich228',
                                          host='0.0.0.0',
                                          database='meets')

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
            return {'error': str(e)}


class GetMeets(Resource):
    def get(self):
        try:

            def ismember(meet, id):
                cnx = mysql.connector.connect(user='root', password='misha_benich228',
                                              host='0.0.0.0',
                                              database='meets')

                cursor = cnx.cursor(buffered=True)
                query = "select count(id) from meetings where id = %s and id in (select idmeeting from participation where idmember = %s);"
                data = (meet, id)
                cursor.execute(query, data)

                for item in cursor:
                    for value in item:
                        if value == 1:
                            return 1
                        else:
                            return 0

                cnx.close()

            parser = reqparse.RequestParser()
            parser.add_argument('id', type=int)
            args = parser.parse_args()

            _id_client = args['id']

            if 'xvk' in request.headers:
                if not AuthUser.check_sign(AuthUser, request):
                    return {'failed': '403'}
            else:
                return {'failed': '403'}

            cnx = mysql.connector.connect(user='root', password='misha_benich228',
                                          host='0.0.0.0',
                                          database='meets')

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
                    if i == 4:
                        meet.update({'members_amount': value})
                    if i == 5:
                        meet.update({'start': str(value)})
                    if i == 6:
                        meet.update({'finish': str(value)})
                    if i == 8:
                        meet.update({'photo': str(value)})
                    if i == 9:
                        meet.update({'ismember': ismember(id, _id_client)})
                    i += 1
                response.append(meet)
            cursor.close()
            cnx.close()
            return response
        except BaseException as e:
            cursor.close()
            cnx.close()
            return str(e)


class GetUserMeets(Resource):
    def get(self):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('id', type=int)
            args = parser.parse_args()

            _id_client = args['id']

            if 'xvk' in request.headers:
                if not AuthUser.check_sign(AuthUser, request):
                    return {'failed': '403'}
            else:
                return {'failed': '403'}

            cnx = mysql.connector.connect(user='root', password='misha_benich228',
                                          host='0.0.0.0',
                                          database='meets')

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
            return str(e)


class AddMeetMember(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('id', type=int)
        parser.add_argument('meet', type=int)
        args = parser.parse_args()

        _id_client = args['id']
        _meet = args['meet']

        if 'xvk' in request.headers:
            if not AuthUser.check_sign(AuthUser, request):
                return {'failed': '403'}
        else:
            return {'failed': '403'}

        try:
            cnx = mysql.connector.connect(user='root', password='misha_benich228',
                                          host='0.0.0.0',
                                          database='meets')

            cursor = cnx.cursor(buffered=True)

            query = "select count(idmember) from participation where idmember = %s and idmeeting = %s;"
            data = (_id_client, _meet, )
            cursor.execute(query, data)

            for item in cursor:
                for value in item:
                    if value != 0:
                        return {'failed': 'User is in meeting yet'}

            query = "insert into participation values (default, %s, %s);"
            data = (_meet, _id_client, )
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
            return {'success': False}


class RemoveMeetMember(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('id', type=int)
        parser.add_argument('meet', type=int)
        args = parser.parse_args()
        try:
            cnx = mysql.connector.connect(user='root', password='misha_benich228',
                                          host='0.0.0.0',
                                          database='meets')

            cursor = cnx.cursor()

            _id_client = args['id']
            _meet = args['meet']

            if 'xvk' in request.headers:
                if not AuthUser.check_sign(AuthUser, request):
                    return {'failed': '403'}
            else:
                return {'failed': '403'}

            query = "select count(idmember) from participation where idmember = %s and idmeeting = %s;"
            data = (_id_client, _meet, )
            cursor.execute(query, data)

            for item in cursor:
                for value in item:
                    print(value)
                    if value == 0:
                        return {'failed': 'user is not in meet'}

            query = "delete from participation where idmember = %s and idmeeting = %s;"
            data = (_id_client, _meet, )
            cursor.execute(query, data)
            cnx.commit()
            query = "update meetings set members_amount = members_amount -1 where id = %s and members_amount > 0"
            data = (_meet, )
            cursor.execute(query, data)
            cnx.commit()

            cursor.close()
            cnx.close()
            return {'success': True}
        except BaseException:
            return {'success': False}


class AuthUser(Resource):
    def check_sign(self, request):
        def is_valid(*, query: dict, secret: str) -> bool:
            """Check VK Apps signature"""
            vk_subset = OrderedDict(sorted(x for x in query.items() if x[0][:3] == "vk_"))
            hash_code = b64encode(HMAC(secret.encode(), urlencode(vk_subset, doseq=True).encode(), sha256).digest())
            decoded_hash_code = hash_code.decode('utf-8')[:-1].replace('+', '-').replace('/', '_')
            return query["sign"] == decoded_hash_code

        if 'xvk' in request.headers:
            launch_params = request.headers.get('xvk')
            launch_params = "https://vargasoff.com:8000?" + launch_params
            launch_params = dict(parse_qsl(urlparse(launch_params).query, keep_blank_values=True))

            if not is_valid(query=launch_params, secret="VUc7I09bHOUYWjfFhx20"):
                return False
            else:
                return True
        else:
            return False

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
        data = (id, )
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
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('id', type=int)
        parser.add_argument('meet', type=int)
        parser.add_argument('comment', type=str)
        args = parser.parse_args()

        cnx = mysql.connector.connect(user='root', password='misha_benich228',
                                      host='0.0.0.0',
                                      database='meets')

        cursor = cnx.cursor(buffered=True)

        _id_client = args['id']
        _meet = args['meet']
        _comment = args['comment']

        if 'xvk' in request.headers:
            if not AuthUser.check_sign(AuthUser, request):
                return {'failed': '403'}
        else:
            return {'failed': '403'}

        query = "insert into comments values (default, %s, %s, %s);"
        data = (_comment, _id_client, _meet)
        cursor.execute(query, data)
        cnx.commit()

        cursor.close()
        cnx.close()
        return {'success': True}


class GetMeetComments(Resource):
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('meet', type=str)
        args = parser.parse_args()

        cnx = mysql.connector.connect(user='root', password='misha_benich228',
                                      host='0.0.0.0',
                                      database='meets')

        cursor = cnx.cursor(buffered=True)

        _meet = args['meet']

        if 'xvk' in request.headers:
            if not AuthUser.check_sign(AuthUser, request):
                return {'failed': '403'}
        else:
            return {'failed': '403'}

        #TODO Добавить проверку что пользователь является участником митинга

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
    def delete(self):
        parser = reqparse.RequestParser()
        parser.add_argument('comment', type=int)
        parser.add_argument('id', type=int)

        args = parser.parse_args()

        cnx = mysql.connector.connect(user='root', password='misha_benich228',
                                      host='0.0.0.0',
                                      database='meets')

        cursor = cnx.cursor(buffered=True)

        _comment = args['comment']
        _id = args['id']

        if 'xvk' in request.headers:
            if not AuthUser.check_sign(AuthUser, request):
                return {'failed': '403'}
        else:
            return {'failed': '403'}

        query = "select count(idcomments)>0 from comments where idcomments = %s"
        data = (_comment,)
        cursor.execute(query, data)
        for item in cursor:
            for value in item:
                if str(value) != "True":
                    return {'success': False, 'failed': 'Comment doesnt exists'}

        query = "delete from comments where idcomments = %s;"
        cursor.execute(query, data)
        cnx.commit()

        cursor.close()
        cnx.close()
        return {'success': False}


class ApproveMeet(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('meet', type=int)
        parser.add_argument('id', type=int)

        args = parser.parse_args()

        cnx = mysql.connector.connect(user='root', password='misha_benich228',
                                      host='0.0.0.0',
                                      database='meets')

        cursor = cnx.cursor(buffered=True)

        _meet = args['meet']
        if 'xvk' in request.headers:
            if not AuthUser.check_sign(AuthUser, request):
                return {'failed': '403'}
        else:
            return {'failed': '403'}

        _id = args['id']
        if AuthUser.checkuser(AuthUser, _id, request):
            query = "select ismoderated from meetings where id = %s;"
            data = (_meet, )
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
        parser.add_argument('id', type=int)
        args = parser.parse_args()

        cnx = mysql.connector.connect(user='root', password='misha_benich228',
                                      host='0.0.0.0',
                                      database='meets')

        cursor = cnx.cursor(buffered=True)

        _meet = args['meet']
        if 'xvk' in request.headers:
            if not AuthUser.check_sign(AuthUser, request):
                return {'failed': '403'}
        else:
            return {'failed': '403'}

        _id = args['id']
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
            parser = reqparse.RequestParser()
            parser.add_argument('id', type=int)

            args = parser.parse_args()

            if 'xvk' in request.headers:
                if not AuthUser.check_sign(AuthUser, request):
                    return {'failed': '403'}
            else:
                return {'failed': '403'}

            _id = args['id']
            if AuthUser.checkuser(AuthUser, _id, request):

                cnx = mysql.connector.connect(user='root', password='misha_benich228',
                                              host='0.0.0.0',
                                              database='meets')

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
#11

if __name__ == '__main__':
    context = ('/etc/ssl/vargasoff.ru.crt', '/etc/ssl/private.key')
    app.run(host='0.0.0.0', port='8000', ssl_context=context)
