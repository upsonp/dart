import datetime

from django.test import TestCase, tag

from core import models
from . import CoreFactoryFloor as core_factory

import io
import ctd
import re

from core.parsers import parser_utils
from core.parsers import chn
from core.parsers import chl
from core.parsers import oxy
from core.parsers import salt
from core.parsers import hplc
from core.parsers import ctd as ctd_parser

@tag('parsers', 'parsers_chn')
class TestCHNParser(TestCase):

    model = models.ChnSample
    sample_directory = r'core/tests/sample_data/'
    sample_file_name = 'CHN_sample.xlsx'
    sample_file = sample_directory + sample_file_name
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

        chn_obj = self.model.objects.filter(bottle=bottle)
        self.assertTrue(chn_obj.exists())

    def test_parse_chn(self):

        df = parser_utils.get_dataframe(self.file_pointer, chn.CHN_REQUIRED_HEADERS)
        samples = chn.parse_dataframe(file_name=self.sample_file_name, dataframe=df)

        self.assertGreater(len(samples), 0)

    def test_get_dataframe(self):
        df = parser_utils.get_dataframe(self.file_pointer, chn.CHN_REQUIRED_HEADERS)
        expected_headers = ["I.D.", "VOLUME(L)", "CARBON(micrograms)", "POC_QC", "NITROGEN(micrograms)", "PON_QC",
                            "C/L(micrograms/litre)", "POC_QC.1", "N/L(micrograms/litre)", "PON_QC.1",  "C/N"]
        self.assertIsNotNone(df)
        for k in df.keys():
            self.assertIn(k, expected_headers)


@tag('parsers', 'parsers_chl')
class TestCHLParser(TestCase):

    model = models.ChlSample
    sample_directory = r'core/tests/sample_data/'
    sample_file_name = 'CHL_sample.xlsx'
    sample_file = sample_directory + sample_file_name
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

        chl_obj = self.model.objects.filter(bottle=bottle)
        self.assertTrue(chl_obj.exists())

    def test_parse_chl(self):

        df = parser_utils.get_dataframe(self.file_pointer, chl.CHL_REQUIRED_HEADERS)
        samples = chl.parse_dataframe(file_name=self.sample_file_name, dataframe=df)

        self.assertGreater(len(samples), 0)

    def test_get_dataframe(self):
        df = parser_utils.get_dataframe(self.file_pointer, chl.CHL_REQUIRED_HEADERS)
        expected_headers = ["I.D.", "VOLUME", "RANGE", "Rb", "Ra", "Rb.1", "Ra.1", "CAL.COEF", "CHL.", "PHAE.", "C+P",
                            "CHL/P.", "MEAN C", "MEAN P"]

        self.assertIsNotNone(df)
        for k in df.keys():
            self.assertIn(k, expected_headers)


@tag('parsers', 'parsers_oxy')
class TestOxyParser(TestCase):

    model = models.OxygenSample
    sample_directory = r'core/tests/sample_data/'
    sample_file_name = 'Oxygen_sample.xlsx'
    sample_file = sample_directory + sample_file_name
    mission = None
    file_pointer = None

    def setUp(self):
        self.mission = core_factory.MissionFactory()

        self.file_pointer = io.FileIO(self.sample_file)

    def test_load_oxy_invalid(self):
        errors = oxy.load_data(mission_id=self.mission.pk, stream=self.file_pointer)

        # There should be no loaded bottles, so all samples are invalid
        self.assertGreater(len(errors), 0)

    def test_load_oxy_valid(self):
        event = core_factory.CTDEventFactory(mission=self.mission, sample_id=488275)
        bottle = core_factory.BottleFactory(event=event, bottle_id=488275)

        errors = oxy.load_data(mission_id=self.mission.pk, stream=self.file_pointer)

        oxy_obj = self.model.objects.filter(bottle=bottle)
        self.assertTrue(oxy_obj.exists())

    def test_parse_oxy(self):

        df = parser_utils.get_dataframe(self.file_pointer, oxy.OXY_REQUIRED_HEADERS)
        samples = oxy.parse_dataframe(file_name=self.sample_file_name, dataframe=df)

        self.assertGreater(len(samples), 0)

    def test_get_dataframe(self):
        df = parser_utils.get_dataframe(self.file_pointer, oxy.OXY_REQUIRED_HEADERS)
        expected_headers = ["Sample", "Bottle#", "O2_Concentration(ml/l)", "O2_Uncertainty(ml/l)", "Titrant_volume(ml)",
                            "Titrant_uncertainty(ml)", "Analysis_date", "Data_file", "Standards(ml)", "Blanks(ml)", "Bottle_volume(ml)",
                            "Initial_transmittance(%%)", "Standard_transmittance0(%%)", "Comments"]

        self.assertIsNotNone(df)
        for k in df.keys():
            self.assertIn(k, expected_headers)


