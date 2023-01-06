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


class SampleSerializer(serializers.ModelSerializer):
    Sample = serializers.SerializerMethodField(method_name='get_sample')
    Pressure = serializers.SerializerMethodField(method_name='get_pressure')

    class Meta:
        model = models.Bottle
        fields = ['Sample', 'Pressure']

    def get_sample(self, instance):
        if type(instance) is models.Bottle:
            return instance.bottle_id

        return self.get_sample(instance.bottle)

    def get_pressure(self, instance):
        if type(instance) is models.Bottle:
            return instance.pressure

        return self.get_pressure(instance.bottle)


class BottleReport(SampleSerializer):
    Name = serializers.SerializerMethodField(method_name='get_name')
    Station = serializers.SerializerMethodField(method_name='get_station')
    Event = serializers.SerializerMethodField(method_name='get_event')

    class Meta:
        model = models.Bottle
        fields = ['Name', 'Station', 'Event'] + SampleSerializer.Meta.fields

    def get_name(self, instance):
        if type(instance) is models.Bottle:
            return instance.event.mission.name

        return self.get_name(instance.bottle)

    def get_station(self, instance):
        if type(instance) is models.Bottle:
            return instance.event.station.name

        return self.get_station(instance.bottle)

    def get_event(self, instance):
        if type(instance) is models.Bottle:
            return instance.event.event_id

        return self.get_event(instance.bottle)


class CTDReportSerializer(serializers.ModelSerializer):
    __headers = None
    __bottles = None

    headers = serializers.SerializerMethodField()
    bottles = serializers.SerializerMethodField()

    class Meta:
        model = models.Mission
        fields = ['headers', 'bottles']

    def get_headers(self, instance):
        self.__headers = instance.sensors.all().distinct()
        return [{"header": (h.column_name + (f" ({h.sensor_details.units})" if h.sensor_details.units else "")), "data":
                [d.value for d in h.bottle_data.all().order_by("bottle__event__station_id")]}
                for h in self.__headers]

    def get_bottles(self, instance):
        self.__bottles = models.Bottle.objects.filter(event__mission=instance).order_by("event__station_id").distinct()
        return [BottleReport(b).data for b in self.__bottles]


class BottleReportSerializer(BottleReport):
    temp_ctd_p = serializers.SerializerMethodField(method_name="get_temp_ctd_p")
    temp_ctd_s = serializers.SerializerMethodField(method_name="get_temp_ctd_s")
    cond_ctd_p = serializers.SerializerMethodField(method_name="get_cond_ctd_p")
    cond_ctd_s = serializers.SerializerMethodField(method_name="get_cond_ctd_s")
    sal_ctd_p = serializers.SerializerMethodField(method_name="get_sal_ctd_p")
    sal_ctd_s = serializers.SerializerMethodField(method_name="get_sal_ctd_s")
    oxy_ctd_p = serializers.SerializerMethodField(method_name="get_oxy_ctd_p")
    oxy_ctd_s = serializers.SerializerMethodField(method_name="get_oxy_ctd_s")

    class Meta:
        model = models.Bottle
        fields = BottleReport.Meta.fields + ['temp_ctd_p', 'temp_ctd_s', 'cond_ctd_p','cond_ctd_s', 'sal_ctd_p',
                                             'sal_ctd_s', 'oxy_ctd_p', 'oxy_ctd_s']

    def get_temp_ctd_p(self, instance):
        if type(instance) is models.Bottle:
            return instance.get_ctd_data(sensor_type=models.SensorType.temperature, sensor_name='t')

        return self.get_temp_ctd_p(instance.bottle)

    def get_temp_ctd_s(self, instance):
        if type(instance) is models.Bottle:
            return instance.get_ctd_data(sensor_type=models.SensorType.temperature, sensor_name='t', priority=2)

        return self.get_temp_ctd_s(instance.bottle)

    def get_cond_ctd_p(self, instance):
        if type(instance) is models.Bottle:
            return instance.get_ctd_data(sensor_type=models.SensorType.conductivity, sensor_name='c')

        return self.get_cond_ctd_p(instance.bottle)

    def get_cond_ctd_s(self, instance):
        if type(instance) is models.Bottle:
            return instance.get_ctd_data(sensor_type=models.SensorType.conductivity, sensor_name='c', priority=2)

        return self.get_cond_ctd_s(instance.bottle)

    def get_sal_ctd_p(self, instance):
        if type(instance) is models.Bottle:
            return instance.get_ctd_data(sensor_type=models.SensorType.salinity, sensor_name='sal')

        return self.get_sal_ctd_p(instance.bottle)

    def get_sal_ctd_s(self, instance):
        if type(instance) is models.Bottle:
            return instance.get_ctd_data(sensor_type=models.SensorType.salinity, sensor_name='sal', priority=2)

        return self.get_sal_ctd_s(instance.bottle)

    def get_oxy_ctd_p(self, instance):
        if type(instance) is models.Bottle:
            return instance.get_ctd_data(sensor_type=models.SensorType.oxygen, units='V')

        return self.get_oxy_ctd_p(instance.bottle)

    def get_oxy_ctd_s(self, instance):
        if type(instance) is models.Bottle:
            return instance.get_ctd_data(sensor_type=models.SensorType.oxygen, units='V', priority=2)

        return self.get_oxy_ctd_s(instance.bottle)


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


