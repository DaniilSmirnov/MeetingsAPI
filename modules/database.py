import mysql.connector
from tokens import database, database_user, database_password
import os


def try_cnx():
    return mysql.connector.connect(user=database_user, password=database_password,
                                   host='0.0.0.0',
                                   database=database)


def get_cnx():
    cnx = try_cnx()
    cnx.set_charset_collation(charset='utf8mb4', collation='utf8mb4_unicode_ci')  # its needed because emoji

    return cnx, cnx.cursor()


def get_value(cursor):
    return cursor.fetchone()[0]


def get_dict(cursor, keys):
    keys = list(keys)
    response = []

    data = cursor.fetchone()
    while data is not None:
        response.append(dict(zip(keys, data)))
        data = cursor.fetchone()

    if len(response) == 1:
        return response[0]
    else:
        return response


def get_array(cursor, keys):
    keys = list(keys)
    response = []

    data = cursor.fetchone()
    while data is not None:
        response.append(dict(zip(keys, data)))
        data = cursor.fetchone()

    return response
