from django.urls import path
from . import views

urlpatterns = [
    path ('module/', views.ModuleListCreate.as_view(), name='module-list-create'), # this url is to create a module
    path ('module/delete/<int:pk>/', views.ModuleDeleteView.as_view(), name='module-delete'), # this is to delete a module
    path('module/list/', views.ModuleListView.as_view(), name='module-list'), # this is to list all modules
    path('module/<int:pk>/', views.ModuleDetailView.as_view(), name='module-detail'), # this is to get a specific module
    path('lecturer/list/', views.GetLecturerView.as_view(), name='create-lecturer'), # this is to create a lecturer
    path('assignment/', views.AssignmentListCreate.as_view(), name='assignment-list-create'), # this is to create an assignment
    path('assignment/delete/<int:pk>/', views.AssignmentDeleteView.as_view(), name='assignment-delete'), # this is to delete an assignment
    path('assignment/<int:pk>/', views.AssignmentDetailView.as_view(), name='assignment-list'), # this is to list all assignments
    path('assignment/list/', views.AssignmentListView.as_view(), name='assignment-list'), # this is to list all assignments
    path('submission/<int:submission_id>/upload/', views.FileUploadView.as_view(), name='file-upload'),
    path('submission/<int:submission_id>/grade/', views.GradeSubmissionView.as_view(), name='grade-submission'),
    path('submission/<int:assignment_id>/files/', views.FileListView.as_view(), name='file-list'),
    path('submission/<int:submission_id>/delete-file/<int:fileId>/',views.DeleteFileView.as_view(),name='delete-file'),
    path("marking-schemes/", views.MarkingSchemeListCreateView.as_view(), name="marking-scheme-list-create"),
    path("marking-schemes/<int:pk>/", views.MarkingSchemeRetrieveUpdateDestroyView.as_view(), name="marking-scheme-detail"),



]