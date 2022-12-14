from django.urls import path

from core import views
from core import utils
from core import reports
from core import readers

app_name = 'core'

urlpatterns = [

    path('mission/dir/<int:mission>/', utils.ajax_set_directory, name="set_dir"),

    path('mission/', views.MissionFilterView.as_view(), name="mission_filter"),
    path('mission/new/', views.MissionCreateView.as_view(), name="mission_new"),
    path('mission/event/<int:pk>/', views.EventDetails.as_view(), name="event_details"),
    path('mission/sample/<int:pk>/', views.SampleDetails.as_view(), name="sample_details"),
    path('mission/delete/', views.mission_delete, name="mission_delete"),

    path('error/<int:pk>/', views.ErrorDetails.as_view(), name="error_details"),

    path('load/', readers.get_files, name="load_files"),
    path('load/ctd/', readers.get_ctd_files, name="load_ctd_files"),
    path('load/samples/<int:pk>/', readers.load_samples, name="ajax_load_samples"),

    path('process/core/', readers.process_elog, name="process_elog"),
    path('process/ctd/<int:mission_id>/', readers.process_ctd, name="process_ctd"),

    path('report/core/elog_summary/<int:pk>/', reports.report_elog_summary, name="event_summary_report"),
    path('report/core/profile_summary/<int:pk>/', reports.report_profile_summary, name="profile_summary_report"),
    path('report/core/biosum_report/<int:pk>/', reports.report_biosum_report, name="biosum_report"),
    path('report/core/error_report/<int:pk>/', reports.report_error_report, name="error_report"),
]
