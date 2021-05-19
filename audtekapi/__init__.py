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


class AudiotekaAPI:
    def __init__(self):
        self._logged_in_data: LoggedInData = None
        self._session: requests.Session = requests.session()

    def get_categories(self):
        """
        "app:category-list":
            "href": "/v2/categories",
            "title": "Browse categories
        """
        return self._get("/v2/categories").json()

    def get_home_v2(self):
        """
        "app:screen:home": {
            "href": "/v2/me/screen",
            "title": "User's homescreen v2"
        },"""
        return self._get("/v2/me/screen").json()

    def login(self, email: str, password: str, device_id: str) -> bool:
        """
        Login (authenticate) user

        :param email:
        :param password:
        :param device_id:
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

        data = {
            "name": "Authenticate",
            "email": email,
            "password": password,
            "device_id": device_id,
        }

        r = self._post("/v2/commands", data)
        self._logged_in_data: LoggedInData = r.json()
        self._logged_in_data['device_id'] = device_id
        return True

    def refresh_token(self) -> bool:
        data = {
            "name": "RefreshToken",
            "refresh_id": self._logged_in_data['refresh_id'],
            "device_id": self._logged_in_data['device_id'],
        }

        r = self._post("/v2/commands", {}, data)
        logged_in_data = r.json()

        return logged_in_data

    def audiobook_start_playback(self, audiobook_id):
        data = {"name": "StartPlayback", "audiobook_id": audiobook_id}

        return self._post("/v2/commands", data).json()

    def get_audiobook_attachment_list(self, audiobook_id):
        """
        "app:attachment-list": {
            "href": "/v2/audiobooks/{id}/attachments",
            "templated": true,
            "title": "Audiobook's attachment list"
        }
        """
        return self._get(
            f"/v2/audiobooks/{audiobook_id}/attachments").json()

    def get_audiobook_media(self, catalog_id, audiobook_id):
        """
        "app:audiobook-media": {
            "href": "/v2/catalogs/{catalog}/audiobooks/{audiobook}/media",
            "templated": true,
            "title": "View audiobook's media"
        },"""
        return self._get(
            f"/v2/catalogs/{catalog_id}/audiobooks/{audiobook_id}/media").json()

    def get_audiobook_license_channels(self, audiobook_id):
        """
        app:license-channels
        """
        return self._get(
            f"/v2/me/audiobook-license-channels/{audiobook_id}").json()

    def get_audiobook(self, audiobook_id):
        """
        app:audiobook
        """
        return self._get(
            f"/v2/audiobooks/{audiobook_id}").json()

    def get_track_file(self, track_file_url):
        return self._get(track_file_url)

    def get_audiobook_track_list(self, audiobook_id):
        """
        "app:track-list": {
            "href": "/v2/audiobooks/{id}/tracks",
            "templated": true,
            "title": "Audiobook's tracks"
        },"""
        return self._get(
            f"/v2/audiobooks/{audiobook_id}/tracks").json()

    def get_audiobook_toc(self, audiobook_id):
        """
        "app:toc": {
                "href": "/v2/audiobooks/{id}/table-of-contents",
                "templated": true,
                "title": "Audiobook's table of contents"
            },
        """
        return self._get(
            f"/v2/audiobooks/{audiobook_id}/table-of-contents").json()

    def get_products_in_catalog(self):
        """
        app:product-list
        """
        return self._get("/v2/products").json()

    def get_user_account_info(self):
        return self._get("/v2/me").json()

    def get_activation_method(self):
        return self._get("/v2/me/activation-methods").json()

    def get_player(self):
        return self._get("/v2/me/player").json()

    def get_recently_played(self):
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
        return self._get("/v2/me/recently-played").json()

    def get_shelf_cycles(self):
        return self._get("/v2/me/shelf/cycles").json()

    def get_playback_progress(self):
        return self._get("/v2/me/playback-progress").json()

    def get_shelf(self) -> Dict:
        """
        gets personal shelf content

        :param logged_in_data:
        :param session:
        :param headers:
        :return:
        """
        return self._get("/v2/me/shelf").json()

    def _post(self, endpoint: str, data: dict = None):
        r = self._session.post(AUDIOTEKA_API_URL + endpoint, json=data, headers=self._make_headers())
        try:
            logger.debug(json.dumps(r.json(), indent=4, sort_keys=True))
        except:
            logger.debug(f"No JSON type response. Status={r.status_code}")
        r.raise_for_status()
        return r

    def _get(self, endpoint: str):
        r = self._session.get(AUDIOTEKA_API_URL + endpoint, headers=self._make_headers())
        try:
            logger.debug(json.dumps(r.json(), indent=4, sort_keys=True))
        except:
            logger.debug(f"No JSON type response. Status={r.status_code}")
        r.raise_for_status()
        return r

    def _make_headers(self) -> dict:
        if not self._logged_in_data:
            return DEFAULT_HEADERS

        d1 = DEFAULT_HEADERS.copy()
        d1.update({"Authorization": f"Bearer {self._logged_in_data['token']}"})
        return d1
