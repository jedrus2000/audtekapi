****************************
AudtekAPI
****************************

.. image:: https://img.shields.io/pypi/v/audtekapi.svg?style=flat
    :target: https://pypi.python.org/pypi/audtekapi/
    :alt: Latest PyPI version



Unofficial API helper for *Audioteka* - audiobooks service: `<https://audioteka.com/>`_

This is set of functions to get contents of your personal bookshelf at *Audioteka*, including book's chapters downloading.

Main reason for creating it, is my upcoming plugin for `Mopidy
<http://apt.mopidy.com/>`_.

Currently following functions are implemented:
    - get_categories - getting Categories (logging not needed)
    - login - logging into service
    - get_shelf - getting shelf content (logging required)
    - get_shelf_item - getting single book detail (logging required)
    - get_chapters - getting book's chapters list (logging required)
    - get_chapter_file - getting one chapter file data (logging required)
    - epoch_to_datetime - converts date time string seen in Audioteka's responses into Python's DateTime


Installation
============
Python 2.7 or higher is required.

Install by running::

    pip install audtekapi



Usage
=============
Examples.

Logging in::

    bash> python
    Python 2.7.15
    >>>> import audtekapi
    >>> cred = audtekapi.login('some@mail.com', 'myPasswordAtAudioteka')
    >>> cred
    {u'AuthenticationToken': u'8122aaaa-aebc-22a1-2233-1111a11ceecb',
    u'Status': u'LoginStatusOk',
    u'HashedPassword': 'DB111ABC01A10203A10C010B4736E83746D838348AD7B8CAA11BBCC7854A010192A93841',
    u'Salt': u'3660123456', u'userLogin': 'a.barganski@gmail.com'}

Getting shelf content::

    >>> shelf = audtekapi.get_shelf(cred)
    >>> shelf
    {
      u'Date':u'20190105',
      u'DownloadDateInMilliseconds':1546710438687,
      u'ServerAddress': u'http://mediaserver5.audioteka.pl/GetFileRouter.ashx'
      u'ShelfItemsCount':1,
      u'Footer':u'No=0&daa=true&httpStatus=true&regen=true',
      u'Books':[
      {
         u'IsFreeChapterEnabled':False,
         u'BigPictureLink': u'https://static.audioteka.com/pl/images/products/calek-perechodnik/spowiedz-duze.jpg',
         u'IsSample':False,
         u'WMStatus':u'Done',
         u'Author':u'Calek Perechodnik',
         u'LineItemCategory':u'',
         u'IsForKids':False,
         u'IsAudiobookPlus':False,
         u'Reader':u'Maciej Wi\u0119ckowski',
         u'Type':u'Audiobook - pe\u0142ny',
         u'ListPrice':32.9,
         u'AverageRating':10,
         u'Status':u'Paid',
         u'LastWatermarkingDate':u'/Date(1546557722603+0100)/',
         u'SmallPictureLink': u'https://static.audioteka.com/pl/images/products/calek-perechodnik/spowiedz-male.jpg',
         u'Title':u'Spowied\u017a',
         u'CanDownloadZip':True,
         u'SampleLink': u'https://static.audioteka.com/pl/content/samples/calek-perechodnik/spowiedz.mp3',
         u'UserRating':0,
         u'Cycle':u'',
         u'FilesDivisionMode':u'Normal',
         u'Publisher':u'Heraclon International',
         u'ProductDateAdd':u'/Date(1519206527537+0100)/',
         u'OrderTrackingNumber':u'1234567890',
         u'Length':861,
         u'LineItemId':u'00000eea-111a-2222-aa22-a1333aaa111f',
         u'BlackBerrySku':u'001199Audioteka',
         u'CategoryId':u'biografie',
         u'ProductId':u'spowiedz',
         u'MediumPicture': u'https://static.audioteka.com/pl/images/products/calek-perechodnik/spowiedz-srednie.jpg',
         u'CategoryName':u'Biografie',
         u'IPodDivisionMode':u'OneFile',
         u'RootCategoryId':u'',
         u'CreatedDate':u'/Date(1546553332470+0100)/',
         u'WatermarkingTarget':u'Normal',
         u'EbookLink':u''
      },
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

License
=================

Apache License Version 2.0
