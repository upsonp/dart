from datetime import datetime

from .. import models

from rest_framework import serializers


def get_bottle_id(bottle):
    return bottle.bottle_id


class InstrumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Instrument
        fields = '__all__'


class ActionVariableSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField("get_field_name")

    class Meta:
        model = models.VariableField
        fields = ('name', 'value')

    def get_field_name(self, obj):
        return obj.name.name


class ActionSerializer(serializers.ModelSerializer):
    action_variables = ActionVariableSerializer(many=True, read_only=True)
    action_type = serializers.SerializerMethodField("get_action_type")
    date_time = serializers.SerializerMethodField("get_date_time")
    date = serializers.SerializerMethodField("get_date")
    time = serializers.SerializerMethodField("get_time")

    class Meta:
        model = models.Action
        fields = '__all__'

    def get_action_type(self, obj):
        at = models.ActionType(obj.action_type)
        return {"id": at.value, "name": at.label}

    def get_date_time(self, obj):
        return datetime.strftime(obj.date_time, "%Y/%m/%d %H:%M:%S")

    def get_date(self, obj):
        return datetime.strftime(obj.date_time, "%Y/%m/%d")

    def get_time(self, obj):
        return datetime.strftime(obj.date_time, "%H:%M:%S")


class ActionSummarySerializer(serializers.ModelSerializer):
    file = serializers.SerializerMethodField("get_log_file_name")

    class Meta:
        model = models.Action
        fields = '__all__'

    def get_log_file_name(self, obj):
        return {"id": obj.file.id, "name": obj.file.file.name}


class StationSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Station
        fields = '__all__'


class EventSerializer(serializers.ModelSerializer):
    instrument = InstrumentSerializer(many=False, read_only=True)
    attachments = serializers.SerializerMethodField()
    actions = ActionSummarySerializer(many=True, read_only=True)
    station = serializers.SerializerMethodField("get_station_name")
    has_data = serializers.SerializerMethodField("get_has_data")

    class Meta:
        model = models.Event
        fields = '__all__'

    def get_station_name(self, obj):
        return {"id": obj.station.id, "name": obj.station.name}

    def get_has_data(self, obj):
        return len(models.Bottle.objects.filter(event=obj)) > 0

    def get_attachments(self, obj):
        return [{'id': a.pk, 'name': a.name} for a in obj.attachments.all()]


class MissionReportSerializer(serializers.ModelSerializer):
    events = EventSerializer(many=True, read_only=True)

    class Meta:
        model = models.Mission
        fields = '__all__'


class CTDData(serializers.ModelSerializer):
    values = serializers.SerializerMethodField()

    class Meta:
        model = models.CTDData
        fields = ['values']

    def get_values(self, instance):
        pass


class ErrorSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Error
        fields = '__all__'


class MissionErrorSerializer(serializers.ModelSerializer):
    mission_errors = ErrorSerializer(many=True, read_only=True)

    class Meta:
        model = models.Mission
        fields = ['id', 'name', 'mission_errors']


class BottleReport(serializers.ModelSerializer):
    Name = serializers.SerializerMethodField(method_name='get_name')
    Station = serializers.SerializerMethodField(method_name='get_station')
    Event = serializers.SerializerMethodField(method_name='get_event')
    Sample = serializers.SerializerMethodField(method_name='get_sample')
    Pressure = serializers.SerializerMethodField(method_name='get_pressure')

    class Meta:
        model = models.Bottle
        fields = ['Name', 'Station', 'Event', 'Sample', 'Pressure']

    def get_name(self, instance):
        return instance.event.mission.name

    def get_station(self, instance):
        return instance.event.station.name

    def get_event(self, instance):
        return instance.event.event_id

    def get_sample(self, instance):
        return instance.bottle_id

    def get_pressure(self, instance):
        return instance.pressure


class CTDReportSerializer(serializers.ModelSerializer):
    __headers = None
    __bottles = None

    headers = serializers.SerializerMethodField()
    bottles = serializers.SerializerMethodField()

    class Meta:
        model = models.Mission
        fields = ['headers', 'bottles']

    def get_headers(self, instance):
        self.__headers = models.Sensor.objects.filter(bottle_data__bottle__event__mission=instance).distinct()
        return [{"header": (h.name + (f"({h.units})" if h.units else "")), "data":
                [d.value for d in h.bottle_data.all().order_by("bottle__event__station_id")]}
                for h in self.__headers]

    def get_bottles(self, instance):
        self.__bottles = models.Bottle.objects.filter(event__mission=instance).order_by("event__station_id").distinct()
        return [BottleReport(b).data for b in self.__bottles]


