from base64 import b64encode
from collections import OrderedDict
from hashlib import sha256
from hmac import HMAC
from urllib.parse import urlparse, parse_qsl, urlencode
from helpers import get_cnx
from tokens import auth_secret


def check_vk_viewer_group_role(request):
    launch_params = request.referrer
    launch_params = dict(parse_qsl(urlparse(launch_params).query, keep_blank_values=True))
    role = launch_params.get('vk_viewer_group_role')
    return role == 'admin'


def check_sign(request):
    def is_valid(*, query: dict, secret: str) -> bool:
        vk_subset = OrderedDict(sorted(x for x in query.items() if x[0][:3] == "vk_"))
        hash_code = b64encode(HMAC(secret.encode(), urlencode(vk_subset, doseq=True).encode(), sha256).digest())
        decoded_hash_code = hash_code.decode('utf-8')[:-1].replace('+', '-').replace('/', '_')
        try:
            return query["sign"] == decoded_hash_code
        except KeyError:
            return query.get("sign") == decoded_hash_code

    launch_params = request.referrer

    launch_params = dict(parse_qsl(urlparse(launch_params).query, keep_blank_values=True))

    if is_valid(query=launch_params, secret=auth_secret):
        return int(launch_params.get('vk_user_id'))
    else:
        return - 100


def check_user(id, request):
    if str(check_sign(request)) != str(id):
        return {'failed': '403'}

    cnx = get_cnx()

    cursor = cnx.cursor(buffered=True)

    query = "select rights_level from members where idmembers = %s;"
    data = (id,)
    cursor.execute(query, data)
    for item in cursor:
        for value in item:
            return str(value) == "admin"
