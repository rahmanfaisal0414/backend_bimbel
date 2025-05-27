from django.urls import path
from .views import (
    # Dashboard & Info
    StudentHomeView,
    StudentUserInfoView,
    StudentGlobalSearchView,
    StudentNotificationView,
    StudentTutorListView,

    # Learning
    StudentLearningDashboardView,
    StudentMaterialDetailView,
    StudentAssignmentDetailView,
    SubmitAssignmentView,

    # Schedule
    StudentScheduleListView,
    StudentScheduleDetailView,
    ConfirmStudentAttendanceView,

    # Attendance
    StudentAttendanceListView,
    StudentAttendanceDetailView,

    # Feedback
    AllFeedbacksForStudentView,
    StudentGiveFeedbackView,
    StudentFeedbackDetailView,

    # Settings
    StudentProfileView,
    StudentChangePasswordView,
    StudentNotificationSettingsView,
    UpdateStudentSettingView,
)

urlpatterns = [
    # Dashboard & Info
    path("dashboard/", StudentHomeView.as_view(), name="student-dashboard"),
    path("userinfo/", StudentUserInfoView.as_view(), name="student-userinfo"),
    path("search/", StudentGlobalSearchView.as_view(), name="student-global-search"),
    path("notifications/", StudentNotificationView.as_view(), name="student-notifications"),
    path("tutors/", StudentTutorListView.as_view(), name="student-tutor-list"),

    # Learning
    path("my-learning/", StudentLearningDashboardView.as_view(), name="student-my-learning"),
    path("my-learning/material/<int:material_id>/", StudentMaterialDetailView.as_view(), name="student-material-detail"),
    path("my-learning/assignment/<int:assignment_id>/", StudentAssignmentDetailView.as_view(), name="student-assignment-detail"),
    path("my-learning/assignment/<int:assignment_id>/submit/", SubmitAssignmentView.as_view(), name="submit-assignment"),

    # Schedule
    path("my-schedule/", StudentScheduleListView.as_view(), name="student-my-schedule"),
    path("my-schedule/<int:schedule_id>/", StudentScheduleDetailView.as_view(), name="student-schedule-detail"),
    path("confirm-attendance/", ConfirmStudentAttendanceView.as_view(), name="student-confirm-attendance"),

    # Attendance
    path("my-attendance/", StudentAttendanceListView.as_view(), name="student-attendance-list"),
    path("my-attendance/<int:attendance_id>/", StudentAttendanceDetailView.as_view(), name="student-attendance-detail"),

    # Feedback
    path("feedbacks/", AllFeedbacksForStudentView.as_view(), name="student-feedback-list"),
    path("feedbacks/add/", StudentGiveFeedbackView.as_view(), name="student-feedback-add"),
    path("feedbacks/<str:id>/", StudentFeedbackDetailView.as_view(), name="student-feedback-detail"),

    # Settings
    path("settings/profile/", StudentProfileView.as_view(), name="student-settings-profile"),
    path("settings/change-password/", StudentChangePasswordView.as_view(), name="student-settings-change-password"),
    path("settings/notifications/", StudentNotificationSettingsView.as_view(), name="student-settings-notifications"),
    path("settings/update/", UpdateStudentSettingView.as_view(), name="student-settings-update"),
]
