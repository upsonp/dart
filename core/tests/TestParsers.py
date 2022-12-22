from django.test import TestCase, tag

from core import models
from . import CoreFactoryFloor as core_factory

import io
import ctd

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

        chn_obj = self.model.objects.filter(bottle=bottle)
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

    model = models.ChlSample
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

        chl_obj = self.model.objects.filter(bottle=bottle)
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

    model = models.OxygenSample
    sample_file = r'core/tests/sample_data/Oxygen_sample.xlsx'
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

        df = parser_utils.get_dataframe(self.file_pointer)
        samples = oxy.parse_dataframe(dataframe=df)

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

    model = models.SaltSample
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

        salt_obj = self.model.objects.filter(bottle=bottle)
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


@tag('parsers', 'parsers_hplc')
class TestHPLCParser(TestCase):
    model = models.HplcSample
    sample_file = r'core/tests/sample_data/HPLC_sample.xlsx'
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

        df = parser_utils.get_dataframe(self.file_pointer)
        samples = hplc.parse_dataframe(dataframe=df)

        self.assertGreater(len(samples), 0)

    def test_get_dataframe(self):
        df = parser_utils.get_dataframe(self.file_pointer)
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
    sample_file = '185A007.BTL'
    sample_file_path = sample_directory + sample_file
    mission = None
    dataframe = None

    def setUp(self):
        self.mission = core_factory.MissionFactory()
        self.dataframe = ctd.from_btl(self.sample_file_path)

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

        sensor = {"sensor": "Oxygen raw, SBE 43 [V]", "expected": ("Oxygen raw", 1, "V", "SBE 43")}
        self.assertTupleEqual(ctd_parser.parse_sensor(sensor['sensor']), sensor['expected'])

        sensor = {"sensor": "Oxygen raw, SBE 43, 2 [V]", "expected": ("Oxygen raw", 2, "V", "SBE 43")}
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
        datafile = core_factory.DataFileFactory(directory=data_file_directory, file=self.sample_file,
                                                file_type=models.FileType.btl)

        ros_file = ctd_parser.get_ros_file(datafile)
        exclude_sensors = ['scan', 'timeS', 'latitude', 'longitude', 'nbf', 'flag']

        new_sensors = ctd_parser.create_sensors_from_ros_data(mission=self.mission, exclude_sensors=exclude_sensors,
                                                              ros_file=ros_file)
        self.assertEquals(len(new_sensors), 14)

        models.MissionSensor.objects.bulk_create(new_sensors)

    def ntest_get_sensor_details(self):
        """Given a string get_sensor_details should return a sensor type, priority and unit of measurement"""

        ctd.rosette_summary()
        sensor_details = ctd_parser.get_sensor_details('C0S/m')
        self.assertEquals(sensor_details[0], models.SensorType.conductivity)
        self.assertEquals(sensor_details[1], 1)
        self.assertEquals(sensor_details[2], "S/m")

        sensor_details = ctd_parser.get_sensor_details('T168C')
        self.assertEquals(sensor_details[0], models.SensorType.temperature)
        self.assertEquals(sensor_details[1], 2)
        self.assertEquals(sensor_details[2], "68C")

        sensor_details = ctd_parser.get_sensor_details('AltM')
        self.assertEquals(sensor_details[0], models.SensorType.alt)
        self.assertEquals(sensor_details[1], 0)  # No priority is given for the altimeter
        self.assertEquals(sensor_details[2], "M")
