from modules.database import get_cnx, get_value, get_dict


def get_geo_be_meet_id(meet_id):
    cnx, cursor = get_cnx()
    query = 'select lat, lon from geoposition where meet_id = %s'
    data = (meet_id,)

    cursor.execute(query, data)

    return get_dict(cursor, cursor.column_names)


'''
NEED TO ALTER TABLE, потому что многих реальных данных и их лучше мигрировать
CREATE TABLE IF NOT EXISTS geoposition(
    geo_id INT AUTO_INCREMENT PRIMARY KEY,
    lat FLOAT NOT NULL,
    lon FLOAT NOT NULL,
    meet_id INT NOT NULL
)  ENGINE=INNODB;
'''
