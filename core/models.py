import numpy
import django.utils.timezone

from django.db import models
from django.dispatch import receiver

from os.path import join


class ErrorType(models.IntegerChoices):
    unknown = 0, "Unknown"
    missing_id = 1, "Mission Sample ID"


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


def get_data_column_name(name):
    return __get_lookup__(DataColumn, name)


# Used to track a list of reusable names, should be extended to create separated tables
class SimpleLookupName(models.Model):
    name = models.CharField(verbose_name="Field Name", max_length=50, unique=True)

    class Meta:
        abstract = True


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
    processed = models.BooleanField(verbose_name="Processed", default=True)

    @property
    def file_path(self):
        return join(self.directory.directory, self.file.name)


class Error(models.Model):

    error_code = models.IntegerField(verbose_name="Error Code", default=0, choices=ErrorType.choices)
    message = models.CharField(verbose_name="Message", max_length=255)
    stack_trace = models.TextField(verbose_name="Stack Trace")


class LogError(models.Model):
    error = models.OneToOneField(Error, verbose_name="Error", on_delete=models.CASCADE)
    file_name = models.CharField(verbose_name="File Name", max_length=50)


class LogFileError(models.Model):
    error_code = models.OneToOneField(Error, verbose_name="Error", on_delete=models.CASCADE)
    file = models.ForeignKey(DataFile, verbose_name="Log File", related_name="log_errors", on_delete=models.CASCADE)
    line = models.IntegerField(verbose_name="Line #")


@receiver(models.signals.pre_save, sender=LogFileError)
def auto_set_file_name(sender, instance, **kwargs):
    if not instance.pk:
        return False

    instance.file_name = instance.file.file


class Station(SimpleLookupName):
    pass


class Event(models.Model):
    event_id = models.IntegerField(verbose_name="Event ID")

    mission = models.ForeignKey(Mission, verbose_name="Mission", related_name="events", on_delete=models.CASCADE)
    station = models.ForeignKey(Station, verbose_name="Station", related_name="events", on_delete=models.CASCADE)

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


class Instrument(models.Model):
    event = models.OneToOneField(Event, verbose_name="Event", related_name="instrument", on_delete=models.CASCADE)
    name = models.CharField(verbose_name="Instrument Name", max_length=50)
    instrument_type = models.IntegerField(verbose_name="Instrument Type", choices=InstrumentType.choices)


class Attachments(models.Model):
    instrument = models.ForeignKey(Instrument, verbose_name="Instrument", related_name="attachments",
                                   on_delete=models.CASCADE)
    name = models.CharField(verbose_name="Attachment Name", max_length=50)


class Action(models.Model):
    event = models.ForeignKey(Event, verbose_name="Event", related_name="actions", on_delete=models.CASCADE)

    date_time = models.DateTimeField(verbose_name="Date/Time")
    latitude = models.FloatField(verbose_name="Latitude")
    longitude = models.FloatField(verbose_name="Longitude")

    # The file this action was loaded from. Events can span different fields
    file = models.ForeignKey(DataFile, verbose_name="File", related_name="actions", on_delete=models.CASCADE)

    # mid helps us track issues
    mid = models.IntegerField(verbose_name="$@MID@$")
    action_type = models.IntegerField(verbose_name="Event Type", choices=ActionType.choices)

    comment = models.CharField(verbose_name="Comment", max_length=255, blank=True, null=True)


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


class DataColumn(SimpleLookupName):
    label = models.CharField(verbose_name="Column Label", max_length=30)

    def save(self, *args, **kwargs):
        if not self.label or self.label.strip() == "":
            self.label = self.name

        super().save(*args, **kwargs)


class BottleData(models.Model):
    bottle = models.ForeignKey(Bottle, verbose_name="Bottle", related_name="bottle_data", on_delete=models.CASCADE)
    column = models.ForeignKey(DataColumn, verbose_name="Column Heading", related_name="bottle_data",
                               on_delete=models.DO_NOTHING)
    value = models.FloatField(verbose_name="Value")


class OxygenSample(models.Model):
    bottle = models.ForeignKey(Bottle, verbose_name="Bottle", related_name="oxygen_data", on_delete=models.CASCADE)
    winkler_1 = models.FloatField(verbose_name="Winkler 1")
    winkler_2 = models.FloatField(verbose_name="Winkler 2", blank=True, null=True)


class SaltSample(models.Model):
    bottle = models.ForeignKey(Bottle, verbose_name="Bottle", related_name="salt_data", on_delete=models.CASCADE)
    sample_date = models.DateTimeField(verbose_name="Sample Date", default=django.utils.timezone.now())
    sample_id = models.CharField(verbose_name="Sample ID", default="", max_length=50)
    calculated_salinity = models.FloatField(verbose_name="Calculated Salinity")
    comments = models.TextField(verbose_name="Comments", blank=True, null=True)


class ChlSample(models.Model):
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

