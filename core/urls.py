from django.urls import path

from . import views, utils, reports

app_name = 'core'

urlpatterns = [
    path('mission/', views.MissionFilterView.as_view(), name="mission_filter"),
    path('mission/new/', views.MissionCreateView.as_view(), name="mission_new"),
    path('mission/event/<int:pk>/', views.EventDetails.as_view(), name="event_details"),
    path('mission/ctd/<int:pk>/', views.CTDDetails.as_view(), name="ctd_details"),
    path('mission/sample/<int:pk>/', views.SampleDetails.as_view(), name="sample_details"),
    path('mission/delete/', views.mission_delete, name="mission_delete"),

    path('load/', utils.get_files, name="load_files"),
    path('load/ctd/', utils.get_ctd_files, name="load_ctd_files"),
    path('load/samples/<int:pk>/', utils.load_samples, name="ajax_load_samples"),

    path('process/core/', utils.process_elog, name="process_elog"),
    path('process/ctd/', utils.process_ctd, name="process_ctd"),

    path('report/core/summary/<int:pk>/', reports.report_elog_summary, name="event_summary_report"),
]
