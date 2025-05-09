from django.urls import path

from .views import (
    AdminDashboardView,
    SidebarUserInfoView,
    AdminStudentManagementView,
    AdminStudentDetailView,
    AdminUpdateStudentView,
    ChangeStudentClassView,
    DeactivateStudentAccountView,
    AdminTokenListView,
    ClassListView,
    TutorListView,
    SubjectListView,
)

urlpatterns = [
    path('dashboard/', AdminDashboardView.as_view(), name='admin-dashboard'),
    path('userinfo/', SidebarUserInfoView.as_view(), name='admin-userinfo'),
    path('list-classes/', ClassListView.as_view(), name='admin-listclass'),
    
    path('students/', AdminStudentManagementView.as_view(), name='admin-students'),
    path('student/<int:student_id>/', AdminStudentDetailView.as_view(), name='admin-student-detail'),
    path("student/<int:student_id>/update/", AdminUpdateStudentView.as_view(), name="admin-edit-student"),
    path("student/<int:student_id>/change-class/", ChangeStudentClassView.as_view()),
    path("student/<int:student_id>/deactivate/", DeactivateStudentAccountView.as_view()),
    
     path('tutors/', TutorListView.as_view(), name='tutor-list'),

    
    path("list-subject/", SubjectListView.as_view(), name="admin-subject-list"),
    
    path("tokens/", AdminTokenListView.as_view(), name="admin-token-list"),
]