class SampleReportSerializer(BottleReport):
    temp_ctd_p = serializers.SerializerMethodField(method_name="get_temp_ctd_p")
    temp_ctd_s = serializers.SerializerMethodField(method_name="get_temp_ctd_s")
    cond_ctd_p = serializers.SerializerMethodField(method_name="get_cond_ctd_p")
    cond_ctd_s = serializers.SerializerMethodField(method_name="get_cond_ctd_s")
    sal_ctd_p = serializers.SerializerMethodField(method_name="get_sal_ctd_p")
    sal_ctd_s = serializers.SerializerMethodField(method_name="get_sal_ctd_s")
    oxy_ctd_p = serializers.SerializerMethodField(method_name="get_oxy_ctd_p")
    oxy_ctd_s = serializers.SerializerMethodField(method_name="get_oxy_ctd_s")

    def get_name(self, instance):
        return super().get_name(instance.bottle)

    def get_station(self, instance):
        return super().get_station(instance.bottle)

    def get_event(self, instance):
        return super().get_event(instance.bottle)

    def get_sample(self, instance):
        return super().get_sample(instance.bottle)

    def get_pressure(self, instance):
        return super().get_pressure(instance.bottle)

    def get_temp_ctd_p(self, instance):
        return instance.bottle.get_sensor_data_by_name('t', models.SensorType.temperature, priority=1).value

    def get_temp_ctd_s(self, instance):
        return instance.bottle.get_sensor_data_by_name('t', models.SensorType.temperature, priority=2).value

    def get_cond_ctd_p(self, instance):
        return instance.bottle.get_sensor_data_by_name('c', models.SensorType.conductivity, priority=1).value

    def get_cond_ctd_s(self, instance):
        return instance.bottle.get_sensor_data_by_name('c', models.SensorType.conductivity, priority=2).value

    def get_sal_ctd_p(self, instance):
        return instance.bottle.get_sensor_data_by_name('sal', models.SensorType.salinity, priority=1).value

    def get_sal_ctd_s(self, instance):
        return instance.bottle.get_sensor_data_by_name('sal', models.SensorType.salinity, priority=2).value

    def get_oxy_ctd_p(self, instance):
        return instance.bottle.get_sensor_data_by_unit('v', models.SensorType.oxygen, priority=1).value

    def get_oxy_ctd_s(self, instance):
        return instance.bottle.get_sensor_data_by_unit('v', models.SensorType.oxygen, priority=2).value


class SaltSerializer(serializers.ModelSerializer):
    Calculated = serializers.SerializerMethodField(method_name="get_salinity")
    Sample_Date = serializers.SerializerMethodField(method_name="get_sample_date")
    Comments = serializers.SerializerMethodField(method_name="get_comments")

    class Meta:
        model = models.SaltSample
        fields = ['Sample_Date', 'Calculated', 'Comments']

    def get_salinity(self, instance):
        return instance.calculated_salinity

    def get_sample_date(self, instance):
        return instance.sample_date

    def get_comments(self, instance):
        return instance.comments


class SaltReport(SampleReportSerializer, SaltSerializer):
    class Meta:
        model = models.SaltSample
        fields = ['Name', 'Station', 'Event', 'Sample', 'Pressure', 'temp_ctd_p', 'temp_ctd_s',
                  'cond_ctd_p', 'cond_ctd_s', 'sal_ctd_p', 'sal_ctd_s', 'Sample_Date', 'Calculated', 'Comments']


class OxygenSerializer(serializers.ModelSerializer):
    oxy_w_rep1 = serializers.SerializerMethodField(method_name='get_oxy_w_rep1')
    oxy_w_rep2 = serializers.SerializerMethodField(method_name='get_oxy_w_rep2')

    class Meta:
        model = models.OxygenSample
        fields = ['oxy_w_rep1', 'oxy_w_rep2']

    def get_oxy_w_rep1(self, instance):
        return instance.winkler_1

    def get_oxy_w_rep2(self, instance):
        return instance.winkler_2


class OxygenReport(SampleReportSerializer, OxygenSerializer):
    class Meta:
        model = models.OxygenSample
        fields = ['Name', 'Station', 'Event', 'Sample', 'Pressure', 'oxy_ctd_p', 'oxy_ctd_s', 'oxy_w_rep1',
                  'oxy_w_rep2']


class ChlSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ChlSample
        fields = ['sample_order', 'chl', 'phae', 'mean_chl', 'mean_phae']


class ChlReport(SampleReportSerializer, ChlSerializer):
    class Meta:
        model = models.ChlSample
        fields = ['Name', 'Station', 'Event', 'Sample', 'Pressure', 'sample_order', 'chl', 'phae', 'mean_chl',
                  'mean_phae']


class FullReport(BottleReport):
    oxygen_data = OxygenSerializer(many=True, read_only=True)
    salt_data = SaltSerializer(many=True, read_only=True)
    chl_data = ChlSerializer(many=True, read_only=True)

    class Meta:
        model = models.Bottle
        fields = ['Name', 'Station', 'Event', 'Sample', 'Pressure', 'oxygen_data', 'salt_data', 'chl_data']
