from datetime import datetime
from datetime import timedelta

import factory
import pytz

from django.utils import timezone

from factory.django import DjangoModelFactory
from faker import Faker

from core import models

faker = Faker()


class MissionFactory(DjangoModelFactory):

    class Meta:
        model = models.Mission

    name = factory.lazy_attribute(lambda o: faker.catch_phrase())


class DataFileDirectoryFactory(DjangoModelFactory):

    class Meta:
        model = models.DataFileDirectory

    directory = factory.django.FileField(filename='/test/')
    mission = factory.SubFactory(MissionFactory)


class DataFileFactory(DjangoModelFactory):

    class Meta:
        model = models.DataFile

    directory = factory.SubFactory(DataFileDirectoryFactory)
    file_type = factory.lazy_attribute(lambda o: faker.random.choice(models.FileType.choices)[0])


class LogFileFactory(DataFileFactory):

    file = factory.django.FileField(filename='2010.log')
    file_type = models.FileType.log.value
    processed = factory.lazy_attribute(lambda o: faker.boolean())


class StationFactory(DjangoModelFactory):

    class Meta:
        model = models.Station

    name = factory.lazy_attribute(lambda o: faker.bothify(text='??_##'))


class InstrumentFactory(DjangoModelFactory):
    class Meta:
        model = models.Instrument

    name = factory.lazy_attribute(lambda o: faker.name())
    instrument_type = factory.lazy_attribute(lambda o: faker.random.choice(models.InstrumentType.choices)[0])


class EventFactory(DjangoModelFactory):

    class Meta:
        model = models.Event
        abstract = True

    # Instrument, sample_id and end_sample_id should be set by extending classes because they're typically dependent
    # on the type of instrument the event is recording

    event_id = factory.lazy_attribute(lambda o: faker.random_number(digits=3))
    mission = factory.SubFactory(MissionFactory)
    station = factory.SubFactory(StationFactory)
    instrument = factory.SubFactory(InstrumentFactory, name="other", instrument_type=models.InstrumentType.other)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        # to be a complete and proper event often multiple, specific, actions are required
        # I'm allowing a user to call this and child factories with the 'actions' keyword
        # and pass in a list of action types (see: models.ActionType) to automagically create
        # the required actions.
        actions = None
        if 'actions' in kwargs:
            actions = kwargs.pop('actions')

        event = super()._create(model_class, *args, **kwargs)

        if actions:
            file = DataFileFactory()
            for action in actions:
                ActionFactory(file=file, event=event, action_type=action)

        return event


class CTDEventFactory(EventFactory):

    instrument = factory.SubFactory(InstrumentFactory, name=models.InstrumentType.ctd.name,
                                    instrument_type=models.InstrumentType.ctd)

    sample_id = factory.lazy_attribute(lambda o: faker.random.randint(0, 1000))
    end_sample_id = factory.lazy_attribute(lambda o: (o.sample_id + faker.random.randint(0, 1000)))


class RingnetEventFactory(EventFactory):

    instrument = factory.SubFactory(InstrumentFactory, name=models.InstrumentType.ringnet.name,
                                    instrument_type=models.InstrumentType.ringnet)

    sample_id = factory.lazy_attribute(lambda o: faker.random.randint(0, 1000))
    end_sample_id = None


class RingnetInstrumentSensorFactory(DjangoModelFactory):

    class Meta:
        model = models.InstrumentSensor

    event = factory.SubFactory(RingnetEventFactory)
    name = factory.lazy_attribute(lambda o: faker.random.choice(['202um', '76um']))


class BottleFactory(DjangoModelFactory):

    class Meta:
        model = models.Bottle

    event = factory.SubFactory(CTDEventFactory)
    date_time = factory.lazy_attribute(lambda o: faker.date_time(tzinfo=timezone.get_current_timezone()))
    bottle_number = factory.lazy_attribute(lambda o: faker.random_int(1, (o.event.end_sample_id-o.event.sample_id)))
    bottle_id = factory.lazy_attribute(lambda o: (o.bottle_number + o.event.sample_id) -1)
    pressure = factory.lazy_attribute(lambda o: faker.pyfloat())

    @classmethod
    def build_batch(cls, size, **kwargs):

        sample_id = faker.random.randint(0, 1000)
        event = CTDEventFactory(sample_id=sample_id, end_sample_id=(sample_id + size - 1))
        bottles = []
        for i in range(1, size+1):
            kwargs['event'] = event
            kwargs['bottle_number'] = i
            bottles.append(BottleFactory(**kwargs))

        return bottles


class ActionFactory(DjangoModelFactory):

    class Meta:
        model = models.Action

    event = factory.SubFactory(EventFactory)
    date_time = factory.lazy_attribute(lambda o: faker.date_time(tzinfo=timezone.get_current_timezone()))
    latitude = factory.lazy_attribute(lambda o: faker.pyfloat())
    longitude = factory.lazy_attribute(lambda o: faker.pyfloat())

    file = factory.SubFactory(LogFileFactory)

    mid = factory.lazy_attribute(lambda o: faker.random_number(digits=3))
    action_type = factory.lazy_attribute(lambda o: faker.random.choice(models.ActionType.choices)[0])


