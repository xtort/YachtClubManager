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
    # Member Type management
    path('member-types/', views.MemberTypeListView.as_view(), name='member_type_list'),
    path('member-types/create/', views.MemberTypeCreateView.as_view(), name='member_type_create'),
    path('member-types/<int:pk>/edit/', views.MemberTypeUpdateView.as_view(), name='member_type_edit'),
    path('member-types/<int:pk>/delete/', views.MemberTypeDeleteView.as_view(), name='member_type_delete'),
    path('member-types/reorder/', views.member_type_reorder, name='member_type_reorder'),
    # Role management
    path('roles/', views.RoleListView.as_view(), name='role_list'),
    path('roles/create/', views.RoleCreateView.as_view(), name='role_create'),
    path('roles/<int:pk>/edit/', views.RoleUpdateView.as_view(), name='role_edit'),
    path('roles/<int:pk>/delete/', views.RoleDeleteView.as_view(), name='role_delete'),
    # Member directory (accessible to members, editors, admins - not viewers)
    path('members/', views.MembersDirectoryView.as_view(), name='members_directory'),
    # Profile management (for all authenticated users)
    path('profile/', views.ProfileUpdateView.as_view(), name='profile'),
]

