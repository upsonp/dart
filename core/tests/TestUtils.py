from django.test import TestCase, tag

from . import CoreFactoryFloor as cff

from core import utils
from core.parsers import elog
from core import models

import os

@tag('utils')
class TestElogProcessing(TestCase):

    expected_stations = ['st_01', 'st_02']
    expected_instruments = ['CTD', 'RingNet']
    expected_events = [
        {
            'event_id': 1, 'instrument': expected_instruments[0], 'station': expected_stations[0],
            'attached': ['pH', 'SBE35'], 'actions': ['Deployed', 'Bottom', 'Recovered'],
            'sample_id': 495000, 'end_sample_id': 495010
        },
        {
            'event_id': 2, 'instrument': expected_instruments[1], 'station': expected_stations[0],
            'attached': ['80um'], 'actions': ['Deployed', 'Bottom', 'Recovered'],
            'sample_id': 495000, 'end_sample_id': None
        },
        {
            'event_id': 3, 'instrument': expected_instruments[0], 'station': expected_stations[1],
            'attached': ['SBE35'], 'actions': ['Deployed', 'Bottom', 'Recovered'],
            'sample_id': 495011, 'end_sample_id': 495020
        },
    ]

    # used when testing that overriding objects is working
    alt_events = [
        {
            'event_id': 1, 'instrument': expected_instruments[1], 'station': expected_stations[1],
            'attached': ['202um'], 'actions': ['Deployed', 'Bottom', 'Recovered'],
            'sample_id': 495000, 'end_sample_id': None
        },
        {
            'event_id': 2, 'instrument': expected_instruments[1], 'station': expected_stations[1],
            'attached': ['pH', 'SBE35'], 'actions': ['Deployed', 'Bottom', 'Recovered'],
            'sample_id': 495000, 'end_sample_id': 495010
        },
        {
            'event_id': 3, 'instrument': expected_instruments[0], 'station': expected_stations[0],
            'attached': ['76um'], 'actions': ['Deployed', 'Bottom', 'Recovered'],
            'sample_id': 495011, 'end_sample_id': None
        },
    ]

    mid_map = None
    log_file = None
    mission = None
    elog_config = None

    def setUp(self):
        super().setUp()

        # when logfiles are created by the LogFileFactory a blank file is created in
        # the root directory that has to be removed in the tearDown method
        self.log_file = cff.LogFileFactory(processed=False)
        self.mission = self.log_file.directory.mission

        # use the MidObjectFactory to create a dictionary mimicking what a parsed Mid object would look like
        # had the object come from an Elog file. This is specific to the Atlantic Region version of an elog file
        mids = []
        for e in self.expected_events:
            mids += cff.MidObjectFactory.get_ctd_net_event(
                event=e['event_id'], instrument=e['instrument'], station=e['station'],
                sample_id=e['sample_id'], end_sample_id=e['end_sample_id'],
                attached=' | '.join(e['attached'])
            )

        # this is what the mid mapping from the utils.read_elog function produces.
        self.mid_map = {'file': self.log_file, 'buffer': {i+1: mids[i] for i in range(0, len(mids))}}
        self.elog_config = models.ElogConfig.get_default_elog_config(self.mission)

    def tearDown(self):
        os.remove(self.log_file.file.name)

    def create_events_entries(self, events_dict):
        models.Event.objects.bulk_create([
            models.Event(
                mission=self.mission, event_id=e['event_id'],
                sample_id=e['sample_id'], end_sample_id=e['end_sample_id'],
                instrument=models.Instrument.objects.get(name=e['instrument']),
                station=models.Station.objects.get(name=e['station'])
            ) for e in events_dict
        ])

    # function to run when checking that database objects match the expected events
    def verify_events(self, events):
        # run through the expected events array and make sure all the elements are in place
        # and have overridden the original objects
        for e in events:
            if not models.Event.objects.filter(mission=self.mission, event_id=e['event_id']).exists():
                self.fail(f"Expected Event {e} was not added to the database")

            event = models.Event.objects.get(mission=self.mission, event_id=e['event_id'])
            inst = e['instrument']
            self.assertEquals(event.instrument, models.Instrument.objects.get(
                name=inst, instrument_type=models.InstrumentType[inst.lower()]))

            self.assertEquals(event.station, models.Station.objects.get(name=e['station']))
            self.assertEquals(event.sample_id, e['sample_id'])
            self.assertEquals(event.end_sample_id, e['end_sample_id'])

    # Test that the process_stations_instruments function can acquire stations from the mid_map
    # and create the expected stations and instruments
    def test_process_station_instrument(self):
        log_file = self.mid_map['file']
        elog.process_stations_instruments(log_file, self.mid_map, self.mid_map['buffer'].keys(), self.elog_config)

        for s in self.expected_stations:
            if len(models.Station.objects.filter(name=s)) <= 0:
                self.fail(f"Expected Station {s} was not added to the database")

        for i in self.expected_instruments:
            if len(models.Instrument.objects.filter(name=i)) <= 0:
                self.fail(f"Expected Instrument {i} was not added to the database")

    # Test that the process_events function can acquire event specific elements from the mid_map
    # and create the expected events with stations and instrumnets attached
    def test_process_events(self):

        # Objects that are expected to already exist for this process to complete
        models.Station.objects.bulk_create([models.Station(name=s) for s in self.expected_stations])
        models.Instrument.objects.bulk_create([
            models.Instrument(name=i, instrument_type=models.InstrumentType[i.lower()])
            for i in self.expected_instruments])
        # ====================================================================== #

        elog.process_events(self.log_file, self.mid_map, self.mid_map['buffer'].keys(), self.elog_config)

        # run through the expected events array and make sure all the elements are in place
        self.verify_events(self.expected_events)

    # test that the process_events function will update objects when run on objects that already exist
    def test_update_process_events(self):
        # Objects that are expected to already exist for this process to complete
        models.Station.objects.bulk_create([models.Station(name=s) for s in self.expected_stations])
        models.Instrument.objects.bulk_create([
            models.Instrument(name=i, instrument_type=models.InstrumentType[i.lower()])
            for i in self.expected_instruments])
        # ====================================================================== #

        # create events that will be updated when the process_events runs.
        self.create_events_entries(self.alt_events)
        # ====================================================================== #

        self.verify_events(self.alt_events)

        elog.process_events(self.log_file, self.mid_map, self.mid_map['buffer'].keys(), self.elog_config)

        self.verify_events(self.expected_events)

    def test_process_attachments_actions_time_location(self):
        # Objects that are expected to already exist for this process to complete
        models.Station.objects.bulk_create([models.Station(name=s) for s in self.expected_stations])
        models.Instrument.objects.bulk_create([
            models.Instrument(name=i, instrument_type=models.InstrumentType[i.lower()])
            for i in self.expected_instruments])

        self.create_events_entries(self.expected_events)

        elog.process_attachments_actions_time_location(self.log_file, self.mid_map, self.mid_map['buffer'].keys(),
                                                       self.elog_config)

        for e in self.expected_events:
            event = models.Event.objects.get(mission=self.mission, event_id=e['event_id'])
            for a in e['actions']:
                a_type = models.ActionType[a.lower()]
                if len(event.actions.filter(action_type=a_type)) <= 0:
                    self.fail(f"Expected Action {a} was not added to the database for event {e['event_id']}")

                action = event.actions.get(action_type=a_type)
                if action.date_time is None:
                    self.fail(f"Time was not set for event {e['event_id']}")

                if action.latitude is None:
                    self.fail(f"Latitude was not set for event {e['event_id']}")

                if action.longitude is None:
                    self.fail(f"Longitude was not set for event {e['event_id']}")

            for att in e['attached']:
                if len(event.attachments.filter(name=att)) <= 0:
                    self.fail(f"Expected attachment {att} was not added to the database for event {e['event_id']}")

    def test_get_create_variables(self):
        buffer = {
            "Flowmeter Start": "2020-06-06 00:00:00",
            "Flowmeter End": "2020-06-06 00:30:00",
        }
        action = cff.ActionFactory()
        return_array = elog.get_create_and_update_variables(action, buffer)

        # the creation array should contain some data, the update array should not
        self.assertTrue(len(return_array[0]) > 0)
        self.assertTrue(len(return_array[1]) <= 0)

        buffer_keys = [k for k in buffer.keys()]
        for index in range(0, len(return_array)):
            element = return_array[0][index]
            variable_name = buffer_keys[index]
            self.assertEquals(element.name.name, variable_name)
            self.assertEquals(element.value, buffer[variable_name])

    def test_get_update_variables(self):
        buffer = {
            "Flowmeter Start": "2020-06-06 00:00:00",
            "Flowmeter End": "2020-06-06 00:30:00",
        }

        buffer_keys = [k for k in buffer.keys()]

        action = cff.ActionFactory()

        for key in buffer_keys:
            variable_name = cff.VariableNameFactory(name=key)
            cff.VariableFieldFactory(action=action, name=variable_name, value="2020-05-05 00:00:00")

        return_array = elog.get_create_and_update_variables(action, buffer)

        # the update array should contain some data, the creation array should not
        self.assertTrue(len(return_array[0]) <= 0)
        self.assertTrue(len(return_array[1]) > 0)

        for index in range(0, len(return_array)):
            element = return_array[1][index]
            variable_name = buffer_keys[index]
            self.assertEquals(element.name.name, variable_name)
            self.assertEquals(element.value, buffer[variable_name])