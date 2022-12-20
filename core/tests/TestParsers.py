from django.test import TestCase, tag

from core import models
from . import CoreFactoryFloor as core_factory

import io

from core.parsers import parser_utils
from core.parsers import chn
from core.parsers import chl
from core.parsers import oxygen
from core.parsers import salt


@tag('parsers', 'parsers_chn')
class TestCHNParser(TestCase):

    sample_file = r'core/tests/sample_data/CHN_sample.xlsx'
    mission = None
    file_pointer = None

    def setUp(self):
        self.mission = core_factory.MissionFactory()

        self.file_pointer = io.FileIO(self.sample_file)

    def test_load_chn_invalid(self):
        errors = chn.load_data(mission_id=self.mission.pk, stream=self.file_pointer)

        # There should be no loaded bottles, so all samples are invalid
        self.assertGreater(len(errors), 0)

    def test_load_chn_valid(self):
        event = core_factory.CTDEventFactory(mission=self.mission, sample_id=488284)
        bottle = core_factory.BottleFactory(event=event, bottle_id=488284)

        errors = chn.load_data(mission_id=self.mission.pk, stream=self.file_pointer)

        chn_obj = models.ChnSample.objects.filter(bottle=bottle)
        self.assertTrue(chn_obj.exists())

    def test_parse_chn(self):

        df = parser_utils.get_dataframe(self.file_pointer)
        samples = chn.parse_dataframe(dataframe=df)

        self.assertGreater(len(samples), 0)

    def test_get_dataframe(self):
        df = parser_utils.get_dataframe(self.file_pointer)
        expected_headers = ["I.D.", "VOLUME(L)", "CARBON(micrograms)", "POC_QC", "NITROGEN(micrograms)", "PON_QC",
                            "C/L(micrograms/litre)", "POC_QC.1", "N/L(micrograms/litre)", "PON_QC.1",  "C/N"]
        self.assertIsNotNone(df)
        for k in df.keys():
            self.assertIn(k, expected_headers)


@tag('parsers', 'parsers_chl')
class TestCHLParser(TestCase):

    sample_file = r'core/tests/sample_data/CHL_sample.xlsx'
    mission = None
    file_pointer = None

    def setUp(self):
        self.mission = core_factory.MissionFactory()

        self.file_pointer = io.FileIO(self.sample_file)

    def test_load_chl_invalid(self):
        errors = chl.load_data(mission_id=self.mission.pk, stream=self.file_pointer)

        # There should be no loaded bottles, so all samples are invalid
        self.assertGreater(len(errors), 0)

    def test_load_chl_valid(self):
        event = core_factory.CTDEventFactory(mission=self.mission, sample_id=488284)
        bottle = core_factory.BottleFactory(event=event, bottle_id=488284)

        errors = chl.load_data(mission_id=self.mission.pk, stream=self.file_pointer)

        chl_obj = models.ChlSample.objects.filter(bottle=bottle)
        self.assertTrue(chl_obj.exists())

    def test_parse_chl(self):

        df = parser_utils.get_dataframe(self.file_pointer)
        samples = chl.parse_dataframe(dataframe=df)

        self.assertGreater(len(samples), 0)

    def test_get_dataframe(self):
        df = parser_utils.get_dataframe(self.file_pointer)
        expected_headers = ["I.D.", "VOLUME", "RANGE", "Rb", "Ra", "Rb.1", "Ra.1", "CAL.COEF", "CHL.", "PHAE.", "C+P",
                            "CHL/P.", "MEAN C", "MEAN P"]

        self.assertIsNotNone(df)
        for k in df.keys():
            self.assertIn(k, expected_headers)


@tag('parsers', 'parsers_oxy')
class TestOxyParser(TestCase):

    sample_file = r'core/tests/sample_data/Oxygen_sample.xlsx'
    mission = None
    file_pointer = None

    def setUp(self):
        self.mission = core_factory.MissionFactory()

        self.file_pointer = io.FileIO(self.sample_file)

    def test_load_oxy_invalid(self):
        errors = oxygen.load_data(mission_id=self.mission.pk, stream=self.file_pointer)

        # There should be no loaded bottles, so all samples are invalid
        self.assertGreater(len(errors), 0)

    def test_load_oxy_valid(self):
        event = core_factory.CTDEventFactory(mission=self.mission, sample_id=488275)
        bottle = core_factory.BottleFactory(event=event, bottle_id=488275)

        errors = oxygen.load_data(mission_id=self.mission.pk, stream=self.file_pointer)

        oxy_obj = models.OxygenSample.objects.filter(bottle=bottle)
        self.assertTrue(oxy_obj.exists())

    def test_parse_oxy(self):

        df = parser_utils.get_dataframe(self.file_pointer)
        samples = oxygen.parse_dataframe(dataframe=df)

        self.assertGreater(len(samples), 0)

    def test_get_dataframe(self):
        df = parser_utils.get_dataframe(self.file_pointer)
        expected_headers = ["Sample", "Bottle#", "O2_Concentration(ml/l)", "O2_Uncertainty(ml/l)", "Titrant_volume(ml)",
                            "Titrant_uncertainty(ml)", "Analysis_date", "Data_file", "Standards(ml)", "Blanks(ml)", "Bottle_volume(ml)",
                            "Initial_transmittance(%%)", "Standard_transmittance0(%%)", "Comments"]

        self.assertIsNotNone(df)
        for k in df.keys():
            self.assertIn(k, expected_headers)


@tag('parsers', 'parsers_salt')
class TestSaltParser(TestCase):

    sample_file = r'core/tests/sample_data/Salts_sample.xlsx'
    mission = None
    file_pointer = None

    def setUp(self):
        self.mission = core_factory.MissionFactory()

        self.file_pointer = io.FileIO(self.sample_file)

    def test_load_salt_invalid(self):
        errors = salt.load_data(mission_id=self.mission.pk, stream=self.file_pointer)

        # There should be no loaded bottles, so all samples are invalid
        self.assertGreater(len(errors), 0)

    def test_load_salt_valid(self):
        event = core_factory.CTDEventFactory(mission=self.mission, sample_id=488275)
        bottle = core_factory.BottleFactory(event=event, bottle_id=488275)

        errors = salt.load_data(mission_id=self.mission.pk, stream=self.file_pointer)

        salt_obj = models.SaltSample.objects.filter(bottle=bottle)
        self.assertTrue(salt_obj.exists())

    def test_parse_salt(self):

        df = parser_utils.get_dataframe(self.file_pointer)
        samples = salt.parse_dataframe(dataframe=df)

        self.assertGreater(len(samples), 0)

    def test_get_dataframe(self):
        df = parser_utils.get_dataframe(self.file_pointer)
        expected_headers = ["Sample ID", "Reading #", "Value #", "Bottle Label", "DateTime", "Bath Temperature",
                            "Uncorrected Ratio", "Uncorrected Ratio StandDev", "Correction", "Adjusted Ratio",
                            "Calculated Salinity", "Salinity_QC", "Calculated Salinity StandDev", "Comments"]

        self.assertIsNotNone(df)
        for k in df.keys():
            self.assertIn(k, expected_headers)
