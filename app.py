from modules.auth import *
from flask import Flask
from flask import request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_restful import Resource, Api, reqparse
from modules.helpers import *
from modules.database import *
from modules.recognize import search
from user.user_functions import get_user
from meetings.meetings_functions import get_meet

app = Flask(__name__)

app.config['CORS_HEADERS'] = 'Access-Control-Allow-Origin: *'

cors = CORS(app)
api = Api(app)
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["5 per second"],
)


@app.before_request
def check_auth():
    if str(request.method) in ['OPTIONS']:
        return 'ok', 200

    if not check_sign(request):
        return 'YOU SHOULD NOT PASS!', 403


class GetStartPage(Resource):
    def get(self):
        _id = check_sign(request)

        return {'user': get_user(_id)}


class AddMeet(Resource):
    decorators = [limiter.limit("3 per day")]

    def post(self):
        _id = check_sign(request)
        if _id == -100:
            return {'failed': 403}

        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str)
        parser.add_argument('description', type=str)
        parser.add_argument('start', type=str)
        parser.add_argument('finish', type=str)
        parser.add_argument('photo', type=str)
        parser.add_argument('isGroup', type=bool)
        args = parser.parse_args()

        _name = args['name']
        _description = args['description']
        _start = args['start']
        _finish = args['finish']
        _photo = args['photo']
        _is_group = args['isGroup']

        if not check_user(_id, request):  # disable content check for admins
            if _name.isspace() or _name.isdigit() or len(_name) > 45 or search(_name):
                return {'failed': 'Некорректное название петиции'}
            if _description.isspace() or _description.isdigit() or len(_description) > 254 or search(_description):
                return {'failed': 'Некорректное описание петиции'}
            if check_url(_description):
                return {'failed': 'Описание не может содержать ссылку'}

        if _is_group:
            if check_vk_viewer_group_role(request):
                _id = get_group_id(request)

        try:
            cnx = get_cnx()

            cursor = cnx.cursor(buffered=True)

            query = "insert into meetings values (default, %s, %s, %s, default, %s, %s, default, %s, null, 1)"
            data = (_name, _description, _id, _start, _finish, compress_blob(_photo))
            cursor.execute(query, data)
            cnx.commit()

            return {'success': 'Ваша петиция отправлена на модерацию, обычно это занимает до трех часов'}

        except BaseException as e:
            return {'failed': 'Произошла ошибка на сервере. Сообщите об этом.', 'error': str(e)}


class GetMeets(Resource):
    def get(self):
        try:
            _id = check_sign(request)
            if _id == -100:
                return {'failed': 403}

            parser = reqparse.RequestParser()
            parser.add_argument('offset', type=int)
            parser.add_argument('needExpired', type=int)
            parser.add_argument('needOwned', type=int)
            parser.add_argument('needParticipated', type=int)
            args = parser.parse_args()

            _offset = args['offset']
            _needParticipated = args['needParticipated']
            _needExpired = args['needExpired']
            _needOwned = args['needOwned']

            cursor = cnx.cursor(buffered=True)

            data = None

            query = "select * from meetings where finish > current_date() and ismoderated = 1 order by members_amount " \
                    "asc;"

            if needParticipated:
                query = "select * from meetings where (finish > current_date()  and ismoderated = 1 and id in (select " \
                        "idmeeting from participation where idmember = %s)) or ownerid = %s order by members_amount asc; "
                data = (_id, _id)

            if _needExpired:
                query = "select * from meetings where finish < current_date() and ismoderated = 1 and id in (select " \
                        "idmeeting from participation where idmember = %s) order by members_amount asc; "
                data = (_id,)

            if _needOwned:
                query = "select * from meetings where ownerid = %s;"
                data = (_id,)

            if data is None:
                cursor.execute(query)
            else:
                cursor.execute(query, data)

            return generate_meet_object(cursor, _id)
        except BaseException as e:
            return {'failed': 'Произошла ошибка на сервере. Сообщите об этом.', 'error': str(e)}


