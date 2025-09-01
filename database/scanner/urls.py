from django.urls import path
from . import views
from . import api
from . import views_api
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('', views.index, name='index'),
    path('', views.event_list, name='event_list'),
    path('scan/', views.scan_page, name='scan'),
    path('scan-stream/', views.scan_stream, name='scan_stream'),
    path('manual/',  views.manual_input_view, name='manual'),
    path('generate/',views.generate_view, name='generate'),
    path('roster/', views.today_roster, name='today_roster'),
    path('events.pdf', views.export_events_pdf, name='export_events_pdf'),
    path('reports/import/', views.import_report, name='import_report'),
    path('api/', views.api_router, name='api'),
    path('api/', api.api_router, name='api_router'),
    path('api.php', views_api.api_php_compat, name='api_php_compat')
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)