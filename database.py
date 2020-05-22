import mysql.connector
from tokens import database, database_user, database_password
import os


def try_cnx():
    return mysql.connector.connect(user=database_user, password=database_password,
                                  host='0.0.0.0',
                                  database=database)


def get_cnx():
    try:
        cnx = try_cnx()
    except BaseException:
        os.system('sudo service mysql start') #restarting mysql
        cnx = try_cnx()

    cnx.set_charset_collation(charset='utf8mb4', collation='utf8mb4_unicode_ci') #its needed because emoji

    return cnx


def select_query(query, data=None, offset=None, decompose=None):
    cnx = get_cnx()
    cursor = cnx.cursor()
    if offset is not None:
        query += " limit " + str(offset) + ",5"
    if data is not None:
        cursor.execute(query, data)
    else:
        cursor.execute(query)

    if decompose is None:
        return cursor.fetchall()
    elif decompose is 'value':
        return decompose_to_value(cursor.fetchall())
    elif decompose is 'dict':
        return decompose_to_dict(cursor.fetchall())


def decompose_to_dict(cursor):
    keys = list(cursor.column_names)
    response = []

    data = cursor.fetchone()
    while data is not None:
        response.append(dict(zip(keys, data)))
        data = cursor.fetchone()

    return response


def decompose_to_value(cursor):
    return cursor.fetchone()[0]


def insert_query(query, data=None):
    cnx = get_cnx()
    cursor = cnx.cursor()

    if data is not None:
        cursor.execute(query, data)
    else:
        cursor.execute(query)

    cnx.commit()
