from django.urls import path
from . import views

app_name = 'calendar'

urlpatterns = [
    path('', views.CalendarView.as_view(), name='calendar'),
    path('events/', views.EventListView.as_view(), name='event_list'),
    path('events/create/', views.EventCreateView.as_view(), name='event_create'),
    path('events/<int:pk>/', views.EventDetailView.as_view(), name='event_detail'),
    path('events/<int:pk>/edit/', views.EventUpdateView.as_view(), name='event_edit'),
    path('events/<int:pk>/delete/', views.EventDeleteView.as_view(), name='event_delete'),
    path('events/<int:pk>/register/', views.event_register, name='event_register'),
    path('events/<int:pk>/unregister/', views.event_unregister, name='event_unregister'),
    path('events/json/', views.calendar_json, name='calendar_json'),
    path('events/action-log/', views.EventActionLogView.as_view(), name='event_action_log'),
    path('members/autocomplete/', views.member_autocomplete, name='member_autocomplete'),
]

