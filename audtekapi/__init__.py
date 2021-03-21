import hashlib
import binascii
import json
import re
import requests
from typing import Dict
from requests.auth import HTTPDigestAuth
import logging
from datetime import datetime

__version__ = "0.3.0"


AUDIOTEKA_API_URL = "https://api-audioteka.audioteka.com"
AUDIOTEKA_API_VERSION = "3.25.1"

DEFAULT_HEADERS = {
    "User-agent": "Audioteka/3.25.1 (1802) Android/11 (Phone;HAL-9000)"
}  # {"User-agent": "Android/" + AUDIOTEKA_API_VERSION + "(S;Phone;11;S)"}

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

LoggedInData = {
    "token": str,
    "refresh_id": str,
    "expires_at": str,
    "device_id": str
}


def get_categories(logged_in_data, session=None, headers=None):
    """
    "app:category-list":
        "href": "/v2/categories",
        "title": "Browse categories
    """
    return _get("/v2/categories", logged_in_data, session, headers).json()


def get_home_v2(logged_in_data, session=None, headers=None):
    """
    "app:screen:home": {
        "href": "/v2/me/screen",
        "title": "User's homescreen v2"
    },"""
    return _get("/v2/me/screen", logged_in_data, session, headers).json()


def login(
    email: str,
    password: str,
    device_id: str,
    session=None,
    headers: [Dict, None] = None,
) -> LoggedInData:
    """
    Login (authenticate) user

    :param email:
    :param password:
    :param device_id:
    :param session:
    :param headers:
    :return:

    {
        "token": "aaaaBBbaaaaaccccccccccddeee33333333334444444444aaaaaaaaaammmmmmmmnnnnnnnnnnn",
        "refresh_id": "aa111aaa-22aa-3333-2aaa-11111aaaaaaa",
        "expires_at": "2021-05-10T13:07:09+00:00",
        "_links": {
            "curies": [
                {
                    "href": "/docs/reference/rel/{rel}",
                    "name": "app",
                    "templated": true
                }
            ]
        }
    }
    """
    headers = headers if headers else DEFAULT_HEADERS

    data = {
        "name": "Authenticate",
        "email": email,
        "password": password,
        "device_id": device_id,
    }

    r = _post("/v2/commands", {}, session, data, headers)
    logged_in_data: LoggedInData = r.json()
    logged_in_data['device_id'] = device_id
    return logged_in_data


def refresh_token(
        logged_in_data: LoggedInData,
        session=None,
        headers: [Dict, None] = None,
) -> LoggedInData:
    headers = headers if headers else DEFAULT_HEADERS

    data = {
        "name": "RefreshToken",
        "refresh_id": logged_in_data['refresh_id'],
        "device_id": logged_in_data['device_id'],
    }

    r = _post("/v2/commands", {}, session, data, headers)
    logged_in_data = r.json()

    return logged_in_data


def audiobook_start_playback(logged_in_data, audiobook_id, session=None, headers=None):
    headers = headers if headers else DEFAULT_HEADERS

    data = {"name": "StartPlayback", "audiobook_id": audiobook_id}

    return _post("/v2/commands", logged_in_data, session, data, headers).json()


def get_audiobook_attachment_list(
    logged_in_data, audiobook_id, session=None, headers=None
):
    """
    "app:attachment-list": {
        "href": "/v2/audiobooks/{id}/attachments",
        "templated": true,
        "title": "Audiobook's attachment list"
    }
    """
    return _get(
        f"/v2/audiobooks/{audiobook_id}/attachments",
        logged_in_data,
        session,
        headers,
    ).json()


def get_audiobook_media(
    logged_in_data, catalog_id, audiobook_id, session=None, headers=None
):
    """
    "app:audiobook-media": {
        "href": "/v2/catalogs/{catalog}/audiobooks/{audiobook}/media",
        "templated": true,
        "title": "View audiobook's media"
    },"""
    return _get(
        f"/v2/catalogs/{catalog_id}/audiobooks/{audiobook_id}/media",
        logged_in_data,
        session,
        headers,
    ).json()


def get_audiobook_license_channels(
    logged_in_data, audiobook_id, session=None, headers=None
):
    """
    app:license-channels
    """
    return _get(
        "/v2/me/audiobook-license-channels/" + audiobook_id,
        logged_in_data,
        session,
        headers,
    ).json()


def get_audiobook(logged_in_data, audiobook_id, session=None, headers=None):
    """
    app:audiobook
    """
    return _get(
        "/v2/audiobooks/" + audiobook_id, logged_in_data, session, headers
    ).json()


def get_track_file(logged_in_data, track_file_url, session=None, headers=None):
    return _get(track_file_url, logged_in_data, session, headers)


