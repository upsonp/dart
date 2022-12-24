from django.test import TestCase, tag
from . import CoreFactoryFloor as core_factory

from .. import validations
from core.validation import ValidateEvents
from .. import models


@tag('validation', 'validation_ctd')
class TestCTDEventValidation(TestCase):
    ctd_event_valid = None

    def setUp(self):
        self.ctd_event_valid = core_factory.CTDEventFactory(sample_id=495000, end_sample_id=495010, actions=[
            models.ActionType.deployed,
            models.ActionType.bottom,
            models.ActionType.recovered
        ])

    def test_ctd_event_sample_id_exists_invalid(self):
        ctd_event_invalid = core_factory.CTDEventFactory(sample_id=None, end_sample_id=495000, actions=[
            models.ActionType.deployed,
            models.ActionType.bottom,
            models.ActionType.recovered
        ])

        errors = ValidateEvents.validate_ctd_event(ctd_event_invalid)
        self.assertIsNotNone(errors)
        self.assertIs(errors[0][0], models.ErrorType.missing_id)

    def test_ctd_event_end_sample_id_exists_invalid(self):
        ctd_event_invalid = core_factory.CTDEventFactory(sample_id=49500, end_sample_id=None, actions=[
            models.ActionType.deployed,
            models.ActionType.bottom,
            models.ActionType.recovered
        ])

        errors = ValidateEvents.validate_ctd_event(ctd_event_invalid)
        self.assertIsNotNone(errors)
        self.assertEquals(errors[0][0], models.ErrorType.missing_id)

    def test_ctd_event_id_range_invalid(self):
        """ invalid if sample_id is greater than end_sample_id """
        ctd_event_invalid = core_factory.CTDEventFactory(sample_id=495010, end_sample_id=495000, actions=[
            models.ActionType.deployed,
            models.ActionType.bottom,
            models.ActionType.recovered
        ])

        errors = ValidateEvents.validate_ctd_event(ctd_event_invalid)
        self.assertIsNotNone(errors)
        self.assertEquals(errors[0][0], models.ErrorType.bad_id)

    def test_ctd_event_id_range_ids_equal_invalid(self):
        """ should also be invalid if sample_id is equal to the end_sample_id """
        ctd_event_invalid = core_factory.CTDEventFactory(sample_id=495000, end_sample_id=495000, actions=[
            models.ActionType.deployed,
            models.ActionType.bottom,
            models.ActionType.recovered
        ])

        errors = ValidateEvents.validate_ctd_event(ctd_event_invalid)
        self.assertIsNotNone(errors)
        self.assertEquals(errors[0][0], models.ErrorType.bad_id)

    def test_ctd_event_id_range_valid(self):
        """ valid if sample_id is less than end_sample_id """
        self.assertListEqual(ValidateEvents.validate_ctd_event(self.ctd_event_valid), [])

    def test_event_validation_factory(self):
        errors = []
        ctd_sample_ids_equal_invalid = core_factory.CTDEventFactory(sample_id=495000, end_sample_id=495000, actions=[
            models.ActionType.deployed,
            models.ActionType.bottom,
            models.ActionType.recovered
        ])

        ctd_missing_end_sample_id_invalid = core_factory.CTDEventFactory(sample_id=49500, end_sample_id=None, actions=[
            models.ActionType.deployed,
            models.ActionType.bottom,
            models.ActionType.recovered
        ])

        ctd_missing_sample_id_invalid = core_factory.CTDEventFactory(sample_id=49500, end_sample_id=None, actions=[
            models.ActionType.deployed,
            models.ActionType.bottom,
            models.ActionType.recovered
        ])

        errors += ValidateEvents.validate_ctd_event(ctd_sample_ids_equal_invalid)
        errors += ValidateEvents.validate_ctd_event(ctd_missing_end_sample_id_invalid)
        errors += ValidateEvents.validate_ctd_event(ctd_missing_sample_id_invalid)
        errors += ValidateEvents.validate_ctd_event(self.ctd_event_valid)

        self.assertEquals(len(errors), 3)


@tag('validation', 'validation_net')
class TestNetEventValidation(TestCase):

    valid_sample_id = 495000
    valid_end_sample_id = 495010
    valid_ctd_event = None
    valid_202_net_event = None

    def setUp(self):
        self.valid_ctd_event = core_factory.CTDEventFactory(sample_id=self.valid_sample_id,
                                                            end_sample_id=self.valid_end_sample_id)

        self.valid_202_net_event = core_factory.RingnetEventFactory(sample_id=self.valid_sample_id)
        core_factory.RingnetInstrumentSensorFactory(event=self.valid_202_net_event, name="202um")

        self.valid_76_net_event = core_factory.RingnetEventFactory(sample_id=self.valid_end_sample_id)
        core_factory.RingnetInstrumentSensorFactory(event=self.valid_76_net_event, name="76um")

    def test_validate_net_event_missing_sample_and_attachment_invalid(self):
        # no sample_id, no 202 or 76 Attachment, No CTD event
        net_event = core_factory.RingnetEventFactory(sample_id=None)

        errors = ValidateEvents.validate_net_event(net_event=net_event)

        self.assertIsNotNone(errors)
        self.assertEquals(errors[0][0], models.ErrorType.missing_id)
        self.assertEquals(errors[1][0], models.ErrorType.missing_information)
        # without a valid ctd and/or net attachment

    def test_validate_net_event_202_bad_id_invalid(self):
        # 202 no ctd event
        net_event = core_factory.RingnetEventFactory(sample_id=800_000)
        core_factory.RingnetInstrumentSensorFactory(event=net_event, name="202um")

        errors = ValidateEvents.validate_net_event(net_event=net_event)
        self.assertIsNotNone(errors)
        self.assertEquals(errors[0][0], models.ErrorType.bad_id)

    def test_validate_net_event_76_bad_id_invalid(self):
        # 76 no ctd event
        net_event = core_factory.RingnetEventFactory(sample_id=800_000)
        core_factory.RingnetInstrumentSensorFactory(event=net_event, name="76um")

        errors = ValidateEvents.validate_net_event(net_event=net_event)
        self.assertIsNotNone(errors)
        self.assertEquals(errors[0][0], models.ErrorType.bad_id)

    def test_validate_net_event_202_valid(self):
        errors = ValidateEvents.validate_net_event(net_event=self.valid_202_net_event)
        self.assertListEqual(errors, [])

    def test_validate_net_event_76_valid(self):
        errors = ValidateEvents.validate_net_event(net_event=self.valid_76_net_event)
        self.assertListEqual(errors, [])
