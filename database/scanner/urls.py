from django.urls import path
from . import views

urlpatterns = [
    path('',      views.event_list,  name='event_list'),
    path('scan/', views.scan_page,   name='scan'),
    path('scan-stream/', views.scan_stream, name='scan_stream'),
    path('manual/',  views.manual_input_view, name='manual'),
    path('generate/',views.generate_view, name='generate'),
    path('roster/', views.today_roster, name='today_roster'),
]