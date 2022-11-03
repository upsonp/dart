from django.test import TestCase, tag
from django.urls import reverse_lazy

from rest_framework.test import APITestCase

import datetime
from . import CoreFactoryFloor as cff
from .. import models


@tag("test_api", "test_oxygen_api")
class TestOxygenApi(APITestCase):

    def setUp(self):
        super().setUp()

    def testListOxygen(self):
        mission = cff.MissionFactory()
        oxygen_samples = cff.OxygenSampleFactory.create_batch(10, mission=mission)

        response = self.client.get(reverse_lazy("core-api:oxygen-list"),
                                   {'mission_id': mission.pk},
                                   format='json')

        for i in range(0, len(response.data)):
            oxygen_sample = oxygen_samples[i]
            self.assertEquals(response.data[i],
                              {'bottle': oxygen_sample.bottle.bottle_id,
                               'winkler_1': oxygen_sample.winkler_1,
                               'winkler_2': oxygen_sample.winkler_2
                               })


@tag("test_api", "test_salt_api")
class TestSaltApi(APITestCase):

    def setUp(self):
        super().setUp()

    def testListSalt(self):
        mission = cff.MissionFactory()
        salt_samples = cff.SaltSampleFactory.create_batch(10, mission=mission)

        response = self.client.get(reverse_lazy("core-api:salt-list"),
                                   {'mission_id': mission.pk},
                                   format='json')

        for i in range(0, len(response.data)):
            salt_sample = salt_samples[i]
            self.assertEquals(response.data[i],
                              {'bottle': salt_sample.bottle.bottle_id,
                               'sample_id': salt_sample.sample_id,
                               'sample_date': datetime.datetime.strftime(salt_sample.sample_date, "%Y-%m-%dT%H:%M:%SZ"),
                               'calculated_salinity': salt_sample.calculated_salinity,
                               'comments': salt_sample.comments
                               })


@tag("test_api", "test_chl_api")
class TestChlApi(APITestCase):

    def setUp(self):
        super().setUp()

    def testListChl(self):
        mission = cff.MissionFactory()
        chl_samples = cff.ChlSampleFactory.create_batch(10, mission=mission)

        response = self.client.get(reverse_lazy("core-api:chl-list"),
                                   {'mission_id': mission.pk},
                                   format='json')

        for i in range(0, len(response.data)):
            chl_sample = chl_samples[i]
            self.assertEquals(response.data[i],
                              {'bottle': chl_sample.bottle.bottle_id,
                               'sample_order': chl_sample.sample_order,
                               'chl': chl_sample.chl,
                               'phae': chl_sample.phae,
                               'mean_chl': chl_sample.mean_chl,
                               'mean_phae': chl_sample.mean_phae,
                               })
