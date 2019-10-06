from flask import Flask
from flask_restful import Resource, Api, reqparse
from flask import request
import mysql.connector
from flask_cors import CORS
import json

app = Flask(__name__)

app.config['CORS_HEADERS'] = 'Access-Control-Allow-Origin: *'

cors = CORS(app)
api = Api(app)

cnx = mysql.connector.connect(user='root', password='i130813',
                                  host='127.0.0.1',
                                  database='mydb')


class TestConnection(Resource):
    def get(self):
        return {'status': 'success'}


class AddMeet(Resource):
    def post(self):

        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str)
        parser.add_argument('description', type=str)
        parser.add_argument('owner_id', type=int)
        parser.add_argument('sig', type=str)
        parser.add_argument('start', type=str)
        parser.add_argument('finish', type=str)
        args = parser.parse_args()

        _name = args['name']
        _signature = args['sig']
        _description = args['description']
        _owner_id = args['owner_id']
        _start = args['start']
        _finish = args['finish']

        try:
            cursor = cnx.cursor(buffered=True)
            query = "select sig from members where idmembers = %s and sig = %s"
            data = (_owner_id, _signature,)
            cursor.execute(query, data)

            for item in cursor:
                for value in item:
                    if str(value) == _signature:
                        query = "insert into meetings values (default, %s, %s, %s, default, %s, %s, default)"
                        data = (_name, _description, _owner_id, _start, _finish)
                        cursor.execute(query, data)
                        cnx.commit()
                        return {'status': 'success'}
                    else:
                        return {'status': 'Signature is not valid'}

            return {'status': "failed"}

        except BaseException:
            return {'status': "failed"}


class GetMeets(Resource):
    def get(self):
        try:
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
                        id = str(value)
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
                    i += 1
                #response.update({'meet' + id: meet})
                response.append(meet)
            return response
        except BaseException as e:
            return str(e)