class GetMeet(Resource):
    def get(self):
        try:
            _id = check_sign(request)
            if _id == -100:
                return {'failed': 403}

            parser = reqparse.RequestParser()
            parser.add_argument('meet', type=int)
            args = parser.parse_args()
            _meet = args['meet']

            return get_meet(_meet, _id)
        except BaseException as e:
            return {'failed': 'Произошла ошибка на сервере. Сообщите об этом.', 'error': str(e)}


class AddMeetMember(Resource):
    def post(self):
        _id = check_sign(request)
        if _id == -100:
            return {'failed': 403}

        try:
            parser = reqparse.RequestParser()
            parser.add_argument('meet', type=int)
            args = parser.parse_args()

            _meet = args['meet']

            cnx = get_cnx()

            cursor = cnx.cursor(buffered=True)

            query = "select count(id) from meetings where id = %s and ismoderated = 1;"
            data = (_meet,)
            cursor.execute(query, data)
            for item in cursor:
                for value in item:
                    if value != 1:
                        return {'failed': 'Митинга не существует'}

            query = "select count(idmember) from participation where idmember = %s and idmeeting = %s;"
            data = (_id, _meet)
            cursor.execute(query, data)

            for item in cursor:
                for value in item:
                    if value != 0:
                        return {'failed': 'Вы уже участник митинга'}

            query = "insert into participation values (default, %s, %s);"
            data = (_meet, _id)
            cursor.execute(query, data)
            query = "update meetings set members_amount = members_amount + 1 where id = %s;"
            data = (_meet,)
            cursor.execute(query, data)
            cnx.commit()

            return {'success': True}

        except BaseException as e:
            return {'failed': 'Произошла ошибка на сервере. Сообщите об этом.', 'error': str(e)}


class RemoveMeetMember(Resource):
    def post(self):
        _id = check_sign(request)
        if _id == -100:
            return {'success': False}, 403

        try:
            parser = reqparse.RequestParser()
            parser.add_argument('meet', type=int)
            args = parser.parse_args()

            cnx = get_cnx()

            cursor = cnx.cursor()

            _meet = args['meet']

            query = "select count(idmember) from participation where idmember = %s and idmeeting = %s;"
            data = (_id, _meet,)
            cursor.execute(query, data)

            for item in cursor:
                for value in item:
                    if value == 0:
                        return {'failed': 'user is not in meet'}

            query = "delete from participation where idmember = %s and idmeeting = %s;"
            data = (_id, _meet,)
            cursor.execute(query, data)
            cnx.commit()
            query = "update meetings set members_amount = members_amount -1 where id = %s and members_amount > 0"
            data = (_meet,)
            cursor.execute(query, data)

            try:
                query = 'delete from geoposition where userid = %s;'
                data = (_id,)
                cursor.execute(query, data)

                cnx.commit()
            except BaseException:  # because the user may not have saved the geolocation
                cnx.commit()

            return {'success': True}
        except BaseException:
            return {'failed': 'Произошла ошибка на сервере. Сообщите об этом.'}


class AddComment(Resource):
    def post(self):
        _id = check_sign(request)
        if _id == -100:
            return {'success': False}, 403

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
        if check_url(_comment):
            return {'failed': 'Нельзя отправлять ссылки в комментарии'}
        if len(_comment) < 4:
            return {'failed': 'Вам не кажется, что комментарий слишком короткий?'}

        query = "select count(id) from meetings where id = %s;"
        data = (_meet,)
        cursor.execute(query, data)
        for item in cursor:
            for value in item:
                if value < 1:
                    return {'failed': 'Meet is not exist'}

        query = "insert into comments values (default, %s, %s, %s, default);"
        data = (_comment, _id, _meet)
        cursor.execute(query, data)
        cnx.commit()

        return {'success': True}