@tag('parsers', 'parsers_salt')
class TestSaltParser(TestCase):

    model = models.SaltSample
    sample_directory = r'core/tests/sample_data/'
    sample_file_name = 'Salts_sample.xlsx'
    sample_file = sample_directory + sample_file_name
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

        salt_obj = self.model.objects.filter(bottle=bottle)
        self.assertTrue(salt_obj.exists())

    def test_parse_salt(self):

        df = parser_utils.get_dataframe(self.file_pointer, salt.SALT_REQUIRED_HEADERS)
        samples = salt.parse_dataframe(file_name=self.sample_file_name, dataframe=df)

        self.assertGreater(len(samples), 0)

    def test_get_dataframe(self):
        df = parser_utils.get_dataframe(self.file_pointer, salt.SALT_REQUIRED_HEADERS)
        expected_headers = ["Sample ID", "Reading #", "Value #", "Bottle Label", "DateTime", "Bath Temperature",
                            "Uncorrected Ratio", "Uncorrected Ratio StandDev", "Correction", "Adjusted Ratio",
                            "Calculated Salinity", "Salinity_QC", "Calculated Salinity StandDev", "Comments"]

        self.assertIsNotNone(df)
        for k in df.keys():
            self.assertIn(k, expected_headers)


@tag('parsers', 'parsers_hplc')
class TestHPLCParser(TestCase):
    model = models.HplcSample
    sample_directory = r'core/tests/sample_data/'
    sample_file_name = 'HPLC_sample.xlsx'
    sample_file = sample_directory + sample_file_name
    mission = None
    file_pointer = None

    def setUp(self):
        self.mission = core_factory.MissionFactory()

        self.file_pointer = io.FileIO(self.sample_file)

    def test_load_hplc_invalid(self):
        errors = hplc.load_data(mission_id=self.mission.pk, stream=self.file_pointer)

        # There should be no loaded bottles, so all samples are invalid
        self.assertGreater(len(errors), 0)

    def test_load_hplc_valid(self):
        event = core_factory.CTDEventFactory(mission=self.mission, sample_id=488281)
        bottle = core_factory.BottleFactory(event=event, bottle_id=488281)

        errors = hplc.load_data(mission_id=self.mission.pk, stream=self.file_pointer)

        hplc_obj = self.model.objects.filter(bottle=bottle)
        self.assertTrue(hplc_obj.exists())

    def test_parse_hplc(self):

        df = parser_utils.get_dataframe(self.file_pointer, hplc.HPLC_REQUIRED_HEADERS)
        samples = hplc.parse_dataframe(file_name=self.sample_file_name, dataframe=df)

        self.assertGreater(len(samples), 0)

    def test_get_dataframe(self):
        df = parser_utils.get_dataframe(self.file_pointer, hplc.HPLC_REQUIRED_HEADERS)
        expected_headers = ["ID", "DEPTH", "BUT19", "HEX19", "ALLOX", "ACAROT", "ASTAX", "BCAROT", "BUTLIKE", "CHLB",
                            "CHLC12", "CHLC3", "CHLIDEA", "DIADINOX", "DIATOX", "FUCOX", "HEXLIKE2", "HEXLIKE",
                            "HPLCHLA", "HPLCPHAE", "PERID", "PRASINOX", "PYROPHAE", "TOTCHLC", "VIOLAX", "ZEA",
                            "Abs Volume(L)"]

        self.assertIsNotNone(df)
        for k in df.keys():
            self.assertIn(k, expected_headers)


