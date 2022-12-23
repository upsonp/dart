import datetime
import shutil
import numpy

from django.test import TestCase, tag
from . import CoreFactoryFloor as core_factory

from .. import models


# The purpose of tests in this suite is to test that the CoreFactory is building objects correctly, since these objects
# are used by other test suites it seems logical to make sure they are being constructed properly and will also
# indicate there are issues if the models change in the future


@tag("model", "model_mission")
class TestMission(TestCase):

    @tag("create", "create_mission")
    def test_create_mission(self):
        mission = core_factory.MissionFactory()

        self.assertIsNotNone(mission.name)


@tag("model", "model_datafiledirectory")
class TestDataFileDirectory(TestCase):

    # Data File Directories are attached to missions. The user specifies a location files exist and those files
    # are then loaded and accessable to the API.
    #
    # NOTE: (p. upson) I'm unsure if this is really a necessary table. Directories are specific to the machine
    #  a file is located on. It may be better to record just the files. The user can still specify where files
    #  should be searched for, but do we need to know forever where that directory was located?
    @tag("create", "create_datafiledirectory")
    def test_create_datafiledirectory(self):
        datafiledirectory = core_factory.DataFileDirectoryFactory()

        self.assertIsNotNone(datafiledirectory.mission)
        self.assertIsNotNone(datafiledirectory.directory)


@tag("model", "model_datafile")
class TestDataFile(TestCase):

    def tearDown(self) -> None:
        # files get created when the DataFileFactory creates a mock file so they have to be removed
        # or you end up with a ton of empty files.
        shutil.rmtree("test_temp")

    # DataFile describes a file that's been loaded into the system. A Datafile will have a
    # file name, file type (.log, .BTL, .csv, etc) and describe if the file has been processed
    # indicating if its already been loaded
    @tag("create", "create_datafile")
    def test_create_datafile(self):
        datafile = core_factory.DataFileFactory()

        self.assertIsNotNone(datafile.directory)
        self.assertIsNotNone(datafile.file)
        self.assertIsNotNone(datafile.file_type)
        self.assertIsNotNone(datafile.processed)

        self.assertFalse(datafile.processed)


@tag("model", "model_station")
class TestStation(TestCase):

    # station extends the simple lookup object, they're essentially just a names of locations
    # but need to be standardized
    @tag("create", "create_station")
    def test_create_station(self):
        station = core_factory.StationFactory()

        self.assertIsNotNone(station.name)
        self.assertRegex(station.name, "\w\w_\d\d")


@tag("model", "model_instrument")
class TestInstrument(TestCase):

    @tag("create", 'create_instrument')
    def test_create_instrument(self):
        instrument = core_factory.InstrumentFactory()

        self.assertIsNotNone(instrument.name)
        self.assertIsNotNone(instrument.instrument_type)


@tag("model", "model_event")
class TestEvent(TestCase):

    instrument = None

    def setUp(self):
        self.instrument = core_factory.InstrumentFactory(name="test", instrument_type=models.InstrumentType.other)

    # Event is an abstract object. Events typically depend on the piece of equipment
    # being used and as such may have different requirements so we'll use a mock object for testing
    # later on we'll be creating and testing more specific types of events
    class MockEvent(core_factory.EventFactory):
        sample_id = 0
        end_sample_id = 10

    @tag("create", "create_event")
    def test_create_event(self):
        event = self.MockEvent(instrument=self.instrument)

        self.assertIsNotNone(event.event_id)
        self.assertIsNotNone(event.mission)
        self.assertIsNotNone(event.station)

    @tag("action_model", "model_properties")
    def test_event_properties(self):
        # events have several property fields that depend on actions
        expected_start = datetime.datetime.strptime("2021-11-29 12:00:00 +00:00", "%Y-%m-%d %H:%M:%S %z")
        expected_end = datetime.datetime.strptime("2021-11-29 12:30:00 +00:00", "%Y-%m-%d %H:%M:%S %z")
        start_lat = 44.57990174559465
        start_lon = -63.51703362318107
        end_lat = 44.40620424722702
        end_lon = -63.332216764346384

        event = self.MockEvent(instrument=self.instrument)
        core_factory.ActionFactory(event=event, action_type=models.ActionType.deployed, date_time=expected_start,
                          latitude=start_lat, longitude=start_lon)
        core_factory.ActionFactory(event=event, action_type=models.ActionType.recovered, date_time=expected_end,
                          latitude=end_lat, longitude=end_lon)

        self.assertEquals(event.start_date, expected_start)
        self.assertEquals(event.start_location, [start_lat, start_lon])
        self.assertEquals(event.end_date, expected_end)
        self.assertEquals(event.end_location, [end_lat, end_lon])


