from auth import *
from flask import Flask
from flask import request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_restful import Resource, Api, reqparse
from helpers import *
from recognize import search

app = Flask(__name__)

app.config['CORS_HEADERS'] = 'Access-Control-Allow-Origin: *'

cors = CORS(app)
api = Api(app)
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["5 per second"],
)


class IsFirst(Resource):
    def get(self):
        try:
            _id = check_sign(request)
            if _id == -100:
                return {'failed': 403}

            cnx = get_cnx()

            cursor = cnx.cursor(buffered=True)

            query = "select count(idmembers) from members where idmembers = %s;"
            data = (_id,)
            cursor.execute(query, data)

            for item in cursor:
                for value in item:
                    if value == 0:
                        query = "insert into members values(%s, default)"
                        data = (_id,)
                        cursor.execute(query, data)
                        cnx.commit()
                        return True
                    return value == 0

        except BaseException:
            return {'success': False}


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
            if (len(_name) == 0) or _name.isspace() or _name.isdigit() or len(_name) > 45 or search(_name):
                return {'failed': 'Некорректное название петиции'}
            if len(_description) == 0 or _description.isspace() or _description.isdigit() or len(
                    _description) > 254 or search(_description):
                return {'failed': 'Некорректное описание петиции'}
            if len(_start) == 0 or _start.isspace() or _start == 'undefined:00' or _start == '0000-00-00 00:00:00:00':
                return {'failed': 'Некорректная дата начала петиции'}
            if len(_finish) == 0 or _finish.isspace() or str(
                    _finish) == 'undefined:00' or _finish == '0000-00-00 00:00:00:00':
                return {'failed': 'Некорректная дата окончания петиции'}
            if len(_photo) == 0 or _photo.isspace() or _photo.isdigit():
                return {'failed': 'Некорректная обложка петиции'}
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

            cnx = get_cnx()

            cursor = cnx.cursor(buffered=True)
            query = "select * from meetings where finish > current_date() and ismoderated = 1 order by members_amount " \
                    "asc;"

            cursor.execute(query)

            return prepare_meet(cursor, _id)
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

            cnx = get_cnx()

            cursor = cnx.cursor(buffered=True)
            query = "select * from meetings where id = %s and ismoderated = 1;"

            data = (_meet,)
            cursor.execute(query, data)

            return prepare_meet(cursor, _id)
        except BaseException as e:
            return {'failed': 'Произошла ошибка на сервере. Сообщите об этом.', 'error': str(e)}


class GetUserMeets(Resource):
    def get(self):
        try:
            _id = check_sign(request)
            if _id == -100:
                return {'failed': 403}

            cnx = get_cnx()

            cursor = cnx.cursor(buffered=True)
            query = "select * from meetings where finish > current_date() and ismoderated = 1 and id in (select " \
                    "idmeeting from participation where idmember = %s) order by members_amount asc; "
            data = (_id,)
            cursor.execute(query, data)

            return prepare_meet(cursor, _id)
        except BaseException as e:
            return {'failed': 'Произошла ошибка на сервере. Сообщите об этом.', 'error': str(e)}


class GetOwneredMeets(Resource):
    def get(self):
        try:
            _id = check_sign(request)
            if _id == -100:
                return {'success': False}, 403

            cnx = get_cnx()

            cursor = cnx.cursor(buffered=True)
            query = "select * from meetings where ownerid = %s;"
            data = (_id,)
            cursor.execute(query, data)

            return prepare_meet(cursor, _id)
        except BaseException as e:
            return {'failed': 'Произошла ошибка на сервере. Сообщите об этом.', 'error': str(e)}


class GetExpiredUserMeets(Resource):
    def get(self):
        try:
            _id = check_sign(request)
            if _id == -100:
                return {'success': False}, 403

            cnx = get_cnx()

            cursor = cnx.cursor(buffered=True)
            query = "select * from meetings where finish < current_date() and ismoderated = 1 and id in (select " \
                    "idmeeting from participation where idmember = %s) order by members_amount asc; "
            data = (_id,)
            cursor.execute(query, data)

            return prepare_meet(cursor, _id)
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
        if (_comment.find(" ") == -1) and (len(_comment) > 15) or (len(_comment) > 45):
            return {'failed': 'Некорректный текст комментария'}
        if check_url(_comment):
            return {'failed': 'Нельзя отправлять ссылки в комментарии'}
        if (len(_comment) < 4) and (_comment[0] == " " or _comment[len(_comment) - 1] == " "):
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
        for item in cursor:
            i = 0
            comment = {}
            for value in item:
                if i == 0:
                    comment.update({'id': value})
                    comment.update({'isliked': is_liked(_id, value)})
                if i == 1:
                    comment.update({'comment': value})
                if i == 2:
                    data = get_user_data(value)
                    comment.update({'ownerid': value})
                    comment.update({'owner_name': data[0].get('first_name')})
                    comment.update({'owner_surname': data[0].get('last_name')})
                    comment.update({'owner_photo': data[0].get('photo_100')})
                if i == 3:
                    comment.update({'meetingid': value})
                if i == 4:
                    comment.update({'rating': value})
                i += 1
            response.append(comment)

        return response


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
                        query = "insert into participation values (default, %s, %s);"
                        data = (_meet, id)
                        cursor.execute(query, data)
                        query = "update meetings set members_amount = members_amount + 1 where id = %s;"
                        data = (_meet,)
                        cursor.execute(query, data)
                        cnx.commit()

                    i += 1

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
                        return {'failed': 'already deapproved'}

            query = "update meetings set ismoderated = 0 where id = %s;"
            data = (_meet,)
            cursor.execute(query, data)
            query = "update meetings set isvisible = 0 where id = %s;"
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
            cursor.execute(query, data)
            for item in cursor:
                for value in item:
                    if value == 0:
                        return {'failed': 'already deapproved'}

            query = "update meetings set isvisible = 0 where id = %s;"
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

                cnx = get_cnx()

                cursor = cnx.cursor(buffered=True)
                query = "select * from meetings;"
                cursor.execute(query)

                return prepare_meet(cursor, _id)
            else:

                return {'success': False}
        except BaseException as e:
            return {'failed': 'Произошла ошибка на сервере. Сообщите об этом.', 'error': str(e)}


class GeoPosition(Resource):
    def get(self):
        _id = check_sign(request)
        if _id == -100:
            return {'success': False}, 403

        parser = reqparse.RequestParser()
        parser.add_argument('meet', type=str)
        args = parser.parse_args()

        _meet = args['meet']

        cnx = get_cnx()
        cursor = cnx.cursor(buffered=True)

        query = "select lat, lon from geoposition where userid in (select idmember from participation where idmeeting = %s and idmember <> %s)"
        data = (_meet, _id)
        cursor.execute(query, data)

        response = []
        for item in cursor:
            i = 0
            cord = {}
            for value in item:
                if i == 0:
                    cord.update({'lat': value})
                if i == 1:
                    cord.update({'lon': value})
                i += 1

        return response

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
            return {'success': False}, 403


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
