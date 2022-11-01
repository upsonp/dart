
from django.contrib import admin
from django.urls import path, include

from django.conf import settings
from django.conf.urls.static import static

from core import views

urlpatterns = [
    path('', views.MissionFilterView.as_view(), name="index"),
    path('admin/', admin.site.urls),

    path('core/', include('core.urls')),
    path('core/api/', include('core.api.urls')),

] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
