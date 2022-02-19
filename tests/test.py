import unittest
import logging
from datetime import datetime

import audtekapi as api


class AudtekAPI(unittest.TestCase):
    def setUp(self):
        logging.basicConfig(level=logging.DEBUG)
        pass

    def test_password_hashing(self):
        self.assertEqual(
            api._get_hashed_password('myPasswordAtAudioteka', '3660123456'),
            'DA290D407F60AB87DD44A58A5DD02F7B7AF8D3B46547CF687D674380D18180DB3EA432BE')

    def test_epoch_to_datetime(self):
        self.assertEqual(
            api.epoch_to_datetime('/Date(1545693401480+0100)/'),
            datetime(year=2018, month=12, day=24, hour=23, minute=16, second=41, microsecond=480000))

