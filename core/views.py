from django.urls import reverse_lazy
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.views.generic import TemplateView, CreateView, UpdateView, DetailView
from django_filters.views import FilterView

from core import forms, filters, models


def mission_delete(request):
    if "mission" in request.GET:
        m = models.Mission.objects.get(pk=request.GET["mission"])
        m.delete()

    messages.success(request=request, message="Mission Deleted")
    return HttpResponseRedirect(reverse_lazy("core:mission_filter"))


class GenericViewMixin:
    page_title = None

    def get_page_title(self):
        return self.page_title

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = self.get_page_title()

        return context


class GenericFlilterMixin(GenericViewMixin, FilterView):
    new_url = None

    def get_new_url(self):
        return self.new_url

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["new_url"] = self.get_new_url()
        context["obj"] = self.get_queryset().values()

        return context


class GenericCreateView(GenericViewMixin, CreateView):
    success_url = None

    def get_success_url(self):
        return self.success_url


class GenericUpdateView(GenericViewMixin, UpdateView):
    success_url = None

    def get_success_url(self):
        return self.success_url


class MissionMixin():
    model = models.Mission
    page_title = "Missions"


class MissionFilterView(MissionMixin, GenericFlilterMixin):
    filterset_class = filters.MissionFilter
    new_url = reverse_lazy("core:mission_new")


class MissionCreateView(MissionMixin, GenericCreateView):
    success_url = reverse_lazy("core:mission_filter")
    form_class = forms.MissionSettingsForm
    template_name = "core/mission_settings.html"

    def form_valid(self, form):
        response = super().form_valid(form)

        data = form.cleaned_data

        dfd = models.DataFileDirectory(mission=self.object, directory=data['elog_dir'])
        dfd.save()

        dfd_type = models.DataFileDirectoryType(directory=dfd, file_type=models.FileType.log.value)
        dfd_type.save()

        dfd = models.DataFileDirectory(mission=self.object, directory=data['bottle_dir'])
        dfd.save()

        dfd_type = models.DataFileDirectoryType(directory=dfd, file_type=models.FileType.btl.value)
        dfd_type.save()

        return response


class EventDetails(GenericViewMixin, DetailView):
    model = models.Mission
    template_name = 'core/event_details.html'

    def get_page_title(self):
        return f'{self.object.name} - Event Details'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['action_types'] = [{"id": a[0], "name": a[1]} for a in models.ActionType.choices]
        context['instrument_types'] = [{"id": i[0], "name": i[1]} for i in models.InstrumentType.choices]

        return context


class CTDDetails(GenericViewMixin, DetailView):
    model = models.Mission
    template_name = 'core/ctd_details.html'

    def get_page_title(self):
        return f'{self.object.name} - CTD Details'


class SampleDetails(GenericViewMixin, DetailView):
    model = models.Mission
    template_name = 'core/sample_details.html'

    def get_page_title(self):
        return f'{self.object.name} - Sample Details'