@tag("model", "model_ctdevent")
class TestCtdEvent(TestEvent):

    # CTD event is a special case event specifically for events that have a CTD instrument
    # they must have an instrument, sample_id and an end_sample_id
    @tag("create", "create_ctdevent")
    def create_ctdevent(self):
        ctd_event = core_factory.CTDEventFactory()

        self.assertIsNotNone(ctd_event.sample_id)
        self.assertIsNotNone(ctd_event.end_sample_id)
        self.assertIsNotNone(ctd_event.instrument)
        self.assertEquals(ctd_event.instrument.instrument_type, models.InstrumentType.ctd.value)


@tag("model", "model_ringnetevent")
class TesTRingNetEvent(TestEvent):

    # RingNet event is a special case event specifically for events that have a RingNet instrument
    # they must have an instrument, sample_id
    @tag("create", "create_ringnetevent")
    def create_ringnetevent(self):
        ringnet_event = core_factory.RingnetEventFactory()

        self.assertIsNotNone(ringnet_event.sample_id)
        self.assertIsNotNone(ringnet_event.instrument)
        self.assertEquals(ringnet_event.instrument.instrument_type, models.InstrumentType.ringnet.value)


@tag("model", "model_instrumentsensor")
class TestInstrumentSensor(TestCase):

    @tag("create", "create_instrumentsensor")
    def test_create_instrumentsensor(self):
        sensor = core_factory.RingnetInstrumentSensorFactory()

        self.assertIsNotNone(sensor.event)
        self.assertIsNotNone(sensor.name)


@tag("model", "model_action")
class TestAction(TestCase):

    # actions depend on the instrument being used. In the case of a CTD the event must have
    # action:deployed and ((action:bottom and action:recovered) or action:aborted)
    @tag("create", "create_action")
    def test_create_action(self):
        action = core_factory.ActionFactory()

        self.assertIsNotNone(action.event)
        self.assertIsNotNone(action.date_time)
        self.assertIsNotNone(action.latitude)
        self.assertIsNotNone(action.longitude)
        self.assertIsNotNone(action.file)
        self.assertIsNotNone(action.mid)
        self.assertIsNotNone(action.action_type)


@tag("model", "model_bottle")
class TestBottle(TestCase):

    @tag("create", "create_bottle")
    def test_create_bottle(self):
        bottle = core_factory.BottleFactory()

        self.assertIsNotNone(bottle.event)
        # bottles should always be attached to a CTD event
        self.assertTrue(type(bottle.event), core_factory.CTDEventFactory)

        self.assertIsNotNone(bottle.date_time)
        self.assertIsNotNone(bottle.bottle_id)
        self.assertIsNotNone(bottle.bottle_number)
        self.assertIsNotNone(bottle.pressure)

    @tag("bulk_create", "bulk_create_bottle")
    def test_bulk_create_bottle(self):
        batch_create = 10
        # Each event is often made up of multiple bottles, when this happens
        # the bottles need to have sequential bottle_numbers
        bottles = core_factory.BottleFactory.build_batch(batch_create)

        p_numbrer = 0
        event_sample = bottles[0].event.sample_id
        self.assertEquals(len(bottles), batch_create)
        for b in bottles:
            self.assertEquals(b.bottle_number, (p_numbrer+1))
            self.assertEquals(b.bottle_id, (event_sample+b.bottle_number-1))
            p_numbrer = b.bottle_number
        else:
            self.assertEquals(b.bottle_id, b.event.end_sample_id)


