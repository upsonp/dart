from django.test import TestCase, tag

from . import CoreFactoryFloor as cff
from .. import utils


@tag('utils')
class TestElogProcessing(TestCase):

    log_file = None

    def setUp(self):
        super().setUp()

        self.log_file = cff.LogFileFactory(processed=False)
        self.mid_map = {'file': self.log_file, 'buffer':{}}