class GetMeetComments(Resource):
    def get(self):
        _id = check_sign(request)
        if _id == -100:
            return {'success': False}, 403
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('meet', type=int)
            args = parser.parse_args()

            cnx = get_cnx()

            cursor = cnx.cursor(buffered=True)

            _meet = args['meet']

            query = "select * from comments where meetingid = %s"
            data = (_meet,)

            response = []
            cursor.execute(query, data)
            buf = cursor.fetchall()
            user = prepare_data(buf, 2)

            for row in buf:
                data = user.get(row[2])

                response.append({'id': row[0],
                                 'isliked': is_liked(_id, row[0]),
                                 'comment': row[1],
                                 'ownerid': row[2],
                                 'owner_name': data.get('first_name'),
                                 'owner_surname': data.get('last_name'),
                                 'owner_photo': data.get('photo_100'),
                                 'meetingid': row[3],
                                 'rating': row[4]})

            return response
        except BaseException as e:
            return {'failed': 'Произошла ошибка на сервере. Сообщите об этом.', 'error': str(e)}


class RateComment(Resource):
    def post(self):
        _id = check_sign(request)
        if _id == -100:
            return {'success': False}, 403

        parser = reqparse.RequestParser()
        parser.add_argument('comment', type=int)
        parser.add_argument('act', type=int)
        args = parser.parse_args()

        cnx = get_cnx()

        cursor = cnx.cursor(buffered=True)

        _comment = args['comment']
        _act = args['act']

        query = "select count(idcomments) from comments where idcomments = %s;"
        data = (_comment,)
        cursor.execute(query, data)
        for item in cursor:
            for value in item:
                if value < 1:
                    return {'failed': 'Comment is not exists'}

        query = "select count(idratings) from ratings where iduser = %s and idcomment = %s;"
        data = (_id, _comment)
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
                        query = "delete from ratings where iduser = %s and idcomment = %s;"
                        cursor.execute(query, data)
                        query = "update comments set rating = rating + 1 where idcomments = %s;"
                        data = (_comment,)
                        cursor.execute(query, data)
                        query = "insert into ratings values (default, %s, %s);"
                        data = (_id, _comment)
                        cursor.execute(query, data)
                        cnx.commit()
                        return {'success': True}


class RemoveComment(Resource):
    def post(self):
        _id = check_sign(request)
        if _id == -100:
            return {'success': False}, 403

        parser = reqparse.RequestParser()
        parser.add_argument('comment', type=int)
        args = parser.parse_args()
        _comment = args['comment']

        cnx = get_cnx()
        cursor = cnx.cursor(buffered=True)

        query = "select count(idcomments) from comments where idcomments = %s and ownerid = %s;"
        data = (_comment, _id)
        cursor.execute(query, data)
        for item in cursor:
            for value in item:
                if value < 1:
                    if not check_user(_id, request):
                        return {'failed': 'Comment doesnt exists'}

        query = "delete from comments where idcomments = %s"
        data = (_comment,)
        cursor.execute(query, data)
        cnx.commit()

        return {'status': True}


class ApproveMeet(Resource):
    def post(self):
        _id = check_sign(request)
        if _id == -100:
            return {'success': False}, 403

        parser = reqparse.RequestParser()
        parser.add_argument('meet', type=int)
        args = parser.parse_args()
        cnx = get_cnx()

        cursor = cnx.cursor(buffered=True)

        _meet = args['meet']

        if check_user(_id, request):
            query = "select ismoderated from meetings where id = %s;"
            data = (_meet,)
            cursor.execute(query, data)
            for item in cursor:
                for value in item:
                    if value == 1:
                        return {'failed': 'Уже одобрено'}

            query = "update meetings set ismoderated = 1, approver = %s where id = %s;"
            data = (_id, _meet)
            cursor.execute(query, data)

            query = "select ownerid from meetings where id = %s"
            data = (_meet,)
            cursor.execute(query, data)
            i = 0
            for item in cursor:
                for value in item:
                    query = "insert into participation values (default, %s, %s);"
                    data = (_meet, value)
                    cursor.execute(query, data)
                    query = "update meetings set members_amount = members_amount + 1 where id = %s;"
                    data = (_meet,)
                    cursor.execute(query, data)

                    i += 1

            cnx.commit()
            return {'success': True}
        else:

            return {'success': False}


