import django_filters

from core import models


class MissionFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = models.Mission
        fields = ['name']


class ErrorFilter(django_filters.FilterSet):
    class Meta:
        model = models.Error
        fields = '__all__'