class AddMeetMember(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('id', type=int)
        parser.add_argument('signature', type=str)
        parser.add_argument('meet', type=int)
        args = parser.parse_args()

        _id_client = args['id']
        _signature = args['signature']
        _meet = args['meet']

        try:
            cursor = cnx.cursor(buffered=True)
            query = "select sig from members where idmembers = %s and sig = %s"
            data = (_id_client, _signature,)
            cursor.execute(query, data)

            for item in cursor:
                for value in item:
                    if str(value) == _signature:

                        query = "select idmember from participation where idmember = %s and idmeeting = %s;"
                        data = (_id_client, _meet, )
                        cursor.execute(query, data)

                        for item in cursor:
                            for value in item:
                                if str(value) == str(_id_client):
                                    return {'failed': 'User is in meeting yet'}

                        query = "insert into participation values (default, %s, %s);"
                        data = (_meet, _id_client, )
                        cursor.execute(query, data)
                        query = "update meetings set members_amount = members_amount + 1 where id = %s"
                        data = (_meet,)
                        cursor.execute(query, data)
                        cnx.commit()
                        return {'status': 'success'}
                    else:
                        return {'failed': 'signature is not valid'}

                    return {'status': 'failed'}

        except BaseException as e:
            return e


class RemoveMeetMember(Resource):
    def delete(self):
        parser = reqparse.RequestParser()
        parser.add_argument('id', type=int)
        parser.add_argument('signature', type=str)
        parser.add_argument('meet', type=int)
        args = parser.parse_args()

        cursor = cnx.cursor(buffered=True)

        _id_client = args['id']
        _signature = args['signature']
        _meet = args['meet']

        query = "select sig from members where idmembers = %s and sig = %s"
        data = (_id_client, _signature,)
        cursor.execute(query, data)

        for item in cursor:
            for value in item:
                if str(value) == _signature:

                    query = "select idmember from participation where idmember = %s and idmeeting = %s;"
                    data = (_id_client, _meet, )
                    cursor.execute(query, data)

                    for item in cursor:
                        for value in item:
                            if str(value) != str(_id_client):
                                return {'failed': 'user is not on meet'}

                    query = "delete from participation where idmember = %s and idmeeting = %s;"
                    data = (_meet, _id_client, )
                    cursor.execute(query, data)
                    cnx.commit()
                    query = "update meetings set members_amount = members_amount -1 where id = %s and members_amount > 0"
                    data = (_meet, )
                    cursor.execute(query, data)
                    cnx.commit()
                    return {'status': 'success'}
        else:
            return {'failed': 'signature is not valid'}

        return {'status': 'failed'}


class AuthUser(Resource):
    def post(self):
        #https://vk.com/dev/vk_apps_docs3?f=6.1+подписью+параметров+запуска
        parser = reqparse.RequestParser()
        parser.add_argument('id', type=int)
        parser.add_argument('signature', type=str)
        args = parser.parse_args()

        _id_client = args['id']
        _signature = args['signature']

        query = "update members set signature = %s where id = ;"

    def checkuser(self, id, sig):
        cursor = cnx.cursor(buffered=True)

        query = "select sig from members where idmembers = %s and sig = %s"
        data = (id, sig)
        cursor.execute(query, data)

        for item in cursor:
            for value in item:
                if str(value) == str(sig):
                    query = "select rights_level from members where sig = %s;"
                    data = (sig,)
                    cursor.execute(query, data)
                    for item in cursor:
                        for value in item:
                            if str(value) == "admin":
                                return True
                            else:
                                return False


class AddComment(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('id', type=int)
        parser.add_argument('signature', type=str)
        parser.add_argument('meet', type=int)
        parser.add_argument('comment', type=str)
        args = parser.parse_args()

        cursor = cnx.cursor(buffered=True)

        _id_client = args['id']
        _signature = args['signature']
        _meet = args['meet']
        _comment = args['comment']

        query = "select sig from members where idmembers = %s and sig = %s"
        data = (_id_client, _signature,)
        cursor.execute(query, data)

        for item in cursor:
            for value in item:
                if str(value) == _signature:

                    query = "insert into comments values (default, %s, %s, %s);"
                    data = (_comment, _id_client, _meet)
                    cursor.execute(query, data)
                    cnx.commit()
                    return {'status': 'success'}
                else:
                    return {'failed': 'signature is not valid'}

        return {'status': 'failed'}


class GetMeetComments(Resource):
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('meet', type=str)
        args = parser.parse_args()

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
                    id = str(value)
                if i == 1:
                    comment.update({'comment': value})
                if i == 2:
                    comment.update({'ownerid': value})
                if i == 3:
                    comment.update({'meetingid': value})

                i += 1
            response.append(comment)

        return response


class RemoveComment(Resource):
    def delete(self):
        parser = reqparse.RequestParser()
        parser.add_argument('comment', type=int)
        parser.add_argument('id', type=int)
        parser.add_argument('sig', type=int)

        args = parser.parse_args()

        cursor = cnx.cursor(buffered=True)

        _comment = args['comment']
        _id = args['id']
        _sig = args['sig']

        exec = True

        query = "select count(idcomments)>0 from comments where idcomments = %s"
        data = (_comment,)
        cursor.execute(query, data)
        for item in cursor:
            for value in item:
                if str(value) != "True":
                    return {'status': 'Comment doesnt exists'}

        if exec:
            query = "delete from comments where idcomments = %s;"
            cursor.execute(query, data)
            cnx.commit()
            return {'status': 'success'}


class ApproveMeet(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('meet', type=int)
        parser.add_argument('id', type=int)
        parser.add_argument('sig', type=int)

        args = parser.parse_args()

        cursor = cnx.cursor(buffered=True)

        _meet = args['meet']
        _id = args['id']
        _sig = args['sig']

        if AuthUser.checkuser(self, _id, _sig):
            query = "update meetings set ismoderated = 1 where id = %s;"
            data = (_meet,)
            cursor.execute(query, data)
            cnx.commit()
            return {'status': 'success'}
        else:
            return {'status': 'failed'}


class DeApproveMeet(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('meet', type=int)
        parser.add_argument('id', type=int)
        parser.add_argument('sig', type=int)
        args = parser.parse_args()

        cursor = cnx.cursor(buffered=True)

        _meet = args['meet']
        _id = args['id']
        _sig = args['sig']
        if AuthUser.checkuser(self, _id, _sig):
            query = "update meetings set ismoderated = 0 where id = %s;"
            data = (_meet,)
            cursor.execute(query, data)
            cnx.commit()
            return {'status': 'success'}
        else:
            return {'status': 'failed'}


class GetAllMeets(Resource):
    def get(self):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('id', type=int)
            parser.add_argument('signature', type=int)

            args = parser.parse_args()

            _id = args['id']
            _sig = args['signature']
            if AuthUser.checkuser(AuthUser, _id, _sig):

                cursor = cnx.cursor(buffered=True)
                query = "select * from meetings;"

                response = {}
                cursor.execute(query)
                for item in cursor:
                    i = 0
                    meet = {}
                    for value in item:
                        if i == 0:
                            meet.update({'id': value})
                            id = str(value)
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
                            meet.update({'approved': str(value)})
                        i += 1
                    response.update({'meet' + id: meet})

                return response
            else:
                return {'status': 'failed'}
        except BaseException as e:
            return str(e)


api.add_resource(TestConnection, '/TestConnection')

api.add_resource(GetMeets, '/GetMeets')
api.add_resource(AddMeet, '/AddMeet')

api.add_resource(AddMeetMember, '/AddMeetMember')
api.add_resource(RemoveMeetMember, '/RemoveMeetMember')

api.add_resource(GetMeetComments, '/GetMeetComments')
api.add_resource(AddComment, '/AddComment')
api.add_resource(RemoveComment, '/RemoveComment')

api.add_resource(ApproveMeet, '/admin/Approve')
api.add_resource(DeApproveMeet, '/admin/DeApprove')
api.add_resource(GetAllMeets, '/admin/GetAllMeets')
#11

if __name__ == '__main__':
    app.run(debug=True)