@tag('parsers', 'parsers_ctd')
class TestCtd(TestCase):
    model = models.Bottle
    sample_directory = r'core/tests/sample_data/'
    sample_file_name = '185A007.BTL'
    sample_file = sample_directory + sample_file_name
    mission = None
    dataframe = None

    def setUp(self):
        self.mission = core_factory.MissionFactory()
        self.dataframe = ctd.from_btl(self.sample_file)

    def test_get_event_number(self):
        """Given a CTD dataframe created by the CTD package, acquire a log event number a bottle is attached to"""

        event_number = ctd_parser.get_event_number(self.dataframe)
        self.assertEquals(event_number, 7)

    def test_get_instrument_names(self):
        """Given a CTD dataframe and a list of columns to exclude, acquire instrument names"""

        # Note: PrDM is a special case. it's the pressure measurement and we use it in another way
        excluded = ['Bottle', 'Bottle_', 'Date', 'Statistic', 'PrDM', 'Latitude', 'Longitude']
        expected_names = ["Sbeox0ML/L", "Sbeox1ML/L", "Sal00", "Sal11", "Potemp068C", "Potemp168C", "Sigma-é00",
                          "Sigma-é11", "Scan", "TimeS", "T068C", "C0S/m", "T168C", "C1S/m", "AltM", "Par/log",
                          "Sbeox0V", "Sbeox1V", "FlSPuv0", "FlSP", "Ph", "TurbWETbb0", "Spar"]

        instrument_names = ctd_parser.get_sensor_names(self.dataframe, excluded)

        for name in expected_names:
            if name not in instrument_names:
                self.fail(f"Expected instrument '{name}' was not found in the resulting array")

    def test_parse_sensors(self):
        """Given a sensor string parse_sensors should return a list [sensor_type, priority, units, additional]"""
        sensor = {"sensor": "Time, Elapsed [seconds]", "expected": ("Time", 1, "seconds", "Elapsed")}
        self.assertTupleEqual(ctd_parser.parse_sensor(sensor['sensor']), sensor['expected'])

        sensor = {"sensor": "Pressure, Digiquartz [db]", "expected": ("Pressure", 1, "db", "Digiquartz")}
        self.assertTupleEqual(ctd_parser.parse_sensor(sensor['sensor']), sensor['expected'])

        sensor = {"sensor": "Temperature [IPTS-68, deg C]", "expected": ("Temperature", 1, "IPTS-68, deg C", "")}
        self.assertTupleEqual(ctd_parser.parse_sensor(sensor['sensor']), sensor['expected'])

        sensor = {"sensor": "Conductivity [S/m]", "expected": ("Conductivity", 1, "S/m", "")}
        self.assertTupleEqual(ctd_parser.parse_sensor(sensor['sensor']), sensor['expected'])

        sensor = {"sensor": "Temperature, 2 [IPTS-68, deg C]", "expected": ("Temperature", 2, "IPTS-68, deg C", "")}
        self.assertTupleEqual(ctd_parser.parse_sensor(sensor['sensor']), sensor['expected'])

        sensor = {"sensor": "Conductivity, 2 [S/m]", "expected": ("Conductivity", 2, "S/m", "")}
        self.assertTupleEqual(ctd_parser.parse_sensor(sensor['sensor']), sensor['expected'])

        sensor = {"sensor": "Altimeter [m]", "expected": ("Altimeter", 1, "m", "")}
        self.assertTupleEqual(ctd_parser.parse_sensor(sensor['sensor']), sensor['expected'])

        sensor = {"sensor": "PAR/Logarithmic, Satlantic [umol photons/m2/s]",
                  "expected": ("PAR/Logarithmic", 1, "umol photons/m2/s", "Satlantic")}
        self.assertTupleEqual(ctd_parser.parse_sensor(sensor['sensor']), sensor['expected'])

        sensor = {"sensor": "Oxygen raw, SBE 43 [V]", "expected": ("Oxygen", 1, "V", "SBE 43")}
        self.assertTupleEqual(ctd_parser.parse_sensor(sensor['sensor']), sensor['expected'])

        sensor = {"sensor": "Oxygen raw, SBE 43, 2 [V]", "expected": ("Oxygen", 2, "V", "SBE 43")}
        self.assertTupleEqual(ctd_parser.parse_sensor(sensor['sensor']), sensor['expected'])

        sensor = {"sensor": "Fluorescence, Seapoint Ultraviolet",
                  "expected": ("Fluorescence", 1, "", "Seapoint Ultraviolet")}
        self.assertTupleEqual(ctd_parser.parse_sensor(sensor['sensor']), sensor['expected'])

        sensor = {"sensor": "Fluorescence, Seapoint", "expected": ("Fluorescence", 1, "", "Seapoint")}
        self.assertTupleEqual(ctd_parser.parse_sensor(sensor['sensor']), sensor['expected'])

        sensor = {"sensor": "pH", "expected": ("pH", 1, "", "")}
        self.assertTupleEqual(ctd_parser.parse_sensor(sensor['sensor']), sensor['expected'])

        sensor = {"sensor": "Turbidity, WET Labs ECO BB [m^-1/sr]",
                  "expected": ("Turbidity", 1, "m^-1/sr", "WET Labs ECO BB")}
        self.assertTupleEqual(ctd_parser.parse_sensor(sensor['sensor']), sensor['expected'])

        sensor = {"sensor": "SPAR/Surface Irradiance", "expected": ("SPAR/Surface Irradiance", 1, "", "")}
        self.assertTupleEqual(ctd_parser.parse_sensor(sensor['sensor']), sensor['expected'])

        sensor = {"sensor": "Latitude [deg]", "expected": ("Latitude", 1, "deg", "")}
        self.assertTupleEqual(ctd_parser.parse_sensor(sensor['sensor']), sensor['expected'])

        sensor = {"sensor": "Longitude [deg]", "expected": ("Longitude", 1, "deg", "")}
        self.assertTupleEqual(ctd_parser.parse_sensor(sensor['sensor']), sensor['expected'])

    def test_get_ros_file(self):
        data_file_directory = core_factory.DataFileDirectoryFactory(directory=self.sample_directory)
        datafile = core_factory.DataFileFactory(directory=data_file_directory, file=self.sample_file_name,
                                                file_type=models.FileType.btl)

        ros_file = ctd_parser.get_ros_file(datafile)
        exclude_sensors = ['scan', 'timeS', 'latitude', 'longitude', 'nbf', 'flag']

        new_sensors = ctd_parser.get_new_sensors_from_ros_data(mission=self.mission, exclude_sensors=exclude_sensors,
                                                               ros_file=ros_file)
        self.assertEquals(len(new_sensors), 14)

        # column_names should all be capitalized
        for sensor in new_sensors:
            self.assertTrue(re.match("^[A-Z]", sensor.column_name), "Column names must be in initial caps")

    def test_get_new_sensors_from_sensor_name(self):
        sensor_names = ["Sbeox0ML/L", "Sbeox1ML/L", "Sal00", "Sal11", "Potemp090C", "Potemp190C", "Sigma-é00",
                        "Sigma-é11", "Scan", "TimeS"]

        new_sensors = ctd_parser.get_new_sensors_from_sensor_name(mission=self.mission, sensors=sensor_names)

        self.assertEquals(len(new_sensors), 10)

    def test_update_bottle(self):
        bottle = core_factory.BottleFactory()
        expected_bottle_id = 777777
        expected_date_time = datetime.datetime.now()
        expected_pressure = 6
        update_fields = {
            "bottle_id": expected_bottle_id,
            "date_time": expected_date_time,
            "pressure": expected_pressure
        }

        fields = ctd_parser.update_bottle(bottle, update_fields)
        self.assertIn("bottle_id", fields)
        self.assertIn("date_time", fields)
        self.assertIn("pressure", fields)

        self.assertEquals(bottle.bottle_id, expected_bottle_id)
        self.assertEquals(bottle.date_time, expected_date_time)
        self.assertEquals(bottle.pressure, expected_pressure)

    def test_process_bottles(self):
        event_id = ctd_parser.get_event_number(self.dataframe)
        event = core_factory.CTDEventFactory(event_id=event_id)

        bottles = event.bottles.all()
        self.assertEquals(len(bottles), 0)

        ctd_parser.process_bottles(file_name=self.sample_file_name, data_frame=self.dataframe, event=event)

        bottles = event.bottles.all()
        self.assertGreater(len(bottles), 0)

        bottle = bottles[0]
        expected_bad_date = datetime.datetime.now()
        bottle_number = bottle.bottle_number

        bottle.date_time = expected_bad_date
        bottle.bottle_id = 7777
        bottle.pressure = 0
        bottle.save()

        ctd_parser.process_bottles(file_name=self.sample_file_name, data_frame=self.dataframe, event=event)

        updated_bottle = event.bottles.get(bottle_number=bottle_number)
        self.assertNotEqual(updated_bottle.bottle_id, 7777)
        self.assertNotEqual(updated_bottle.date_time, expected_bad_date)
        self.assertNotEqual(updated_bottle.pressure, 0)

