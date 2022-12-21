from rest_framework import viewsets

from rest_pandas import PandasViewSet
from django.http import JsonResponse

from .. import models
from . import serializers


# Django, or the database calls, seems to have an issue deleting large numbers of sample ids
# get_chunks will break a list up into sets of manageable size to be deleted.
def get_chunks(lst, size):
    for i in range(0, len(lst), size):
        yield lst[i:i+size]


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
        queryset = models.Event.objects.all()
        if "mission_id" in self.request.GET:
            queryset = queryset.filter(mission_id=self.request.GET['mission_id'])

        if "event_id" in self.request.GET:
            queryset = queryset.filter(event_id=self.request.GET['event_id'])

        if "station" in self.request.GET:
            queryset = queryset.filter(station__name=self.request.GET['station'])

        if "instrument" in self.request.GET:
            queryset = queryset.filter(instrument__name=self.request.GET['instrument'])

        return queryset

    def destroy(self, request, *args, **kwargs):
        # if samples are not specifically listed use get_queryset to filter down to what should be deleted
        sample_set = self.get_queryset()
        sample_set.delete()

        return JsonResponse({})


class ActionViewset(viewsets.ModelViewSet):
    queryset = models.Action.objects.all().order_by('date_time')
    serializer_class = serializers.ActionSerializer

    def get_queryset(self):
        if "event_id" in self.request.GET:
            return models.Action.objects.filter(event_id=self.request.GET['event_id']).order_by('date_time')

        return models.Action.objects.all().order_by('date_time')


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


class BottleViewset(viewsets.ModelViewSet):

    model = models.Bottle
    serializer_class = serializers.BottleReport

    def get_model(self):
        return self.model

    def get_queryset(self):
        queryset = self.get_model().objects.all()
        if 'mission_id' in self.request.GET:
            queryset = queryset.filter(event__mission_id=self.request.GET['mission_id'])

        if 'sample_id' in self.request.GET:
            queryset = queryset.filter(bottle_id=self.request.GET['sample_id'])

        if 'station' in self.request.GET:
            queryset = queryset.filter(event__station__name=self.request.GET['station'])

        return queryset

    def destroy(self, request, *args, **kwargs):
        # if samples are not specifically listed use get_queryset to filter down to what should be deleted
        sample_set = self.get_queryset()
        sample_set.delete()

        return JsonResponse({})


class SampleViewset(viewsets.ModelViewSet):

    model = None

    def get_model(self):
        return self.model

    def get_queryset(self):
        queryset = self.get_model().objects.all()
        if 'mission_id' in self.request.GET:
            queryset = queryset.filter(bottle__event__mission_id=self.request.GET['mission_id'])

        if 'sample_id' in self.request.GET:
            queryset = queryset.filter(bottle__bottle_id=self.request.GET['sample_id'])

        if 'station' in self.request.GET:
            queryset = queryset.filter(bottle__event__station__name=self.request.GET['station'])

        return queryset

    def destroy(self, request, *args, **kwargs):
        # if samples are not specifically listed use get_queryset to filter down to what should be deleted
        sample_set = self.get_queryset()
        sample_set.delete()

        return JsonResponse({})


class SaltViewset(SampleViewset):
    model = models.SaltSample
    serializer_class = serializers.SaltReport


class PandaSaltReport(SaltViewset, PandasViewSet):

    def get_pandas_filename(self, request, format):
        return f"{models.Mission.objects.get(pk=request.query_params['mission']).name}_Salt_Report"


class OxygenViewset(SampleViewset):
    model = models.OxygenSample
    serializer_class = serializers.OxygenReport


class PandaOxygenReport(OxygenViewset, PandasViewSet):

    def get_pandas_filename(self, request, format):
        return f"{models.Mission.objects.get(pk=request.query_params['mission']).name}_Oxygen_Report"


class ChlViewset(SampleViewset):
    model = models.ChlSample
    serializer_class = serializers.ChlReport


class PandaChlReport(ChlViewset, PandasViewSet):

    def get_pandas_filename(self, request, format):
        return f"{models.Mission.objects.get(pk=request.query_params['mission']).name}_Chl_Report"


class ChnViewset(SampleViewset):
    model = models.ChnSample
    serializer_class = serializers.ChnReport


class HplcViewset(SampleViewset):
    model = models.HplcSample
    serializer_class = serializers.HplcReport

    def get_queryset(self):
        result = super().get_queryset()

        return result


class FullSampleViewset(viewsets.ModelViewSet):
    queryset = models.Bottle.objects.all()
    serializer_class = serializers.FullReport

    def get_queryset(self):
        queryset = models.Bottle.objects.all()

        if 'mission_id' in self.request.GET:
            queryset = queryset.filter(event__mission_id=self.request.GET['mission_id'])

        return queryset