class DeApproveMeet(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('meet', type=int)
        args = parser.parse_args()

        cnx = get_cnx()

        cursor = cnx.cursor(buffered=True)

        _meet = args['meet']

        if check_user(check_sign(request), request):
            query = "select ismoderated from meetings where id = %s;"
            data = (_meet,)
            cursor.execute(query, data)
            for item in cursor:
                for value in item:
                    if value == 0:
                        return {'failed': 'Уже скрыт'}

            query = "update meetings set ismoderated = 0 where id = %s;"
            data = (_meet,)
            cursor.execute(query, data)

            cnx.commit()

            return {'success': True}
        else:

            return {'success': False}, 403


class DenyMeet(Resource):
    def post(self):
        _id = check_sign(request)
        if _id == -100:
            return {'success': False}, 403

        parser = reqparse.RequestParser()
        parser.add_argument('meet', type=int)
        args = parser.parse_args()

        cnx = get_cnx()

        cursor = cnx.cursor(buffered=True)

        _meet = args['meet']

        if check_user(_id, request):
            query = "select isvisible from meetings where id = %s;"
            data = (_meet,)
            if select_query(query=query, data=data, decompose='value') == 0:
                return {'failed': 'Уже удален'}

            query = "update meetings set isvisible = 0, ismoderated = 0 where id = %s;"
            data = (_meet,)
            cursor.execute(query, data)
            cnx.commit()

            return {'success': True}
        else:

            return {'success': False}


class GetAllMeets(Resource):
    def get(self):
        try:
            _id = check_sign(request)
            if _id == -100:
                return {'success': False}, 403

            if check_user(_id, request):
                return prepare_meet(select_query(query="select * from meetings where isvisible = 1"), _id)
            else:
                return {'success': False}

        except BaseException as e:
            return {'failed': 'Произошла ошибка на сервере. Сообщите об этом.', 'error': str(e)}


class GeoPosition(Resource):
    def get(self):
        if check_sign(request) == -100:
            return {'success': False}, 403

        parser = reqparse.RequestParser()
        parser.add_argument('meet', type=str)
        args = parser.parse_args()

        _meet = args['meet']

        query = "select lat, lon from geoposition where userid in " \
                "(select idmember from participation where idmeeting = %s);"
        data = (_meet,)

        return select_query(query=query, data=data, decompose='dict')

    def post(self):
        try:
            _id = check_sign(request)
            if _id == -100:
                return {'success': False}, 403

            parser = reqparse.RequestParser()
            parser.add_argument('lat', type=str)
            parser.add_argument('long', type=str)
            args = parser.parse_args()

            _lat = args['lat']
            _lon = args['long']

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
            return {'status': 'success'}
        except BaseException as e:
            return {'failed': 'Произошла ошибка на сервере. Сообщите об этом.', 'error': str(e)}


class GetGroupInfo(Resource):
    def get(self):
        try:
            _id = check_sign(request)
            if _id == -100:
                return {'success': False}, 403

            if check_vk_viewer_group_role(request):
                group_id = get_group_id(request)
                data = get_group_data(group_id)
                return {
                    'id': group_id,
                    'name': data[0].get('name'),
                    'photo': data[0].get('photo_100')
                }
            else:
                return {'success': False}, 200
        except BaseException as e:
            return {'failed': 'Произошла ошибка на сервере. Сообщите об этом.', 'error': str(e)}


class GetWidget(Resource):
    def get(self):
        try:
            _id = check_sign(request)
            if _id == -100:
                return {'success': False}, 403

            parser = reqparse.RequestParser()
            parser.add_argument('meet', type=int)
            args = parser.parse_args()
            _meet = args['meet']

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
                        meet.update({'description': value})
                    if i == 3:
                        meet.update({'button': "Открыть"})
                    if i == 8:
                        meet.update({'cover_id': str(value)})
                    i += 1
                rows.append(meet)
            response.update({"title": 'Петиции'})
            response.update({'rows': rows})

            return response
        except BaseException as e:
            return {'failed': 'Произошла ошибка на сервере. Сообщите об этом.', 'error': str(e)}


api.add_resource(IsFirst, '/IsFirst')
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

api.add_resource(GeoPosition, '/GeoPosition')
api.add_resource(GetWidget, '/GetWidget')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port='8000')
