from django.test import TestCase, tag
from . import CoreFactoryFloor as core_factory

from .. import validations
from .. import models


@tag('validation')
class ValidationTest(TestCase):

    def setUp(self):
        pass

    def test_validation_start_lt_end_id(self):
        # this should cause an issue because the sample ID is less than the end sample id.
        ctd_event = core_factory.CTDEventFactory(sample_id=495100, end_sample_id=495000, actions=[
            models.ActionType.deployed,
            models.ActionType.bottom,
            models.ActionType.recovered
        ])

        log_file = ctd_event.actions.get(action_type=models.ActionType.deployed).file
        errors = validations.validate_events(log_file)

        self.assertGreater(len(errors), 0)

    def test_validation_sample_id_exists(self):
        # this should cause an issue because the sample ID is missing.
        ctd_event = core_factory.CTDEventFactory(sample_id=None, end_sample_id=495000, actions=[
            models.ActionType.deployed,
            models.ActionType.bottom,
            models.ActionType.recovered
        ])
        log_file = ctd_event.actions.get(action_type=models.ActionType.deployed).file
        errors = validations.validate_events(log_file)

        self.assertGreater(len(errors), 0)

    def test_validation_end_sample_id_exists(self):
        # this should cause an issue because the end sample ID is missing.
        ctd_event = core_factory.CTDEventFactory(sample_id=495000, end_sample_id=None, actions=[
            models.ActionType.deployed,
            models.ActionType.bottom,
            models.ActionType.recovered
        ])
        log_file = ctd_event.actions.get(action_type=models.ActionType.deployed).file
        errors = validations.validate_events(log_file)

        self.assertGreater(len(errors), 0)

    def test_validation_start_and_end_sample_id_exists(self):
        # this should cause an issue because both the sample ID and end sample id are missing.
        ctd_event = core_factory.CTDEventFactory(sample_id=None, end_sample_id=None, actions=[
            models.ActionType.deployed,
            models.ActionType.bottom,
            models.ActionType.recovered
        ])
        log_file = ctd_event.actions.get(action_type=models.ActionType.deployed).file
        errors = validations.validate_events(log_file)

        self.assertEquals(len(errors), 2)

    def test_validation_ring_net_202(self):
        # 202 or 76 should be present as an attachment to a ringnet
        # 202 ringnets correspond to CTD Bottom sample id

        expected_sample_id = 495000
        expected_end_id = 495024
        ctd_event = core_factory.CTDEventFactory(sample_id=expected_sample_id, end_sample_id=expected_end_id)

        ringnet_event_good = core_factory.RingnetEventFactory(sample_id=expected_sample_id,
                                                              actions=[
                                                         models.ActionType.deployed,
                                                         models.ActionType.bottom,
                                                         models.ActionType.recovered
                                                     ])

        core_factory.RingnetInstrumentSensorFactory(event=ringnet_event_good, name="202um")

        log_file = ringnet_event_good.actions.get(action_type=models.ActionType.deployed).file

        errors = validations.validate_events(log_file)
        self.assertEquals(len(errors), 0)

        ringnet_event_bad = core_factory.RingnetEventFactory(sample_id=295000, actions=[
                                                         models.ActionType.deployed,
                                                         models.ActionType.bottom,
                                                         models.ActionType.recovered
                                                     ])
        log_file = ringnet_event_bad.actions.get(action_type=models.ActionType.deployed).file

        errors = validations.validate_events(log_file)
        self.assertEquals(len(errors), 1)
        self.assertEquals(errors[0].message, f"Event {ringnet_event_bad.event_id} in file {log_file.file.name} does not "
                                             f"specify the type of net used as an attachment")

        core_factory.RingnetInstrumentSensorFactory(event=ringnet_event_bad, name="202um")

        errors = validations.validate_events(log_file)
        self.assertEquals(errors[0].message, f"Event {ringnet_event_bad.event_id} in file {log_file.file.name} - "
                                             f"202um ringnets must have a sample id corresponding to a CTD bottom id")

    def test_validation_ring_net_76(self):
        # 202 or 76 should be present as an attachment to a ringnet
        # 202 ringnets correspond to CTD Bottom sample id

        expected_sample_id = 495000
        expected_end_id = 495024
        ctd_event = core_factory.CTDEventFactory(sample_id=expected_sample_id, end_sample_id=expected_end_id)

        ringnet_event_good = core_factory.RingnetEventFactory(sample_id=expected_end_id, actions=[
            models.ActionType.deployed,
            models.ActionType.bottom,
            models.ActionType.recovered
        ])
        core_factory.RingnetInstrumentSensorFactory(event=ringnet_event_good, name="76um")

        log_file = ringnet_event_good.actions.get(action_type=models.ActionType.deployed).file

        errors = validations.validate_events(log_file)
        self.assertEquals(len(errors), 0)

        ringnet_event_bad = core_factory.RingnetEventFactory(sample_id=295000, actions=[
            models.ActionType.deployed,
            models.ActionType.bottom,
            models.ActionType.recovered
        ])
        log_file = ringnet_event_bad.actions.get(action_type=models.ActionType.deployed).file

        errors = validations.validate_events(log_file)
        self.assertEquals(len(errors), 1)
        self.assertEquals(errors[0].message, f"Event {ringnet_event_bad.event_id} in file {log_file.file.name} does not"
                                             f" specify the type of net used as an attachment")

        core_factory.RingnetInstrumentSensorFactory(event=ringnet_event_bad, name="76um")

        errors = validations.validate_events(log_file)
        self.assertEquals(errors[0].message, f"Event {ringnet_event_bad.event_id} in file {log_file.file.name} - "
                                             f"76um ringnets must have a sample id corresponding to a CTD surface id")
