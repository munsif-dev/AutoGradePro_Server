from django.urls import path
from . import views

urlpatterns = [
    path('module/', views.ModuleListCreate.as_view(), name='module-list-create'), # this url is to create a module
    path('module/delete/<int:pk>/', views.ModuleDeleteView.as_view(), name='module-delete'), # this is to delete a module
    path('module/list/', views.ModuleListView.as_view(), name='module-list'), # this is to list all modules
    path('module/<int:pk>/', views.ModuleDetailView.as_view(), name='module-detail'), # this is to get a specific module
    path('module/edit/<int:pk>/', views.ModuleUpdateView.as_view(), name='module-edit'),
    path('lecturer/list/', views.GetLecturerView.as_view(), name='create-lecturer'), # this is to create a lectur
    path('lecturer/details/', views.LecturerDetailView.as_view(), name='lecturer-details'),
   
    path('assignment/', views.AssignmentListCreate.as_view(), name='assignment-list-create'), # this is to create an assignment
    path('assignment/delete/<int:pk>/', views.AssignmentDeleteView.as_view(), name='assignment-delete'), # this is to delete an assignment
    path('assignment/edit/<int:pk>/', views.AssignmentUpdateView.as_view(), name='assignment-edit'), # this is to edit an assignment
    path('assignment/<int:pk>/', views.AssignmentDetailView.as_view(), name='assignment-list'), # this is to list all assignments
    path('assignment/list/', views.AssignmentListView.as_view(), name='assignment-list'), # this is to list all assignments

    path('submission/<int:submission_id>/upload/', views.FileUploadView.as_view(), name='file-upload'),
    path('submission/<int:assignment_id>/grade/', views.GradeSubmissionView.as_view(), name='grade-submission'),
    path('submission/<int:assignment_id>/files/', views.FileListView.as_view(), name='file-list'),
    path('submission/<int:submission_id>/delete-file/<int:fileId>/',views.DeleteFileView.as_view(),name='delete-file'),
    path('submission/<int:submission_id>/grading-results/', views.GradingResultListView.as_view(), name='grading-results-list'),

    path('assignment/<int:assignment_id>/clear-grading-results/', views.ClearGradingResultsView.as_view(), name='clear-grading-results'),
    path('assignment/<int:assignment_id>/marking-scheme/', views.MarkingSchemeCreateView.as_view(), name='marking-scheme-create'),
    path('assignment/<int:assignment_id>/marking-scheme/detail/', views.MarkingSchemeRetrieveUpdateDestroyView.as_view(), name='marking-scheme-detail'),
    path('assignment/<int:assignment_id>/parse-marking-scheme/', views.ParseMarkingSchemeView.as_view(), name='parse-marking-scheme'),
    path('assignment/<int:assignment_id>/report/', views.AssignmentReportView.as_view(), name='assignment_report'),
    path('assignment/<int:assignment_id>/<int:file_id>/detail/', views.FileDetailView.as_view(), name='submission_report'),

    
    path('dashboard/stats/', views.DashboardStatsView.as_view(), name='dashboard-stats'),
    path("dashboard/module-trends/", views.get_module_trends, name="module-trends"),
    path("dashboard/assignment-trends/", views.get_assignment_trends, name="assignment-trends"),
    path("dashboard/upload-trends/", views.get_upload_trends, name="upload-trends"),
    path("assignment-list-page", views.AssignmentListPageView.as_view(), name= "assignment-list-for-sorting/filtering"),

    # api/urls.py - Add new endpoints
    path('profile/', views.LecturerProfileView.as_view(), name='lecturer-profile'),
    path('profile/user/', views.UserProfileView.as_view(), name='user-profile'),
    path('profile/password/', views.PasswordChangeView.as_view(), name='password-change'),
    path('profile/picture/', views.ProfilePictureView.as_view(), name='profile-picture'),

]