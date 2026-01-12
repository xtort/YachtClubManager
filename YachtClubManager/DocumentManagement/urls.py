from django.urls import path
from . import views

app_name = 'document_management'

urlpatterns = [
    # Dashboard
    path('', views.document_management_dashboard, name='dashboard'),
    
    # Folders
    path('folders/', views.FolderListView.as_view(), name='folder_list'),
    path('folders/<int:pk>/', views.FolderDetailView.as_view(), name='folder_detail'),
    path('folders/create/', views.FolderCreateView.as_view(), name='folder_create'),
    path('folders/<int:pk>/edit/', views.FolderUpdateView.as_view(), name='folder_edit'),
    path('folders/<int:pk>/delete/', views.FolderDeleteView.as_view(), name='folder_delete'),
    
    # Files
    path('files/upload/', views.FileUploadView.as_view(), name='file_upload'),
    path('files/<int:pk>/', views.FileDetailView.as_view(), name='file_detail'),
    path('files/<int:pk>/download/', views.FileDownloadView.as_view(), name='file_download'),
    path('files/<int:pk>/edit/', views.FileUpdateView.as_view(), name='file_edit'),
    path('files/<int:pk>/delete/', views.FileDeleteView.as_view(), name='file_delete'),
    
    # Permissions
    path('folders/<int:folder_id>/permissions/create/', views.FolderPermissionCreateView.as_view(), name='permission_create'),
    path('permissions/<int:pk>/edit/', views.FolderPermissionUpdateView.as_view(), name='permission_edit'),
    path('permissions/<int:pk>/delete/', views.FolderPermissionDeleteView.as_view(), name='permission_delete'),
]