def get_audiobook_track_list(logged_in_data, audiobook_id, session=None, headers=None):
    """
    "app:track-list": {
        "href": "/v2/audiobooks/{id}/tracks",
        "templated": true,
        "title": "Audiobook's tracks"
    },"""
    return _get(
        f"/v2/audiobooks/{audiobook_id}/tracks", logged_in_data, session, headers
    ).json()


def get_audiobook_toc(logged_in_data, audiobook_id, session=None, headers=None):
    """
    "app:toc": {
            "href": "/v2/audiobooks/{id}/table-of-contents",
            "templated": true,
            "title": "Audiobook's table of contents"
        },
    """
    return _get(
        f"/v2/audiobooks/{audiobook_id}/table-of-contents",
        logged_in_data,
        session,
        headers,
    ).json()


def get_products_in_catalog(logged_in_data, session=None, headers=None):
    """
    app:product-list
    """
    return _get("/v2/products", logged_in_data, session, headers).json()


def get_user_account_info(logged_in_data, session=None, headers=None):
    return _get("/v2/me", logged_in_data, session, headers).json()


def get_activation_method(logged_in_data, session=None, headers=None):
    return _get(
        "/v2/me/activation-methods", logged_in_data, session, headers
    ).json()


def get_player(logged_in_data, session=None, headers=None):
    return _get("/v2/me/player", logged_in_data, session, headers).json()


def get_recently_played(logged_in_data, session=None, headers=None):
    """
    "app:recently-played": {
            "href": "/v2/me/recently-played",
            "title": "View recently played"
        },

    :param logged_in_data:
    :param session:
    :param headers:
    :return:
    """
    return _get("/v2/me/recently-played", logged_in_data, session, headers).json()


def get_shelf_cycles(logged_in_data, session=None, headers=None):
    return _get("/v2/me/shelf/cycles", logged_in_data, session, headers).json()


def get_playback_progress(logged_in_data, session=None, headers=None):
    return _get(
        "/v2/me/playback-progress", logged_in_data, session, headers
    ).json()


def get_shelf(logged_in_data: LoggedInData, session=None, headers=None) -> Dict:
    """
    gets personal shelf content

    :param logged_in_data:
    :param session:
    :param headers:
    :return:
    """
    return _get("/v2/me/shelf", logged_in_data, session, headers).json()


def __get_shelf_item(product_id, credentials, session=None, headers=None):
    """
    OLD API

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


def __get_chapters(
    tracking_number, line_item_id, credentials, session=None, headers=None
):
    """
    OLD API

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


def __get_chapter_file(
    tracking_number,
    line_item_id,
    download_server_url,
    download_server_footer,
    file_name,
    credentials,
    stream=False,
    session=None,
    headers=None,
):
    """
    OLD API

    gets chapter file.

    :param tracking_number:
    :param line_item_id:
    :param download_server_url:
    :param download_server_footer:
    :param file_name:
    :param credentials:
    :param stream: Default: False. If True, returns stream (chunks)
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
        stream=stream,
    )

    return r


def __epoch_to_datetime(aud_dt):
    """
    OLD API
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


def _post(endpoint, logged_in_data, session=None, data=None, headers=None):
    d, h = _merge_into_data_and_headers(
        logged_in_data, data, headers if headers else DEFAULT_HEADERS
    )
    s = session if session else requests.session()
    #
    r = s.post(AUDIOTEKA_API_URL + endpoint, json=d, headers=h)
    try:
        logger.debug(json.dumps(r.json(), indent=4, sort_keys=True))
    except:
        logger.debug(f"No JSON type response. Status={r.status_code}")

    r.raise_for_status()
    return r


def _get(endpoint, logged_in_data, session=None, headers=None):
    d, h = _merge_into_data_and_headers(
        logged_in_data, None, headers if headers else DEFAULT_HEADERS
    )
    s = session if session else requests.session()
    #
    r = s.get(AUDIOTEKA_API_URL + endpoint, headers=h)
    try:
        logger.debug(json.dumps(r.json(), indent=4, sort_keys=True))
    except:
        logger.debug(f"No JSON type response. Status={r.status_code}")
    r.raise_for_status()
    return r


def _merge_into_data_and_headers(login_data, data, headers):
    if not login_data:
        return data, headers

    ret_data = dict()
    ret_headers = dict()
    ret_headers["Authorization"] = "Bearer " + login_data["token"]
    return _merge_dicts(data, ret_data), _merge_dicts(ret_headers, headers)


def _merge_dicts(*dict_args):
    result = {}
    for dictionary in dict_args:
        if dictionary:
            result.update(dictionary)
    return result


def _set_response_login_failed(r):
    r.status_code = 401
    r.reason = "Login failed"


def _set_response_item_not_found(r):
    r.status_code = 404
    r.reason = "Item not found"
