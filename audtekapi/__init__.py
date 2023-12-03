import hashlib
import binascii
import json
import pickle
import re
import requests
from typing import Dict
from requests.auth import HTTPDigestAuth
import logging
from datetime import datetime
from pathlib import Path

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

FILE_SESSION = "audteka_session.bin"
FILE_LOGGED_IN_DATA = "audteka_logged_in_data.bin"


class AudiotekaAPI:
    def __init__(self, email: str, password: str, device_id: str, save_session: bool = False):
        self._email: str = email
        self._password: str = password
        self._device_id: str = device_id
        self._logged_in_data: LoggedInData = None
        self._save_session: bool = save_session
        self._session: requests.Session = requests.session()
        try:
            self._logged_in_data = pickle.loads(Path(FILE_LOGGED_IN_DATA).read_bytes())
            self._session = pickle.loads(Path(FILE_SESSION).read_bytes())
        except:
            ...

    def _store_session(self):
        if not self._save_session:
            return
        try:
            Path(FILE_LOGGED_IN_DATA).write_bytes(pickle.dumps(self._logged_in_data))
            Path(FILE_SESSION).write_bytes(pickle.dumps(self._session))
        except:
            ...


    @property
    def session(self) -> requests.Session:
        return self._session

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

    def login(self) -> bool:
        """
        Login (authenticate) user

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

        if self._logged_in_data:
            return True

        data = {
            "name": "Authenticate",
            "email": self._email,
            "password": self._password,
            "device_id": self._device_id,
        }

        r = self._post("/v2/commands", data)
        self._logged_in_data = r.json()
        self._logged_in_data['device_id'] = self._device_id
        self._store_session()
        return True

    def refresh_token(self) -> bool:
        data = {
            "name": "RefreshToken",
            "refresh_id": self._logged_in_data['refresh_id'],
            "device_id": self._logged_in_data['device_id'],
        }

        r = self._post("/v2/commands", data)
        logged_in_data = r.json()
        self._store_session()
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

    def get_track(self, track_file_url):
        return self._get(track_file_url).json()

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

    def get_products_in_catalog(self, page: int = 1, limit: int = 10, cycle: str = '', catalog: str = None):
        """

        get products in catalog

        :param page:
        :param limit:
        :param cycle:
        :param catalog: if use catalog cycle should be also provided
        :return:
        """
        params = {"page": page, "limit": limit}
        if catalog:
            params["catalog"] = catalog

        return self._get(f"/v2/products/{cycle}", params).json()

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

    def get_shelf(self, page: int = 1, limit: int = 10, sort: str = None, order: str = None) -> Dict:
        """
        gets personal shelf content

        :param page:
        :param limit:
        :param sort
        :param order
        :return:
        """
        params = {"page": page, "limit": limit}
        if sort:
            params["sort"] = sort
        if order:
            params["order"] = order
        return self._get("/v2/me/shelf", params).json()

    def get_favourites(self, page: int = 1, limit: int = 100, sort: str = None, order: str = None) -> Dict:
        """
        gets personal favourites content

        :param page:
        :param limit:
        :param sort
        :param order
        :return:
        """
        params = {"page": page, "limit": limit}
        return self._get("/v2/me/favourites", params).json()

    def get_config(self):
        return self._get("/v2/apps/config").json()

    def get_algolia(self):
        return self._get("/v2/me/algolia").json()

    def _post(self, endpoint: str, data: dict = None):
        r = None
        try:
            r = self._session.post(AUDIOTEKA_API_URL + endpoint, json=data, headers=self._make_headers())
            try:
                logger.debug(json.dumps(r.json(), indent=4, sort_keys=True))
            except:
                logger.debug(f"No JSON type response. Status={r.status_code}")
            r.raise_for_status()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code != 401:
                raise e
            if self._logged_in_data:
                self.refresh_token()
            else:
                self.login()
            return self._post(endpoint, data)
        return r

    def _get(self, endpoint: str, params: dict = None):
        r = None
        try:
            r = self._session.get(AUDIOTEKA_API_URL + endpoint, params=params, headers=self._make_headers())
            try:
                logger.debug(json.dumps(r.json(), indent=4, sort_keys=True))
            except:
                logger.debug(f"No JSON type response. Status={r.status_code}")
            r.raise_for_status()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code != 401:
                raise e
            if self._logged_in_data:
                self.refresh_token()
            else:
                self.login()
            return self._get(endpoint, params)
        return r

    def _make_headers(self) -> dict:
        if not self._logged_in_data:
            return DEFAULT_HEADERS

        d1 = DEFAULT_HEADERS.copy()
        d1.update({"Authorization": f"Bearer {self._logged_in_data['token']}"})
        return d1
