from django.urls import reverse_lazy, path
from django.utils.translation import gettext as _

from dart.views import GenericTemplateView
from . import form_global_station_plan


class StationPlanDetails(GenericTemplateView):
    page_title = _("Station Plan Details")
    template_name = "settingsdb/station_plan.html"

    def get_page_title(self):
        return _("Station Plan Details")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['station_form'] = form_global_station_plan.StationForm()
        return context


path_prefix = 'station/plan'
station_plan_urls = [
    path(f'{path_prefix}/', StationPlanDetails.as_view(), name="station_plan_details"),
]

station_plan_urls += form_global_station_plan.station_plan_urls
