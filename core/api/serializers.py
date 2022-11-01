from datetime import datetime

from .. import models

from rest_framework import serializers


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
    actions = ActionSummarySerializer(many=True, read_only=True)
    station = serializers.SerializerMethodField("get_station_name")

    class Meta:
        model = models.Event
        fields = '__all__'

    def get_station_name(self, obj):
        return {"id": obj.station.id, "name": obj.station.name}


class MissionReportSerializer(serializers.ModelSerializer):

    events = EventSerializer(many=True, read_only=True)

    class Meta:
        model = models.Mission
        fields = '__all__'


class CTDData(serializers.ModelSerializer):

    values = serializers.SerializerMethodField()

    class Meta:
        model = models.BottleData
        fields = ['values']

    def get_values(self, instance):
        pass


class CTDReportSerializer(serializers.ModelSerializer):

    __headers = None
    __bottles = None

    headers = serializers.SerializerMethodField()
    bottles = serializers.SerializerMethodField()

    class Meta:
        model = models.Mission
        fields = ['headers', 'bottles']

    def get_headers(self, instance):
        self.__headers = models.DataColumn.objects.filter(bottle_data__bottle__event__mission=instance).distinct()
        return [{"header": h.name, "data": [d.value for d in h.bottle_data.all().order_by("bottle__event__station_id")]} for h in self.__headers]

    def get_bottles(self, instance):
        self.__bottles = models.Bottle.objects.filter(event__mission=instance).order_by("event__station_id").distinct()
        return [b.bottle_id for b in self.__bottles]
