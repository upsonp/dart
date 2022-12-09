import re

import numpy
import django.utils.timezone

from django.db import models
from django.dispatch import receiver

from os.path import join


class ErrorType(models.IntegerChoices):
    unknown = 0, "Unknown"
    missing_id = 1, "Missing Sample ID"
    bad_id = 2, "Bad Sample ID"
    missing_information = 3, "Missing Information"
    duplicate_value = 4, "Duplicate Value"


class ActionType(models.IntegerChoices):
    # make sure new option names are in lowercase with underscores instead of spaces
    # Labels, in quotations marks, can be uppercase with spaces
    deployed = 1, "Deployed"
    bottom = 2, "Bottom"
    recovered = 3, "Recovered"
    aborted = 4, "Aborted"
    attempt_comms = 5, "Attempted Comms"
    release = 6, "Release"
    on_deck = 7, "On Deck"
    in_water = 8, "In Water"
    start_deployment = 9, "Start Deployment"
    on_bottom = 10, "On Bottom"

    other = 999, "Other"


class InstrumentType(models.IntegerChoices):
    ctd = 1, "CTD"
    ringnet = 2, "RingNet"
    mooring = 3, "Mooring"
    viking_buoy = 4, "Viking Buoy"
    vpr = 5, "VPR"

    other = 999, "Other"


class FileType(models.IntegerChoices):
    log = 1, ".LOG"
    btl = 2, ".BTL"


class SensorType(models.IntegerChoices):
    unknown = 0, "Unknown"
    pressure = 1, "Pressure"
    temperature = 2, "Temperature"
    salinity = 3, "Salinity"
    oxygen = 4, "Oxygen"
    sigma = 5, "Sigma-é"
    time = 6, "Time"
    conductivity = 7, "Conductivity"
    ph = 8, "Ph"
    fluorescence = 9, 'Fluorescence'
    turw = 10, 'CStarAt'
    alt = 11, 'Altimeter'
    par = 12, 'Par'
    other = 99, "other"


# we're going to make or best guess on what the sensor type is based on names me know.
# in the future as we build up a repo of sensors this will be unnecessary
def get_sensor_type(sensor_name):
    name = sensor_name.lower().replace("-", "_")
    if name == 'prdm':
        return SensorType.pressure.value
    elif name == "sbeox":
        return SensorType.oxygen.value
    elif name == "sal":
        return SensorType.salinity.value
    elif name == "potemp":
        return SensorType.temperature.value
    elif name == "sigma_é":
        return SensorType.sigma.value
    elif name == "scan":
        return SensorType.other.value
    elif name == "times":
        return SensorType.time.value
    elif name == "t":
        return SensorType.temperature.value
    elif name == "c":
        return SensorType.conductivity.value
    elif name == "ph":
        return SensorType.time.value
    elif name == "fleco_afl":
        return SensorType.fluorescence.value
    elif name == "cstartat":
        return SensorType.turw.value
    elif name == "altm":
        return SensorType.alt.value
    elif name == "par/log":
        return SensorType.par.value
    elif name == "wetcdom":
        return SensorType.fluorescence.value
    else:
        return SensorType.unknown.value


def __get_lookup__(model, name):
    obj = model.objects.get(name=name) if len(model.objects.filter(name=name)) > 0 else None

    if not obj:
        obj = model(name=name)
        obj.save()

    return obj


def get_variable_name(name):
    return __get_lookup__(VariableName, name)


def get_station(name):
    return __get_lookup__(Station, name)


def get_instrument(instrument_name):
    try:
        inst_type = InstrumentType[instrument_name.lower()].value
    except KeyError:
        # if an unknown type is recieved consider this an 'other' event
        inst_type = InstrumentType['other'].value

    instr = Instrument.objects.filter(name=instrument_name, instrument_type=inst_type)
    if not instr:
        instr = Instrument(name=instrument_name, instrument_type=inst_type)
        instr.save()
    else:
        instr = instr[0]

    return instr


def get_sensor_name(name):
    sensor_vars = re.split("(\d)", name, 1)
    sensor = Sensor.objects.filter(name=sensor_vars[0])
    if len(sensor_vars) > 1:
        sensor = sensor.filter(priority=(int(sensor_vars[1])+1))

    if len(sensor_vars) > 2 and sensor_vars[2] != "":
        sensor = sensor.filter(units=sensor_vars[2].lower())

    return sensor[0]


