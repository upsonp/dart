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
    home_url = reverse_lazy('core:mission_filter')

    def get_home_url(self):
        return self.home_url

    def get_page_title(self):
        return self.page_title

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["home_url"] = self.get_home_url()
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


class ErrorMixin():
    model = models.Error
    page_title = "Errors"


class MissionFilterView(MissionMixin, GenericFlilterMixin):
    filterset_class = filters.MissionFilter
    new_url = reverse_lazy("core:mission_new")


class MissionCreateView(MissionMixin, GenericCreateView):
    success_url = reverse_lazy("core:mission_filter")
    form_class = forms.MissionSettingsForm
    template_name = "core/mission_settings.html"

    def get_success_url(self):
        success = super().get_success_url()
        success = reverse_lazy("core:event_details", args=(self.object.pk, ))
        return success

    def form_valid(self, form):
        response = super().form_valid(form)

        data = form.cleaned_data

        if 'elog_dir' in data:
            dfd = models.DataFileDirectory(mission=self.object, directory=data['elog_dir'])
            dfd.save()

            dfd_type = models.DataFileDirectoryType(directory=dfd, file_type=models.FileType.log.value)
            dfd_type.save()

        if 'bottle_dir' in data:
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

        elog_dir = self.object.mission_directories.filter(file_types__file_type=models.FileType.log.value)
        context['elog_dir'] = elog_dir[0].directory if elog_dir else ""
        context['action_types'] = [{"id": a[0], "name": a[1]} for a in models.ActionType.choices]
        context['instrument_types'] = [{"id": i[0], "name": i[1]} for i in models.InstrumentType.choices]

        return context


class SampleDetails(GenericViewMixin, DetailView):
    model = models.Mission
    template_name = 'core/sample_details.html'

    def get_page_title(self):
        return f'{self.object.name} - Sample Details'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['tab_keys'] = {
          'oxy': {'get': 'core-api:oxygen-list', 'delete': 'core-api:oxygen-list'},
          'salt': {'get': 'core-api:salt-list', 'delete': 'core-api:salt-list'},
          'chl': {'get': 'core-api:chl-list', 'delete': 'core-api:chl-list'},
          'chn': {'get': 'core-api:chn-list', 'delete': 'core-api:chn-list'},
          'hplc': {'get': 'core-api:hplc-list', 'delete': 'core-api:hplc-list'},
        }
        ctd_dir = self.object.mission_directories.filter(file_types__file_type=models.FileType.btl.value)
        context['ctd_dir'] = ctd_dir[0].directory if ctd_dir else ""

        return context


class ErrorDetails(GenericViewMixin, DetailView):
    model = models.Mission
    template_name = 'core/error_details.html'

    def get_page_title(self):
        return f'{self.object.name} - Error Report'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['error_type'] = [{"id": i[0], "name": i[1]} for i in models.ErrorType.choices]

        return context
