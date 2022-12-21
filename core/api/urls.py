from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'mission-report', views.MissionReportViewset, basename='mission-report')
router.register(r'event', views.EventViewset, basename='event')
router.register(r'action', views.ActionViewset, basename='action')
router.register(r'ctd-report', views.CTDReport, basename='ctd-report')

router.register(r'station-name', views.StationNameViewset, basename='station-name')

router.register(r'full_samples', views.FullSampleViewset, basename='full_samples')
router.register(r'bottle', views.BottleViewset, basename='bottle')
router.register(r'oxygen', views.OxygenViewset, basename='oxygen')
router.register(r'salt', views.SaltViewset, basename='salt')
router.register(r'chl', views.ChlViewset, basename='chl')
router.register(r'chn', views.ChnViewset, basename='chn')
router.register(r'hplc', views.HplcViewset, basename='hplc')

router.register(r'error', views.ErrorViewset, basename='error')

# pandasView
router.register(r'pd_salt', views.PandaSaltReport, basename='pd_salt')
router.register(r'pd_oxygen', views.PandaOxygenReport, basename='pd_oxygen')
router.register(r'pd_chl', views.PandaChlReport, basename='pd_chl')

# I use the following to print URLs when the server starts to get an idea of how to reverse them
# import pprint
# pprint.pprint(router.get_urls())

urlpatterns = [
    path("", include((router.urls, 'core-api'), namespace='core-api')),
]