class SaltReport(SaltSerializer, SampleSerializer):

    class Meta:
        model = SaltSerializer.Meta.model
        fields = SampleSerializer.Meta.fields + SaltSerializer.Meta.fields


class SaltSampleReport(BottleReportSerializer):

    salt_data = SaltSerializer(many=True)

    class Meta:
        model = models.Bottle
        fields = BottleReportSerializer.Meta.fields + ['salt_data']

    def to_representation(self, instance):

        representation = super().to_representation(instance)
        if 'salt_data' in representation.keys():
            salt_data = representation.pop('salt_data')
            if len(salt_data) > 0:
                representation['sample_date'] = salt_data[0]['Sample_Date']
                for index, sample in enumerate(salt_data):
                    representation[f'sal_rep{(index+1)}'] = sample['Calculated']

        return representation


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


class OxygenReport(OxygenSerializer, SampleSerializer):

    class Meta:
        model = OxygenSerializer.Meta.model
        fields = SampleSerializer.Meta.fields + OxygenSerializer.Meta.fields


class OxygenSampleReport(BottleReportSerializer):
    oxygen_data = OxygenSerializer(many=True)

    class Meta:
        model = models.Bottle
        fields = BottleReportSerializer.Meta.fields + ['oxygen_data']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if 'oxygen_data' in representation.keys():
            oxy_data = representation.pop('oxygen_data')
            if len(oxy_data) > 0:
                representation['oxy_w_rep1'] = oxy_data[0]['oxy_w_rep1']
                representation['oxy_w_rep2'] = oxy_data[0]['oxy_w_rep2']

        return representation


class ChlSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ChlSample
        fields = ['sample_order', 'chl', 'phae', 'mean_chl', 'mean_phae']


class ChlReport(ChlSerializer, SampleSerializer):

    class Meta:
        model = ChlSerializer.Meta.model
        fields = SampleSerializer.Meta.fields + ChlSerializer.Meta.fields


class ChlSampleReport(BottleReportSerializer):
    chl_data = ChlSerializer(many=True)

    class Meta:
        model = models.Bottle
        fields = BottleReportSerializer.Meta.fields + ['chl_data']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if 'chl_data' in representation.keys():
            chl_data = representation.pop('chl_data')
            if len(chl_data) > 0:
                chl = {}
                for chl_ in chl_data:
                    chl[f'chl_{chl_["sample_order"]}'] = chl_['chl']
                    chl[f'phae_{chl_["sample_order"]}'] = chl_['phae']

                chl[f'mean_chl'] = chl_data[0]['mean_chl']
                chl[f'mean_phae'] = chl_data[0]['mean_phae']

                representation.update(chl)

        return representation


class ChnSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ChnSample
        fields = ['sample_order', 'carbon', 'nitrogen', 'carbon_nitrogen']


class ChnReport(ChnSerializer, SampleSerializer):
    class Meta:
        model = ChnSerializer.Meta.model
        fields = SampleSerializer.Meta.fields + ChnSerializer.Meta.fields


class HplcSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.HplcSample
        # skip the first three fields which are the pk, the bottle and xxx fields that we don't want
        fields = [field.attname for field in model._meta.fields[3:]]


class HplcReport(HplcSerializer, SampleSerializer):
    class Meta:
        model = HplcSerializer.Meta.model
        fields = SampleSerializer.Meta.fields + HplcSerializer.Meta.fields


class FullReport(BottleReport):
    oxygen_data = OxygenSerializer(many=True, read_only=True)
    salt_data = SaltSerializer(many=True, read_only=True)
    chl_data = ChlSerializer(many=True, read_only=True)

    class Meta:
        model = models.Bottle
        fields = ['Name', 'Station', 'Event', 'Sample', 'Pressure', 'oxygen_data', 'salt_data', 'chl_data']
