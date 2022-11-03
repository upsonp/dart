from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'mission-report', views.MissionReportViewset, basename='mission-report')
router.register(r'event', views.EventViewset, basename='event')
router.register(r'action', views.ActionViewset, basename='action')
router.register(r'ctd-report', views.CTDReport, basename='ctd-report')

router.register(r'oxygen', views.OxygenViewset, basename='oxygen')
router.register(r'salt', views.SaltViewset, basename='salt')
router.register(r'chl', views.ChlViewset, basename='chl')

urlpatterns = [
    path("", include((router.urls, 'core-api'), namespace='core-api')),
]