# Used to track a list of reusable names, should be extended to create separated tables
class SimpleLookupName(models.Model):
    name = models.CharField(verbose_name="Field Name", max_length=50, unique=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


class Mission(models.Model):
    name = models.CharField(verbose_name="Mission Name", max_length=30)


class DataFileDirectory(models.Model):
    mission = models.ForeignKey(Mission, verbose_name="Mission", related_name="mission_directories",
                                on_delete=models.CASCADE)
    directory = models.FilePathField(verbose_name="File Directory", allow_folders=True, allow_files=False)


class DataFileDirectoryType(models.Model):
    directory = models.ForeignKey(DataFileDirectory, verbose_name="Directory", related_name="file_types",
                                  on_delete=models.CASCADE)
    file_type = models.IntegerField(verbose_name="File Types", choices=FileType.choices)


class DataFile(models.Model):
    directory = models.ForeignKey(DataFileDirectory, verbose_name="Directoy", related_name="data_files",
                                  on_delete=models.CASCADE)
    file = models.FileField(verbose_name="File")
    file_type = models.IntegerField(verbose_name="File Type", choices=FileType.choices)
    processed = models.BooleanField(verbose_name="Processed", default=False)

    @property
    def file_path(self):
        return join(self.directory.directory, self.file.name)


class Error(models.Model):
    mission = models.ForeignKey(Mission, verbose_name="mission", related_name="mission_errors",
                                on_delete=models.CASCADE)
    file = models.ForeignKey(DataFile, verbose_name="Log File", blank=True, null=True, related_name="log_errors",
                             on_delete=models.CASCADE)
    file_name = models.TextField(verbose_name="file", max_length=50)

    error_code = models.IntegerField(verbose_name="Error Code", default=0, choices=ErrorType.choices)
    message = models.CharField(verbose_name="Message", max_length=255)
    stack_trace = models.TextField(verbose_name="Stack Trace")
    line = models.IntegerField(verbose_name="Line/Object #")


@receiver(models.signals.pre_save, sender=Error)
def auto_set_file_name(sender, instance, **kwargs):
    if not instance.file:
        return False

    instance.file_name = instance.file.file


class Station(SimpleLookupName):
    pass


class Instrument(models.Model):
    name = models.CharField(verbose_name="Instrument Name", max_length=50)
    instrument_type = models.IntegerField(verbose_name="Instrument Type", choices=InstrumentType.choices)


class Event(models.Model):
    event_id = models.IntegerField(verbose_name="Event ID")

    mission = models.ForeignKey(Mission, verbose_name="Mission", related_name="events", on_delete=models.CASCADE)
    station = models.ForeignKey(Station, verbose_name="Station", related_name="events", on_delete=models.CASCADE)

    instrument = models.ForeignKey(Instrument, verbose_name="Instrument", on_delete=models.DO_NOTHING)

    sample_id = models.IntegerField(verbose_name="Sample ID", null=True, blank=True)
    end_sample_id = models.IntegerField(verbose_name="End Sample ID", null=True, blank=True)

    @property
    def start_location(self):
        action = self.actions.all().order_by("date_time")[0]
        return [action.latitude, action.longitude]

    @property
    def end_location(self):
        action = self.actions.all().order_by("-date_time")[0]
        return [action.latitude, action.longitude]

    @property
    def start_date(self):
        action = self.actions.all().order_by("date_time")[0]
        return action.date_time

    @property
    def end_date(self):
        action = self.actions.all().order_by("-date_time")[0]
        return action.date_time

    class Meta:
        unique_together = ("event_id", "mission")
        ordering = ("event_id",)

    def __str__(self):
        return f"{self.event_id} - {self.station.name}"


# In reality a sensor is physically attached to an instrument, but depending on a station's depth a sensor might be
# removed. The Ph sensor for example is only rated to 1,200m, if a station is deeper than that the Ph sensor has to be
# removed. In which case it makes more 'database' sense to attache the sensor to an event.
class InstrumentSensor(models.Model):
    event = models.ForeignKey(Event, verbose_name="Event", related_name="attachments", on_delete=models.CASCADE)
    name = models.CharField(verbose_name="Attachment Name", max_length=50)


class Action(models.Model):
    event = models.ForeignKey(Event, verbose_name="Event", related_name="actions", on_delete=models.CASCADE)

    date_time = models.DateTimeField(verbose_name="Date/Time")
    latitude = models.FloatField(verbose_name="Latitude")
    longitude = models.FloatField(verbose_name="Longitude")

    # The file this action was loaded from. Events can span different fields
    file = models.ForeignKey(DataFile, verbose_name="File", related_name="actions", on_delete=models.DO_NOTHING)

    # mid helps us track issues
    mid = models.IntegerField(verbose_name="$@MID@$")
    action_type = models.IntegerField(verbose_name="Action Type", choices=ActionType.choices)
    # if the action is an unknown type then leave a comment here identifying what the 'other' type is
    action_type_other = models.CharField(verbose_name="Action Other", max_length=50, blank=True, null=True)

    comment = models.CharField(verbose_name="Comment", max_length=255, blank=True, null=True)


# A variable field has a variable name because variable names can be reused. Instead of having 50 variable fields
# with the name 'Flowmeter Start' taking up DB space we have one Variable Name 'Flowmeter Start' referenced
# 50 times in the VariableField. Integers take up less space than strings. SimpleLookupName can also be used
# later on to add bilingual support
class VariableName(SimpleLookupName):
    pass


class VariableField(models.Model):
    action = models.ForeignKey(Action, verbose_name="Action", related_name="action_variables", on_delete=models.CASCADE)
    name = models.ForeignKey(VariableName, verbose_name="Field Name", related_name="action_variables",
                             on_delete=models.CASCADE)
    value = models.CharField(verbose_name="Field Value", max_length=255)


class Bottle(models.Model):
    event = models.ForeignKey(Event, verbose_name="Event", related_name="bottles", on_delete=models.CASCADE)
    date_time = models.DateTimeField(verbose_name="Fired Date/Time")

    # the bottle number is its order from 1 to N in a series of bottles as opposed tot he bottle ID which is the
    # label placed on the bottle linking it to all samples that come from that bottle.
    bottle_id = models.IntegerField(verbose_name="Bottle ID")
    bottle_number = models.IntegerField(verbose_name="Bottle Number")

    pressure = models.FloatField(verbose_name="Pressure", default=0.0)

    def get_sensor_data_by_name(self, sensor_name, sensor_type, priority=1):
        return self.bottle_data.get(
            sensor__name__iexact=sensor_name,
            sensor__sensor_type=sensor_type,
            sensor__priority=priority)

    def get_sensor_data_by_unit(self, unit, sensor_type, priority=1):
        return self.bottle_data.get(
            sensor__units__iexact=unit,
            sensor__sensor_type=sensor_type,
            sensor__priority=priority)


class Sensor(models.Model):
    name = models.TextField(verbose_name="Sensor Name")
    sensor_type = models.IntegerField(verbose_name="Sensor Type", choices=SensorType.choices,
                                      default=SensorType.unknown.value)
    priority = models.IntegerField(verbose_name="Priority", default=1,
                                   help_text="1 = primary sensor, 2 = secondary sensor, 3 = tertiary, etc.")
    units = models.CharField(verbose_name="Units", blank=True, null=True, max_length=10)

    def __str__(self):
        return self.name + (f'({self.units})' if self.units else "")

    class Meta:
        unique_together = ['name', 'priority', 'units']


class CTDData(models.Model):
    bottle = models.ForeignKey(Bottle, verbose_name="Bottle", related_name="bottle_data", on_delete=models.CASCADE)
    sensor = models.ForeignKey(Sensor, verbose_name="Column Heading", related_name="bottle_data",
                               on_delete=models.DO_NOTHING)
    value = models.FloatField(verbose_name="Value")


class Sample(models.Model):
    class Meta:
        abstract = True

    file = models.FileField(verbose_name="File")


class OxygenSample(Sample):
    bottle = models.ForeignKey(Bottle, verbose_name="Bottle", related_name="oxygen_data", on_delete=models.CASCADE)
    winkler_1 = models.FloatField(verbose_name="Winkler 1")
    winkler_2 = models.FloatField(verbose_name="Winkler 2", blank=True, null=True)

    @property
    def average(self):
        winks = []
        if self.winkler_1:
            winks.append(self.winkler_1)

        if self.winkler_2:
            winks.append(self.winkler_2)

        return numpy.average(winks)


class SaltSample(Sample):
    bottle = models.ForeignKey(Bottle, verbose_name="Bottle", related_name="salt_data", on_delete=models.CASCADE)
    sample_date = models.DateTimeField(verbose_name="Sample Date", default=django.utils.timezone.now)
    sample_id = models.CharField(verbose_name="Sample ID", default="", max_length=50)
    calculated_salinity = models.FloatField(verbose_name="Calculated Salinity")
    comments = models.TextField(verbose_name="Comments", blank=True, null=True)


class ChlSample(Sample):
    bottle = models.ForeignKey(Bottle, verbose_name="Bottle", related_name="chl_data", on_delete=models.CASCADE)
    sample_order = models.IntegerField(verbose_name="Sample Order")
    chl = models.FloatField(verbose_name="CHL")
    phae = models.FloatField(verbose_name="PHAE")

    class Meta:
        unique_together = ['bottle', 'sample_order']

    @property
    def mean_chl(self):
        return numpy.average([c.chl for c in self.bottle.chl_data.all()])

    @property
    def mean_phae(self):
        return numpy.average([c.phae for c in self.bottle.chl_data.all()])

