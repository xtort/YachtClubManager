from django.urls import path
from . import views

app_name = 'management'

urlpatterns = [
    path('', views.management_dashboard, name='dashboard'),
    path('section/', views.dashboard_section, name='dashboard_section'),
    # Category management
    path('categories/', views.EventCategoryListView.as_view(), name='category_list'),
    path('categories/create/', views.EventCategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/edit/', views.EventCategoryUpdateView.as_view(), name='category_edit'),
    path('categories/<int:pk>/delete/', views.EventCategoryDeleteView.as_view(), name='category_delete'),
    # User management
    path('users/', views.ClubUserListView.as_view(), name='user_list'),
    path('users/create/', views.ClubUserCreateView.as_view(), name='user_create'),
    path('users/<int:pk>/edit/', views.ClubUserUpdateView.as_view(), name='user_edit'),
    path('users/<int:pk>/delete/', views.ClubUserDeleteView.as_view(), name='user_delete'),
    # Profile management (for all authenticated users)
    path('profile/', views.ProfileUpdateView.as_view(), name='profile'),
]

