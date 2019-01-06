# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import hashlib
import binascii
import struct
import re
import requests
from requests.auth import HTTPDigestAuth
import logging
from datetime import datetime

__version__ = '0.1.1'


AUDIOTEKA_API_URL = "https://proxy3.audioteka.com/pl/MobileService.svc/"
AUDIOTEKA_API_VERSION = "2.3.15"

DEFAULT_HEADERS = {"User-agent": "Android/" + AUDIOTEKA_API_VERSION}

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


def get_categories(
    category_name, page=1, per_page_count=100, samples=False, session=None, headers=None
):
    """
    gets Categories

    :param category_name:
    :param page:
    :param per_page_count:
    :param samples:
    :param session:
    :param headers:
    :return:
    """
    return _post(
        "categories",
        {},
        session,
        {
            "categoryName": category_name,
            "page": page,
            "samples": samples,
            "count": per_page_count,
        },
        headers,
    ).json()


def login(user_login, user_password, session=None, headers=None):
    """
    signing in into Audioteka.

    :param user_login:
    :param user_password:
    :param session:
    :param headers:
    :return: credentials Dict with login data,token and hashed password

    {
        "userLogin": "yyyyyyyyyyyyyyyyy",
        "userPassword": "xxxxxxxxxxxxxx",
        "HashedPassword": "aasssddddeeffrr",
        "AuthenticationToken": "11aaa11a-22bb-33dd-44dd-33aa11cc33cc",
        "Salt": "3666666666",
        "Status": "LoginStatusOk"
    }
    """
    headers = headers if headers else DEFAULT_HEADERS
    headers["XMobileAudiotekaVersion"] = AUDIOTEKA_API_VERSION

    credentials = {"userLogin": user_login, "userPassword": user_password}

    logged_in_data = _post("login", credentials, session, {}, headers).json()
    logged_in_data["HashedPassword"] = _get_hashed_password(
        credentials["userPassword"], logged_in_data["Salt"]
    )
    logged_in_data["userLogin"] = credentials["userLogin"]

    return logged_in_data


def get_shelf(credentials, session=None, headers=None):
    """
    gets personal shelf content

    :param credentials:
    :param session:
    :param headers:
    :return:
    """
    return _post(
        "get_shelf", credentials, session, {"onlyPaid": "false"}, headers
    ).json()


def get_shelf_item(product_id, credentials, session=None, headers=None):
    """
    gets one book details

    :param product_id:
    :param credentials:
    :param session:
    :param headers:
    :return:
    """
    return _post(
        "shelf_item", credentials, session, {"productId": product_id}, headers
    ).json()


def get_chapters(
    tracking_number, line_item_id, credentials, session=None, headers=None
):
    """
    get list of chapters from book

    :param tracking_number:
    :param line_item_id:
    :param credentials:
    :param session:
    :param headers:
    :return:
    """
    return _post(
        "get_chapters",
        credentials,
        session,
        {"lineItemId": line_item_id, "trackingNumber": tracking_number},
        headers,
    ).json()


def get_chapter_file(
    tracking_number,
    line_item_id,
    download_server_url,
    download_server_footer,
    file_name,
    credentials,
    session=None,
    headers=None,
):
    """
    gets chapter file.

    :param tracking_number:
    :param line_item_id:
    :param download_server_url:
    :param download_server_footer:
    :param file_name:
    :param credentials:
    :param session:
    :param headers:

    :return: Requests response
    """
    s = session if session else requests.session()

    if not headers:
        headers = DEFAULT_HEADERS

    headers["XMobileAudiotekaVersion"] = AUDIOTEKA_API_VERSION
    headers["XMobileAppVersion"] = DEFAULT_HEADERS["User-agent"]
    headers["Range"] = "bytes=0-"

    url = (
        download_server_url
        + "?TrackingNumber={0}&LineItemId={1}&FileName={2}&".format(
            tracking_number, line_item_id, file_name
        )
        + download_server_footer
    )

    r = s.get(
        url,
        auth=HTTPDigestAuth(credentials["userLogin"], credentials["HashedPassword"]),
        headers=headers,
    )

    return r


def epoch_to_datetime(aud_dt):
    """
    converts datetime in format: /Date(1545693401480+0100)/ into Datetime

    :param aud_dt:
    :return:
    """
    result = re.search(r"Date\((.*)\+(.*)\)", aud_dt)
    epoch_utc = result.group(1)
    local_tz_offset = result.group(2)
    try:
        return datetime.utcfromtimestamp(
            float(epoch_utc) if len(epoch_utc) < 11 else float(epoch_utc) / 1000
        )
    except (TypeError, ValueError) as e:
        logger.error(str(e) + " Input epoch_utc: " + str(epoch_utc))


def _get_hashed_password(user_password, salt):
    """
    calculates hashed password
    Salt can be get calling `login`

    :param user_password:
    :param salt:
    :return:
    """
    salt_bytes = struct.pack(">I", int(salt))
    password_encoded = user_password.encode("utf-16le")

    hash_bytes = hashlib.sha256(salt_bytes + password_encoded).digest()
    hashed_password = binascii.hexlify(salt_bytes + hash_bytes).upper()

    return hashed_password


def _post(endpoint, credentials, session=None, data=None, headers=None):
    d, h = _merge_into_data_and_headers(
        credentials, data, headers if headers else DEFAULT_HEADERS
    )
    s = session if session else requests.session()
    #
    r = s.post(AUDIOTEKA_API_URL + endpoint, data=d, headers=h)
    j = r.json()
    if j == "login_failed":
        r.status_code = 401
        r.reason = "Login failed"
    elif j == "item_not_found":
        r.status_code = 404
        r.reason = "Item not found"
    r.raise_for_status()
    return r


def _merge_into_data_and_headers(credentials, data, headers):
    if not credentials:
        return data, headers

    ret_data = dict()
    ret_headers = dict()
    ret_data["userLogin"] = credentials["userLogin"]
    if "userPassword" in credentials:
        ret_data["userPassword"] = credentials["userPassword"]
    else:
        ret_headers["XMobileAudiotekaVersion"] = AUDIOTEKA_API_VERSION
        ret_headers["XMobileTokenAuthentication"] = credentials["AuthenticationToken"]
        ret_headers["XMobileUserLogin"] = credentials["userLogin"]

    return _merge_dicts(data, ret_data), _merge_dicts(ret_headers, headers)


def _merge_dicts(*dict_args):
    result = {}
    for dictionary in dict_args:
        result.update(dictionary)
    return result