class VariableNameFactory(DjangoModelFactory):

    class Meta:
        model = models.VariableName

    name = factory.lazy_attribute(lambda o: faker.name())


class VariableFieldFactory(DjangoModelFactory):

    class Meta:
        model = models.VariableField

    action = factory.SubFactory(ActionFactory)
    name = factory.SubFactory(VariableNameFactory)
    value = factory.lazy_attribute(lambda o: faker.nam())


class SensorFactory(DjangoModelFactory):

    class Meta:
        model = models.Sensor

    name = factory.lazy_attribute(lambda o: faker.name())
    sensor_type = factory.lazy_attribute(lambda o: faker.random.choice(models.SensorType.choices)[0])
    priority = factory.lazy_attribute(lambda o: faker.random.randint(1, 5))


class CTDDataFactory(DjangoModelFactory):

    class Meta:
        model = models.CTDData

    bottle = factory.SubFactory(BottleFactory)
    sensor = factory.SubFactory(SensorFactory)
    value = factory.lazy_attribute(lambda o: faker.pyfloat())


class SampleFactory(DjangoModelFactory):

    class Meta:
        abstract = True

    file = factory.lazy_attribute(lambda o: faker.name())
    bottle = factory.SubFactory(BottleFactory)


class OxygenSampleFactory(SampleFactory):

    class Meta:
        model = models.OxygenSample

    winkler_1 = factory.lazy_attribute(lambda o: faker.pyfloat())


class SaltSampleFactory(SampleFactory):

    class Meta:
        model = models.SaltSample

    sample_date = factory.lazy_attribute(lambda o: faker.date_time(tzinfo=timezone.get_current_timezone()))
    sample_id = factory.lazy_attribute(lambda o: faker.name)
    calculated_salinity = factory.lazy_attribute(lambda o: faker.pyfloat())


class ChlSampleFactory(SampleFactory):

    class Meta:
        model = models.ChlSample

    sample_order = 1
    chl = factory.lazy_attribute(lambda o: faker.pyfloat())
    phae = factory.lazy_attribute(lambda o: faker.pyfloat())

    @classmethod
    def _after_postgeneration(cls, instance, create, results=None):
        if create and instance.sample_order == 1:
            file = instance.file
            bottle = instance.bottle
            ChlSampleFactory(file=file, bottle=bottle, sample_order=2)


class ChnSampleFactory(SampleFactory):

    class Meta:
        model = models.ChnSample

    sample_order = 1
    carbon = factory.lazy_attribute(lambda o: faker.pyfloat())
    nitrogen = factory.lazy_attribute(lambda o: faker.pyfloat())
    carbon_nitrogen = factory.lazy_attribute(lambda o: faker.pyfloat())

    @classmethod
    def _after_postgeneration(cls, instance, create, results=None):
        if create and instance.sample_order == 1:
            file = instance.file
            bottle = instance.bottle
            ChnSampleFactory(file=file, bottle=bottle, sample_order=2)


class HplcSampleFactory(SampleFactory):

    class Meta:
        model = models.HplcSample


def convert_degs_dms(dd):
    d = int(dd)
    m = float((dd-d)*60.0)

    return f'{d} {m}'


def get_time_position(date_time=None):
    dt = datetime.now(pytz.utc) if not date_time else date_time
    date = datetime.strftime(dt, '%Y-%m-%d')
    time = datetime.strftime(dt, '%H%M%S.%f')
    lat = convert_degs_dms(faker.pyfloat(2, 5, True, 0, 90)) + ' ' + faker.random.choice(['N', 'S'])
    lon = convert_degs_dms(faker.pyfloat(3, 5, True, 0, 180)) + ' ' + faker.random.choice(['W', 'E'])

    return f'{date} | {time} | {lat} | {lon}'


