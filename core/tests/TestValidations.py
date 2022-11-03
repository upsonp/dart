from django.test import TestCase
from . import CoreFactoryFloor as eff

from .. import validations


class ValidationTest(TestCase):

    def setUp(self):
        pass

    def test_validation_start_lt_end_id(self):
        # this should cause an issue because the sample ID is less than the end sample id.
        ctd_event = eff.CTDEventFactory(sample_id=495100, end_sample_id=495000)
        log_file = ctd_event.actions.all()[0].file
        errors = validations.validate_events(log_file)

        self.assertGreater(len(errors), 0)

    def test_validation_sample_id_exists(self):
        # this should cause an issue because the sample ID is missing.
        ctd_event = eff.CTDEventFactory(sample_id=None, end_sample_id=495000)
        log_file = ctd_event.actions.all()[0].file
        errors = validations.validate_events(log_file)

        self.assertGreater(len(errors), 0)

    def test_validation_end_sample_id_exists(self):
        # this should cause an issue because the end sample ID is missing.
        ctd_event = eff.CTDEventFactory(sample_id=495000, end_sample_id=None)
        log_file = ctd_event.actions.all()[0].file
        errors = validations.validate_events(log_file)

        self.assertGreater(len(errors), 0)

    def test_validation_start_and_end_sample_id_exists(self):
        # this should cause an issue because both the sample ID and end sample id are missing.
        ctd_event = eff.CTDEventFactory(sample_id=None, end_sample_id=None)
        log_file = ctd_event.actions.all()[0].file
        errors = validations.validate_events(log_file)

        self.assertEquals(len(errors), 2)
