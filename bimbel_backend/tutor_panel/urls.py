from django.urls import path
from .views import (
    # Home & Profil
    TutorHomeView,
    TutorUserInfoView,
    TutorProfileView,
    TutorChangePasswordView,
    TutorNotificationSettingsView,
    UpdateTutorSettingView,
    TutorGlobalSearchView,
    TutorNotificationStatusView,

    # Teaching Dashboard
    TutorTeachingDashboardView,
    TutorAddMaterialView,
    TutorAddAssignmentView,
    TutorEditMaterialView,
    TutorEditAssignmentView,
    TutorMaterialDetailView,
    TutorAssignmentDetailView,
    TutorMaterialDeleteView,
    TutorAssignmentDeleteView,
    GradeAssignmentSubmissionView,

    # My Schedule
    TutorScheduleListView,
    TutorScheduleDetailView,
    SelectMaterialView,
    AddAssignmentView,
    MarkAttendanceView,
    RequestRescheduleView,

    # Feedback
    TutorFeedbackListView,
    TutorFeedbackDetailView,

    # Availability
    TutorAvailabilityListView,
    AddTutorAvailabilityView,
    DeleteTutorAvailabilityView,

    # Student Performance
    StudentPerformanceView,
    StudentPerformanceDetailView,
)

urlpatterns = [
    # Home & User Info
    path("home/", TutorHomeView.as_view(), name="tutor-home"),
    path("userinfo/", TutorUserInfoView.as_view(), name="tutor-user-info"),
    path("search/", TutorGlobalSearchView.as_view(), name="tutor-global-search"),
    path("notifications/", TutorNotificationStatusView.as_view(), name="tutor-notifications"),

    # My Schedule
    path("my-schedule/", TutorScheduleListView.as_view(), name="tutor-my-schedule"),
    path("my-schedule/<int:schedule_id>/", TutorScheduleDetailView.as_view(), name="tutor-schedule-detail"),
    path("my-schedule/<int:schedule_id>/select-material/", SelectMaterialView.as_view(), name="select-material"),
    path("my-schedule/<int:schedule_id>/add-assignment/", AddAssignmentView.as_view(), name="add-assignment"),
    path("my-schedule/<int:schedule_id>/mark-attendance/", MarkAttendanceView.as_view(), name="mark-attendance"),
    path("my-schedule/<int:schedule_id>/request-reschedule/", RequestRescheduleView.as_view(), name="request-reschedule"),

    # Teaching Dashboard
    path("teaching-dashboard/", TutorTeachingDashboardView.as_view(), name="tutor-teaching-dashboard"),
    path("teaching-dashboard/add-material/", TutorAddMaterialView.as_view(), name="tutor-add-material"),
    path("teaching-dashboard/add-assignment/", TutorAddAssignmentView.as_view(), name="tutor-add-assignment"),
    path("teaching-dashboard/materials/<int:material_id>/", TutorMaterialDetailView.as_view(), name="tutor-material-detail"),
    path("teaching-dashboard/materials/<int:material_id>/edit/", TutorEditMaterialView.as_view(), name="edit-tutor-material"),
    path("teaching-dashboard/materials/<int:material_id>/delete/", TutorMaterialDeleteView.as_view(), name="delete-tutor-material"),
    path("teaching-dashboard/assignments/<int:assignment_id>/", TutorAssignmentDetailView.as_view(), name="tutor-assignment-detail"),
    path("teaching-dashboard/assignments/<int:assignment_id>/edit/", TutorEditAssignmentView.as_view(), name="edit-tutor-assignment"),
    path("teaching-dashboard/assignments/<int:assignment_id>/delete/", TutorAssignmentDeleteView.as_view(), name="delete-tutor-assignment"),
    path("teaching-dashboard/assignments/<int:assignment_id>/grade/", GradeAssignmentSubmissionView.as_view(), name="grade-assignment"),

    # Student Performance
    path("student-performance/", StudentPerformanceView.as_view(), name="student-performance"),
    path("student-performance/<int:student_id>/", StudentPerformanceDetailView.as_view(), name="student-performance-detail"),

    # Feedback
    path("feedbacks/", TutorFeedbackListView.as_view(), name="tutor-feedback-list"),
    path("feedbacks/<int:feedback_id>/", TutorFeedbackDetailView.as_view(), name="tutor-feedback-detail"),

    # Settings
    path("settings/change-password/", TutorChangePasswordView.as_view(), name="tutor-change-password"),
    path("settings/profile/", TutorProfileView.as_view(), name="tutor-profile"),
    path("settings/notifications/", TutorNotificationSettingsView.as_view(), name="tutor-notification-settings"),
    path("settings/update/", UpdateTutorSettingView.as_view(), name="tutor-update-setting"),

    # Availability
    path("availability/", TutorAvailabilityListView.as_view(), name="tutor-availability"),
    path("availability/add/", AddTutorAvailabilityView.as_view(), name="add-tutor-availability"),
    path("availability/<int:availability_id>/delete/", DeleteTutorAvailabilityView.as_view(), name="delete-tutor-availability"),
]
