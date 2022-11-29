import factory

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


class StationFactory(DjangoModelFactory):

    class Meta:
        model = models.Station

    name = factory.lazy_attribute(lambda o: faker.bothify(text='??_##'))


class InstrumentFactory(DjangoModelFactory):
    class Meta:
        model = models.Instrument

    name = factory.lazy_attribute(lambda o: faker.name())
    instrument_type = factory.lazy_attribute(lambda o: faker.random.choice(models.InstrumentType.choices)[0])


class LogFileFactory(DjangoModelFactory):

    class Meta:
        model = models.DataFile

    directory = factory.SubFactory(DataFileDirectoryFactory)

    file = factory.django.FileField(filename='2010.log')
    file_type = models.FileType.log.value
    processed = factory.lazy_attribute(lambda o: faker.boolean())


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
    pressure = factory.lazy_attribute(lambda o: faker.pyfloat())

    @classmethod
    def build_batch(cls, size, **kwargs):

        sample_id = faker.random.randint(0, 1000)
        event = CTDEventFactory(sample_id=sample_id, end_sample_id=(sample_id + size))
        bottles = []
        for i in range(1, size):
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
