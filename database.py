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
        os.system('sudo service mysql start')
        cnx = try_cnx()

    cnx.set_charset_collation(charset='utf8mb4', collation='utf8mb4_unicode_ci')

    return cnx


def select_query(query, data=None, offset=None):
    cnx = get_cnx()
    cursor = cnx.cursor()
    if offset is not None:
        query += " limit " + str(offset) + ",5"
    if data is not None:
        cursor.execute(query, data)
    else:
        cursor.execute(query)

    return cursor.fetchall()


def insert_query(query, data=None):
    cnx = get_cnx()
    cursor = cnx.cursor()

    if data is not None:
        cursor.execute(query, data)
    else:
        cursor.execute(query)

    cnx.commit()