# Creates Elog like objects used for testing utilities for reading log files
class MidObjectFactory(factory.DictFactory):

    class Meta:
        rename = {
            'date': 'Date', 'event': 'Event', 'station': 'Station',
            'instrument': 'Instrument', 'attached': 'Attached', 'number_of_bottles': 'Number_of_Bottles',
            'flow_sn': "Flowmeter S / N", 'flow_start': 'Flowmeter Start', 'flow_end': 'Flowmeter End',
            'action': 'Action', 'sounding': 'Sounding', 'sample_id': 'Sample ID', 'end_sample_id': 'End_Sample_ID',
            'wire_out': 'Wire out', 'wire_angle': 'Wire Angle', 'new_clogging': 'Net Clogging',
            'wind_direction': 'Wind Direction', 'wind_speed': 'Wind Speed(nm)', 'sky': 'Sky(condition)',
            'swell_direction': 'Swell Direction', 'swell_height': 'Swell Height(M)', 'author': 'Author',
            'sea': 'Sea(Condition)', 'depth': 'Depth', 'sn': 'S / N', 'name': 'Name', 'comment': 'Comment',
            'time_position': 'Time|Position', 'cruise': 'Cruise', 'pi': 'PI', 'protocol': 'Protocol',
            'platform': 'Platform', 'mooring_number': 'Mooring Number', 'number_of_rcms': 'Number of RCMs',
            'number_of_microcats': 'Number of MicroCATs',
            'number_of_temperature_recorders': 'Number of Temperature Recorders',
            'number_of_amars': 'Number of Amars', 'attachment': 'Attachment', 'encoding': 'Encoding'
        }

    date = factory.lazy_attribute(lambda o: datetime.now(pytz.utc))
    event = 1
    station = factory.lazy_attribute(lambda o: faker.bothify(text='??_##'))
    instrument = factory.lazy_attribute(lambda o: faker.random.choice(models.InstrumentType.choices)[1])
    attached = ''
    number_of_bottles = ''
    flow_sn = ''
    flow_start = ''
    flow_end = ''
    action = factory.lazy_attribute(lambda o: faker.random.choice(models.ActionType.choices)[1])
    sounding = factory.lazy_attribute(lambda o: faker.pyfloat())
    sample_id = ''
    end_sample_id = ''
    wire_out = ''
    wire_angle = ''
    new_clogging = ''
    wind_direction = ''
    wind_speed = ''
    sky = ''
    swell_direction = ''
    swell_height = ''
    sea = ''
    depth = ''
    author = 'Patrick Upson'
    IMEI_No = ''
    WMO_No = ''
    sn = ''
    name = ''
    comment = ''
    time_position = factory.lazy_attribute(lambda o: get_time_position())
    cruise = 'JC24301'
    pi = 'Lindsay Beazley'
    protocol = 'AZMP'
    platform = 'James Cook'
    Revisions = ''
    mooring_number = ''
    number_of_rcms = ''
    number_of_microcats = ''
    number_of_temperature_recorders = ''
    number_of_amars = ''
    attachment = ''
    encoding = 'plain'

    @classmethod
    def create_batch(cls, size, **kwargs):
        mids = []
        start_sample = 495000
        start_time = datetime.now(pytz.utc)
        for i in range(0, size):
            mid = MidObjectFactory(sample_id=start_sample, time_position=get_time_position(start_time))
            mids.append(mid)
            start_sample = mid['End_Sample_ID']
            # randomly add some time between events
            start_time += timedelta(minutes=faker.random.randint(15, 60))

        return mids

    @staticmethod
    def get_ctd_net_event(**kwargs):
        instrument = faker.random.choice([models.InstrumentType.ctd, models.InstrumentType.ringnet])
        if 'instrument' in kwargs:
            instrument = models.InstrumentType[kwargs['instrument'].lower()]
        else:
            kwargs[instrument] = instrument.label

        start_sample = kwargs['sample_id'] if 'sample_id' in kwargs else (495000 + faker.random.randint(0, 999))
        kwargs['sample_id'] = start_sample

        if instrument == instrument.ctd:
            end_sample = kwargs['end_sample_id'] if 'end_sample_id' in kwargs else \
                (kwargs['sample_id'] + faker.random.randint(1, 24))
            kwargs['end_sample_id'] = end_sample
            kwargs['attached'] = kwargs['attached'] if 'attached' in kwargs else 'pH | SBE35'
        else:
            kwargs['attached'] = kwargs['attached'] if 'attached' in kwargs else faker.random.choice(['202um', '76um'])

        time = (kwargs['time_position'] if 'time_position' in kwargs else None)
        start_time = datetime.now(pytz.utc)
        if time:
            t = time.split(" | ")
            start_time = datetime.strptime(f'{t[0]} {t[1]}', '%Y-%m-%d %H%M%S.%f')

        # these are unique to each CTD event action.
        kwargs['time_position'] = get_time_position(start_time)
        kwargs['action'] = models.ActionType.deployed.label
        deployed = MidObjectFactory(**kwargs)

        bottom_time = start_time + timedelta(minutes=faker.random.randint(3, 30))
        kwargs['time_position'] = get_time_position(bottom_time)
        kwargs['action'] = models.ActionType.bottom.label
        kwargs['station'] = deployed['Station']
        bottom = MidObjectFactory(**kwargs)

        recover_time = start_time + timedelta(minutes=faker.random.randint(3, 30))
        kwargs['time_position'] = get_time_position(recover_time)
        kwargs['action'] = models.ActionType.recovered.label
        kwargs['station'] = deployed['Station']
        reccovered = MidObjectFactory(**kwargs)

        return [deployed, bottom, reccovered]