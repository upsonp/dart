from rest_framework import viewsets
from django.http import FileResponse

from rest_framework import viewsets, renderers
from rest_framework.decorators import action

from rest_pandas import PandasViewSet

from .. import models
from . import serializers

class MissionReportViewset(viewsets.ModelViewSet):
    queryset = models.Mission.objects.all()
    serializer_class = serializers.MissionReportSerializer

    def get_queryset(self):
        if "mission_id" in self.request.GET:
            return models.Mission.objects.filter(pk=self.request.GET['mission_id'])
        elif "name" in self.request.GET:
            return models.Mission.objects.filter(name=self.request.GET["name"])

        return models.Mission.objects.all()


class EventViewset(viewsets.ModelViewSet):
    queryset = models.Event.objects.all()
    serializer_class = serializers.EventSerializer

    def get_queryset(self):
        if "mission_id" in self.request.GET:
            return models.Event.objects.filter(mission_id=self.request.GET['mission_id'])

        return models.Event.objects.all()


class ActionViewset(viewsets.ModelViewSet):
    queryset = models.Action.objects.all()
    serializer_class = serializers.ActionSerializer

    def get_queryset(self):
        if "event_id" in self.request.GET:
            return models.Action.objects.filter(event_id=self.request.GET['event_id'])

        return models.Action.objects.all()


class CTDReport(viewsets.ModelViewSet):
    queryset = models.Mission.objects.all()
    serializer_class = serializers.CTDReportSerializer

    def get_queryset(self):
        if 'mission_id' in self.request.GET:
            return models.Mission.objects.filter(pk=self.request.GET['mission_id'])
        return models.Mission.objects.all()


class StationNameViewset(viewsets.ModelViewSet):
    queryset = models.Station.objects.all().distinct().order_by("name")
    serializer_class = serializers.StationSerializer

    def get_queryset(self):
        if 'mission_id' in self.request.GET:
            return models.Station.objects.filter(events__mission_id=self.request.GET['mission_id'])\
                .distinct().order_by("name")

        return models.Station.objects.all().distinct().order_by("name")


class ErrorViewset(viewsets.ModelViewSet):
    queryset = models.Mission.objects.all()
    serializer_class = serializers.MissionErrorSerializer

    def get_queryset(self):
        if 'mission_id' in self.request.GET:
            return models.Mission.objects.filter(pk=self.request.GET['mission_id'])

        return models.Mission.objects.all()


class GetErrorReport(viewsets.ModelViewSet):
    queryset = models.Error.objects.all()
    serializer_class = serializers.ErrorSerializer

    def get_queryset(self):
        if 'mission_id' in self.request.GET:
            return models.Error.objects.filter(mission_id=self.request.GET['mission_id'])

        return models.Error.objects.all()


class SaltViewset(viewsets.ModelViewSet):
    queryset = models.SaltSample.objects.all()

    serializer_class = serializers.SaltReport

    def get_queryset(self):
        if 'mission_id' in self.request.GET:
            return models.SaltSample.objects.filter(bottle__event__mission=self.request.GET['mission_id'])

        return models.SaltSample.objects.all()


class PandaSaltReport(SaltViewset, PandasViewSet):

    def get_pandas_filename(self, request, format):
        return f"{models.Mission.objects.get(pk=request.query_params['mission']).name}_Salt_Report"


class OxygenViewset(viewsets.ModelViewSet):
    queryset = models.OxygenSample.objects.all()

    serializer_class = serializers.OxygenReport

    def get_queryset(self):
        if 'mission_id' in self.request.GET:
            return models.OxygenSample.objects.filter(bottle__event__mission=self.request.GET['mission_id'])

        return models.OxygenSample.objects.all()


class PandaOxygenReport(OxygenViewset, PandasViewSet):

    def get_pandas_filename(self, request, format):
        return f"{models.Mission.objects.get(pk=request.query_params['mission']).name}_Oxygen_Report"


class ChlViewset(viewsets.ModelViewSet):
    queryset = models.ChlSample.objects.all()

    serializer_class = serializers.ChlReport

    def get_queryset(self):
        if 'mission_id' in self.request.GET:
            return models.ChlSample.objects.filter(bottle__event__mission=self.request.GET['mission_id'])

        return models.ChlSample.objects.all()


class PandaChlReport(ChlViewset, PandasViewSet):

    def get_pandas_filename(self, request, format):
        return f"{models.Mission.objects.get(pk=request.query_params['mission']).name}_Chl_Report"
