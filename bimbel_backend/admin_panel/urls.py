from django.urls import path
from .views import (
    # Dashboard & Sidebar
    AdminDashboardView,
    SidebarUserInfoView,
    AdminNotificationStatusView,
    GlobalSearchView,

    # Profile & Settings
    AdminProfileView,
    ChangePasswordView,
    FeedbackModerationSettingView,
    UpdateFeedbackModerationSettingView,
    LearningContentSettingsView,
    NotificationSettingsView,
    UpdateSettingView,

    # Student Management
    AdminStudentManagementView,
    AdminStudentDetailView,
    AdminUpdateStudentView,
    ChangeStudentClassView,
    DeactivateStudentAccountView,

    # Tutor Management
    TutorListView,
    TutorDetailView,
    UpdateTutorView,
    ToggleTutorAccountView,

    # Class Management
    ClassListView,
    ClassManagementListView,
    AddClassView,
    AddScheduleView,
    ScheduleDetailView,
    EditScheduleView,
    CancelScheduleView,
    AvailableTutorsView,

    # Learning Material Management
    LearningMaterialListView,
    AddMaterialView,
    MaterialDetailView,
    DeleteMaterialView,
    EditMaterialView,

    # Feedback Management
    FeedbackListView,
    FeedbackDetailView,
    ApproveFeedbackView,

    # Token & Subject
    AdminTokenListView,
    SubjectListView,
    AddSubjectView,

    # Reschedule Requests
    AdminRescheduleListView,
    AdminApproveReschedule,
    AdminRejectReschedule,
)

urlpatterns = [
    # Dashboard & Sidebar
    path('dashboard/', AdminDashboardView.as_view(), name='admin-dashboard'),
    path('userinfo/', SidebarUserInfoView.as_view(), name='admin-userinfo'),
    path('notifications/', AdminNotificationStatusView.as_view(), name='admin-notification'),
    path('search/', GlobalSearchView.as_view(), name='global-search'),

    # Profile & Settings
    path('profile/', AdminProfileView.as_view(), name='admin-profile'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('settings/feedback-moderation/', FeedbackModerationSettingView.as_view(), name='feedback-moderation'),
    path('settings/feedback-moderation/update/', UpdateFeedbackModerationSettingView.as_view(), name='update-feedback-moderation'),
    path('settings/learning-content/', LearningContentSettingsView.as_view(), name='learning-content-settings'),
    path('settings/notifications/', NotificationSettingsView.as_view(), name='notification-settings'),
    path('settings/update/', UpdateSettingView.as_view(), name='update-setting'),

    # Student Management
    path('students/', AdminStudentManagementView.as_view(), name='admin-students'),
    path('student/<int:student_id>/', AdminStudentDetailView.as_view(), name='admin-student-detail'),
    path('student/<int:student_id>/update/', AdminUpdateStudentView.as_view(), name='admin-edit-student'),
    path('student/<int:student_id>/change-class/', ChangeStudentClassView.as_view(), name='change-student-class'),
    path('student/<int:student_id>/deactivate/', DeactivateStudentAccountView.as_view(), name='deactivate-student'),

    # Tutor Management
    path('tutors/', TutorListView.as_view(), name='tutor-list'),
    path('tutor/<int:tutor_id>/', TutorDetailView.as_view(), name='tutor-detail'),
    path('tutor/<int:tutor_id>/update/', UpdateTutorView.as_view(), name='update-tutor'),
    path('tutor/<int:tutor_id>/toggle-status/', ToggleTutorAccountView.as_view(), name='toggle-tutor-status'),

    # Class Management
    path('list-classes/', ClassListView.as_view(), name='admin-listclass'),
    path('class-management/', ClassManagementListView.as_view(), name='class-management'),
    path('class-management/add-class/', AddClassView.as_view(), name='admin-add-class'),
    path('class-management/add-schedule/', AddScheduleView.as_view(), name='admin-add-schedule'),
    path('class-management/<int:schedule_id>/', ScheduleDetailView.as_view(), name='admin-detail-schedule'),
    path('class-management/<int:schedule_id>/edit/', EditScheduleView.as_view(), name='admin-edit-schedule'),
    path('class-management/<int:schedule_id>/cancel/', CancelScheduleView.as_view(), name='cancel-schedule'),
    path('available-tutors/', AvailableTutorsView.as_view(), name='available-tutors'),

    # Learning Material Management
    path('learning-management/', LearningMaterialListView.as_view(), name='learning-management'),
    path('learning-management/add/', AddMaterialView.as_view(), name='add-material'),
    path('learning-management/<int:material_id>/', MaterialDetailView.as_view(), name='material-detail'),
    path('learning-management/<int:material_id>/delete/', DeleteMaterialView.as_view(), name='delete-material'),
    path('learning-management/<int:material_id>/edit/', EditMaterialView.as_view(), name='edit-material'),

    # Feedback Management
    path('feedbacks/', FeedbackListView.as_view(), name='feedback-list'),
    path('feedbacks/<int:id>/', FeedbackDetailView.as_view(), name='feedback-detail'),
    path('feedbacks/<int:id>/approve/', ApproveFeedbackView.as_view(), name='approve-feedback'),

    # Token & Subject
    path('tokens/', AdminTokenListView.as_view(), name='admin-token-list'),
    path('list-subject/', SubjectListView.as_view(), name='admin-subject-list'),
    path('subject/add/', AddSubjectView.as_view(), name='add-subject'),

    # Reschedule Requests
    path('reschedule-requests/', AdminRescheduleListView.as_view(), name='reschedule-list'),
    path('reschedule-requests/<int:reschedule_id>/approve/', AdminApproveReschedule.as_view(), name='approve-reschedule'),
    path('reschedule-requests/<int:reschedule_id>/reject/', AdminRejectReschedule.as_view(), name='reject-reschedule'),
]
