import mysql.connector


def get_cnx():
    try:
        cnx = mysql.connector.connect(user='meetings_user', password='misha_benich228',
                                      host='0.0.0.0',
                                      database='meets')

    except BaseException:
        import os
        os.system('sudo service mysql start')

        cnx = mysql.connector.connect(user='meetings_user', password='misha_benich228',
                                      host='0.0.0.0',
                                      database='meets')

    cnx.set_charset_collation(charset='utf8mb4', collation='utf8mb4_unicode_ci')

    return cnx


def select_query(query, data=None):
    cnx = get_cnx()
    cursor = cnx.cursor()

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

    return cursor.fetchall()