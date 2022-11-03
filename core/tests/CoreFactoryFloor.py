import factory

from django.utils import timezone

from factory.django import DjangoModelFactory
from faker import Faker

from faker.providers import BaseProvider as number_provider

from core import models

faker = Faker()


class MissionFactory(DjangoModelFactory):

    class Meta:
        model = models.Mission

    name = factory.lazy_attribute(lambda o: faker.catch_phrase())


class Station(DjangoModelFactory):

    class Meta:
        model = models.Station

    name = factory.lazy_attribute(lambda o: faker.bothify(text='??_##'))


class DataFileDirectoryFactory(DjangoModelFactory):

    class Meta:
        model = models.DataFileDirectory

    directory = factory.django.FileField(filename='/test/')
    mission = factory.SubFactory(MissionFactory)


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

    event_id = factory.lazy_attribute(lambda o: faker.random_number(digits=3))
    mission = factory.SubFactory(MissionFactory)
    station = factory.SubFactory(Station)


class ActionFactory(DjangoModelFactory):

    class Meta:
        model = models.Action

    event = factory.SubFactory(EventFactory)
    date_time = factory.lazy_attribute(lambda o: faker.date_time(tzinfo=timezone.get_current_timezone()))
    latitude = factory.lazy_attribute(lambda o: faker.pyfloat())
    longitude = factory.lazy_attribute(lambda o: faker.pyfloat())

    file = factory.SubFactory(LogFileFactory)

    mid = factory.lazy_attribute(lambda o: faker.random_number(digits=3))
    action_type = 1


class InstrumentFactory(DjangoModelFactory):
    class Meta:
        model = models.Instrument

    event = factory.SubFactory(EventFactory)
    name = factory.lazy_attribute(lambda o: faker.name())
    instrument_type = factory.lazy_attribute(lambda o: faker.random_int(1, len(models.InstrumentType.choices)))


class CTDEventFactory(EventFactory):
    sample_id = factory.lazy_attribute(lambda o: (495000 + faker.random_number(digits=3)))
    end_sample_id = factory.lazy_attribute(lambda o: (o.sample_id + faker.random_int(0, 24)))

    @classmethod
    def _after_postgeneration(cls, instance, create, results=None):
        file = LogFileFactory()

        instrument = InstrumentFactory(event=instance, name="CTD", instrument_type=models.InstrumentType.ctd.value)
        deployed = ActionFactory(file=file, event=instance, action_type=models.ActionType.deployed.value)
        bottom = ActionFactory(file=file, event=instance, action_type=models.ActionType.bottom.value)
        recovered = ActionFactory(file=file, event=instance, action_type=models.ActionType.recovered.value)


class BottleFactory(DjangoModelFactory):

    class Meta:
        model = models.Bottle

    event = factory.SubFactory(CTDEventFactory)
    date_time = factory.lazy_attribute(lambda o: faker.date_time(tzinfo=timezone.get_current_timezone()))
    bottle_number = factory.lazy_attribute(lambda o: faker.random_int(1, (o.event.end_sample_id-o.event.sample_id)))
    bottle_id = factory.lazy_attribute(lambda o: (o.event.sample_id + o.bottle_number))


class OxygenSampleFactory(DjangoModelFactory):

    class Meta:
        model = models.OxygenSample

    bottle = factory.SubFactory(BottleFactory)
    winkler_1 = factory.lazy_attribute(lambda o: (faker.random_number(digits=5)/1000.0))
    winkler_2 = factory.lazy_attribute(lambda o: (faker.random_number(digits=5)/1000.0))

    @classmethod
    def create_batch(cls, size, **kwargs):
        mission = MissionFactory() if 'mission' not in kwargs else kwargs['mission']

        event = CTDEventFactory(mission=mission)
        bottles = BottleFactory.create_batch(size, event=event)

        samples = [OxygenSampleFactory(bottle=b) for b in bottles]
        return samples


class SaltSampleFactory(DjangoModelFactory):

    class Meta:
        model = models.SaltSample

    bottle = factory.SubFactory(BottleFactory)
    sample_id = factory.lazy_attribute(lambda o: faker.name())
    sample_date = factory.lazy_attribute(lambda o: faker.date_time(tzinfo=timezone.get_current_timezone()))
    calculated_salinity = factory.lazy_attribute(lambda o: (faker.random_number(digits=5)/1000.0))

    @classmethod
    def create_batch(cls, size, **kwargs):
        mission = MissionFactory() if 'mission' not in kwargs else kwargs['mission']

        event = CTDEventFactory(mission=mission)
        bottles = BottleFactory.create_batch(size, event=event)

        samples = [SaltSampleFactory(bottle=b) for b in bottles]
        return samples


class ChlSampleFactory(DjangoModelFactory):

    class Meta:
        model = models.ChlSample

    bottle = factory.SubFactory(BottleFactory)
    sample_order = factory.lazy_attribute(lambda o: faker.random_int(0, 2))
    chl = factory.lazy_attribute(lambda o: (faker.random_number(digits=5)/1000.0))
    phae = factory.lazy_attribute(lambda o: (faker.random_number(digits=5)/1000.0))

    @classmethod
    def create_batch(cls, size, **kwargs):
        mission = MissionFactory() if 'mission' not in kwargs else kwargs['mission']

        event = CTDEventFactory(mission=mission)
        bottles = BottleFactory.create_batch(size, event=event)

        samples = [ChlSampleFactory(bottle=b) for b in bottles]
        return samples
