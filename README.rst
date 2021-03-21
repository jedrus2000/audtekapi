****************************
AudtekAPI
****************************

.. image:: https://img.shields.io/pypi/v/audtekapi.svg?style=flat
    :target: https://pypi.python.org/pypi/audtekapi/
    :alt: Latest PyPI version



Unofficial API helper for *Audioteka* - audiobooks service: `<https://audioteka.com/>`_

This is set of functions to get contents of your personal bookshelf at *Audioteka*, including book's chapters downloading.

Main reason for creating it, is to use it in my plugin for `Mopidy
<http://apt.mopidy.com/>`_.

Currently following functions are implemented:
    - get_categories - getting Categories (sign in not needed)
    - login - login into service
    - get_shelf - getting shelf content (sign in required)
    - get_shelf_item - getting single book detail (sign in required)
    - get_chapters - getting book's chapters list (sign in required)
    - get_chapter_file - getting one chapter file data (sign in required)
    - epoch_to_datetime - converts date time string seen in Audioteka's responses into Python's DateTime


Installation
============
Python 3.7 or higher is required.

Install by running::

    pip install audtekapi



Usage
=============
Examples.

generate device id::

    bash> python
    Python 3.9.1
    >>> import uuid
    >>> str(uuid.uuid4())
    'mydevice-id00-aaaa-bbbb-ccddeeddffaa'

sign in::

    >>> import audtekapi
    >>> logged_in_data = audtekapi.login('some@mail.com', 'myPasswordAtAudioteka', 'mydevice-id00-aaaa-bbbb-ccddeeddffaa')
    >>> logged_in_data
    {'token': 'ey-Looong-token-content', 'refresh_id': 'aabb22cc-1122-55aa-aa22-1a222222aa11', 'expires_at': '2021-06-20T01:11:22+00:00',
    '_links': {'curies': [{'href': '/docs/reference/rel/{rel}', 'name': 'app', 'templated': True}]},
    'device_id': 'mydevice-id00-aaaa-bbbb-ccddeeddffaa'}

Getting shelf content::

    >>> shelf = audtekapi.get_shelf(logged_in_data)
    >>> shelf
    {
        "_embedded": {
            "app:product": [
                {
                    "_links": {
                        "app:audiobook": {
                            "href": "/v2/audiobooks/aaaaaaaa-bbbb-2222-1111-222222222222?catalog=ebebebeb-eeee-eeee-eeee-ffffffffffff"
                        },
                        "self": {
                            "href": "/v2/products/aaaaaaaa-bbbb-2222-1111-222222222222?catalog=ebebebeb-eeee-eeee-eeee-ffffffffffff"
                        }
                    },
                    "deeplink": "https://lstn.link/audiobook/aaaaaaaa-bbbb-2222-1111-222222222222",
                    "description": "Walter Isaacson",
                    "id": "aaaaaaaa-bbbb-2222-1111-222222222222",
                    "image_url": "https://assets.audioteka.com/pl/images/products/walter-isaacson/leonardo-da-vinci-original.png",
                    "is_free": false,
                    "name": "Leonardo da Vinci",
                    "rating": 4.54,
                    "reference_id": "pl_leonardo-da-vinci"
                }
            ]
        },
        "_links": {
            "curies": [
                {
                    "href": "/docs/reference/rel/{rel}",
                    "name": "app",
                    "templated": true
                }
            ],
            "first": {
                "href": "/v2/me/shelf?page=1&limit=10"
            },
            "last": {
                "href": "/v2/me/shelf?page=7&limit=10"
            },
            "next": {
                "href": "/v2/me/shelf?page=2&limit=10"
            },
            "self": {
                "href": "/v2/me/shelf?page=1&limit=10"
            }
        },
        "limit": 10,
        "page": 1,
        "pages": 7,
        "total": 69
    }

Getting book's chapters information::

    >>> chapters = audtekapi.get_chapters(shelf['Books'][0]['OrderTrackingNumber'], shelf['Books'][0]['LineItemId'], cred)
    >>> chapters
    [
        {u'Track': 1, u'Length': 335673, u'Size': 4920010, u'Link': u'001_Spowiedz.mp3', u'ChapterTitle': u'001_Spowiedz'},
        {u'Track': 2, u'Length': 1047450, u'Size': 14884993, u'Link': u'002_Spowiedz.mp3', u'ChapterTitle': u'002_Spowiedz'}
    ]

Downloading one chapter and saving it into file::

    >>> r = audtekapi.get_chapter_file(shelf['Books'][0]['OrderTrackingNumber'], shelf['Books'][0]['LineItemId'], shelf['ServerAddress'], shelf['Footer'], chapters[1]['Link'], cred)
    >>> open(chapters[1]['Link'], 'wb').write(r.content)

...or downloading as stream (chunks) and saving it into file::

    >>> r = audtekapi.get_chapter_file(shelf['Books'][0]['OrderTrackingNumber'], shelf['Books'][0]['LineItemId'], shelf['ServerAddress'], shelf['Footer'], chapters[1]['Link'], cred, True)
    >>> with open(chapters[1]['Link'], 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)


License
=================

Apache License Version 2.0