@tag("model", "model_sensor")
class TestSensor(TestCase):

    @tag("create", "create_sensor")
    def test_create_sensor(self):
        sensor = core_factory.SensorDetailsFactory()

        self.assertIsNotNone(sensor.sensor_type)


@tag("model", "model_ctddata")
class TestCTDData(TestCase):

    @tag("create", "create_ctddata")
    def test_create_ctddata(self):
        data = core_factory.CTDDataFactory()

        self.assertIsNotNone(data.bottle)
        self.assertIsNotNone(data.sensor)
        self.assertIsNotNone(data.value)


@tag("model", "model_oxygensample")
class TestOxygenSample(TestCase):

    @tag("create", "create_oxygensample")
    def test_create_oxygensample(self):
        sample = core_factory.OxygenSampleFactory()

        self.assertIsNotNone(sample.file)
        self.assertIsNotNone(sample.bottle)
        self.assertIsNotNone(sample.winkler_1)

    @tag("model_properties")
    def test_property_average(self):
        wink_1 = 20.20
        wink_2 = 10.10

        os = core_factory.OxygenSampleFactory(winkler_1=wink_1, winkler_2=wink_2)
        self.assertEquals(os.average, numpy.average([wink_1, wink_2]))


@tag("model", "model_saltsample")
class TestSaltSample(TestCase):

    @tag("create", "create_saltsample")
    def test_create_saltsample(self):
        sample = core_factory.SaltSampleFactory()

        self.assertIsNotNone(sample.file)
        self.assertIsNotNone(sample.bottle)
        self.assertIsNotNone(sample.sample_date)
        self.assertIsNotNone(sample.sample_id)
        self.assertIsNotNone(sample.calculated_salinity)


@tag("model", "model_chlsample")
class TestChlSample(TestCase):

    @tag("create", "create_chlsample")
    def test_create_chlsample(self):
        sample = core_factory.ChlSampleFactory()

        self.assertIsNotNone(sample.file)
        self.assertIsNotNone(sample.bottle)
        self.assertIsNotNone(sample.sample_order)
        self.assertIsNotNone(sample.chl)
        self.assertIsNotNone(sample.phae)

        # CHL Samples are always done in pairs
        sample2 = sample.bottle.chl_data.get(sample_order=2)

    @tag("model_properties", "mean_chl")
    def test_mean_chl(self):
        sample_1 = core_factory.ChlSampleFactory()
        b = sample_1.bottle
        sample_2 = b.chl_data.get(sample_order=2)
        expected = numpy.average([sample_1.chl, sample_2.chl])

        self.assertEquals(sample_1.mean_chl, expected)

    @tag("model_properties", "mean_phae")
    def test_mean_chl(self):
        sample_1 = core_factory.ChlSampleFactory()
        b = sample_1.bottle
        sample_2 = b.chl_data.get(sample_order=2)
        expected = numpy.average([sample_1.phae, sample_2.phae])

        self.assertEquals(sample_1.mean_phae, expected)


@tag("model", "model_chnsample")
class TestChnSample(TestCase):

    @tag("create", "create_chnsample")
    def test_create_chnsample(self):
        sample = core_factory.ChnSampleFactory()

        self.assertIsNotNone(sample.file)
        self.assertIsNotNone(sample.bottle)
        self.assertIsNotNone(sample.sample_order)
        self.assertIsNotNone(sample.carbon)
        self.assertIsNotNone(sample.nitrogen)
        self.assertIsNotNone(sample.carbon_nitrogen)

        # CHN Samples are always done in pairs
        sample2 = sample.bottle.chn_data.get(sample_order=2)


@tag("model", "model_hplcsample")
class TestHplcSample(TestCase):

    @tag("create", "create_hplcsample")
    def test_create_hplcsample(self):
        sample = core_factory.HplcSampleFactory()

        self.assertIsNotNone(sample.file)
        self.assertIsNotNone(sample.bottle)

