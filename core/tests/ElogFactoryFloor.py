import factory

from os.path import join

from factory.django import DjangoModelFactory
from faker import Faker
from faker.providers.file import Provider as file_provider
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

    name = factory.lazy_attribute(lambda o: number_provider.random_letters(length=2) + "_" +
                                            number_provider.random_number(digits=2))


class EventFactory(DjangoModelFactory):

    class Meta:
        model = models.Event

    event_id = factory.lazy_attribute(lambda o: number_provider.random_number(digits=3))
    mission = factory.SubFactory(MissionFactory)
    station = factory.SubFactory(Station)
    sample_id = factory.lazy_attribute(lambda o: (495000 + number_provider.random_number(digits=3)))
    end_sample_id = factory.lazy_attribute(lambda o: (496000 + number_provider.random_number(digits=3)))
