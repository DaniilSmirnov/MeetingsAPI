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
