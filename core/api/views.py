from rest_framework import viewsets
from rest_framework.response import Response

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
