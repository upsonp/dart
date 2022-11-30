from django.test import TestCase, tag

from . import CoreFactoryFloor as cff
from .. import utils

from .. import models


@tag('utils')
class TestElogProcessing(TestCase):

    expected_stations = ['st_01', 'st_02']
    expected_instruments = ['CTD', 'RingNet']
    expected_events = [
        {
            'event_id': 1, 'instrument': expected_instruments[0], 'station': expected_stations[0],
            'attached': ['pH', 'SBE35'], 'actions': ['Deployed', 'Bottom', 'Recovered']
        },
        {
            'event_id': 2, 'instrument': expected_instruments[1], 'station': expected_stations[0],
            'attached': ['80um'], 'actions': ['Deployed', 'Bottom', 'Recovered']
        },
        {
            'event_id': 3, 'instrument': expected_instruments[0], 'station': expected_stations[1],
            'attached': ['SBE35'], 'actions': ['Deployed', 'Bottom', 'Recovered']
        },
    ]

    mid_map = None

    def setUp(self):
        super().setUp()

        log_file = cff.LogFileFactory(processed=False)

        mids = []
        for e in self.expected_events:
            mids += cff.MidObjectFactory.get_ctd_net_event(
                event=e['event_id'], instrument=e['instrument'], station=e['station'],
                attached=' | '.join(e['attached'])
            )

        self.mid_map = {'file': log_file, 'buffer': {i+1: mids[i] for i in range(0, len(mids))}}

    def test_process_station_instrument(self):
        log_file = self.mid_map['file']
        utils.process_stations_instrumnets(log_file, self.mid_map, self.mid_map['buffer'].keys())

        for s in self.expected_stations:
            if len(models.Station.objects.filter(name=s)) <= 0:
                self.fail(f"Expected Station {s} was not added to the database")

        for i in self.expected_instruments:
            if len(models.Instrument.objects.filter(name=i)) <= 0:
                self.fail(f"Expected Instrument {i} was not added to the database")

    def test_process_events(self):
        # Objects that are expected to already exist for this process to complete
        log_file = self.mid_map['file']
        mission = log_file.directory.mission

        models.Station.objects.bulk_create([models.Station(name=s) for s in self.expected_stations])
        models.Instrument.objects.bulk_create([
            models.Instrument(name=i, instrument_type=models.InstrumentType[i.lower()])
            for i in self.expected_instruments])

        utils.process_events(log_file, self.mid_map, self.mid_map['buffer'].keys())

        for e in self.expected_events:
            if len(models.Event.objects.filter(mission=mission, event_id=e['event_id'])) <= 0:
                self.fail(f"Expected Event {e} was not added to the database")

            event = models.Event.objects.get(mission=mission, event_id=e['event_id'])
            inst = e['instrument']
            self.assertEquals(event.instrument, models.Instrument.objects.get(
                name=inst, instrument_type=models.InstrumentType[inst.lower()]))

            self.assertEquals(event.station, models.Station.objects.get(name=e['station']))

    def test_process_attachments_actions_time_location(self):
        # Objects that are expected to already exist for this process to complete
        log_file = self.mid_map['file']
        mission = log_file.directory.mission

        models.Station.objects.bulk_create([models.Station(name=s) for s in self.expected_stations])
        models.Instrument.objects.bulk_create([
            models.Instrument(name=i, instrument_type=models.InstrumentType[i.lower()])
            for i in self.expected_instruments])

        models.Event.objects.bulk_create([
            models.Event(
                mission=mission, event_id=e['event_id'],
                instrument=models.Instrument.objects.get(name=e['instrument']),
                station=models.Station.objects.get(name=e['station'])
            ) for e in self.expected_events
        ])

        utils.process_attachments_actions_time_location(log_file, self.mid_map, self.mid_map['buffer'].keys())

        for e in self.expected_events:
            event = models.Event.objects.get(mission=mission, event_id=e['event_id'])
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