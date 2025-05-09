from django.contrib import admin
from .models import (
    Users, Students, Tutors, SignupTokens, Classes,
    Schedules, Attendance, Feedbacks, Materials,
    RescheduleRequests, AssignmentSubmissions, Assignments,
    StudentClasses, TutorClasses, BimbelRating
)

@admin.register(Users)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'username', 'email', 'role', 'date_joined',
        'reset_token', 'reset_token_created_at',
    )
    search_fields = ('username', 'email')
    list_filter = ('role',)
    ordering = ('-date_joined',)

@admin.register(SignupTokens)
class SignupTokenAdmin(admin.ModelAdmin):
    list_display = ('token', 'role', 'full_name', 'phone', 'is_used', 'created_at')
    list_filter = ('role', 'is_used')
    search_fields = ('token', 'full_name', 'phone')

@admin.register(Students)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'phone', 'user')
    search_fields = ('full_name', 'phone')

@admin.register(Tutors)
class TutorAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'expertise', 'phone', 'user')
    search_fields = ('full_name', 'expertise', 'phone')

@admin.register(Classes)
class ClassAdmin(admin.ModelAdmin):
    list_display = ('id', 'class_name', 'level', 'created_at')
    search_fields = ('class_name', 'level')

@admin.register(Schedules)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('id', 'class_field', 'tutor', 'status', 'schedule_date', 'start_time', 'end_time')
    list_filter = ('status', 'schedule_date')
    search_fields = ('class_field__class_name', 'tutor__full_name')

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('id', 'student', 'schedule', 'marked_by_tutor', 'confirmed_by_student', 'timestamp')
    list_filter = ('marked_by_tutor', 'confirmed_by_student')
    search_fields = ('student__full_name',)

@admin.register(Feedbacks)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('id', 'student', 'tutor', 'rating', 'created_at')
    list_filter = ('rating',)
    search_fields = ('student__full_name', 'tutor__full_name')
    
@admin.register(Materials)
class MaterialsAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'tutor', 'class_field', 'type', 'is_approved', 'uploaded_at')
    list_filter = ('is_approved', 'type')
    search_fields = ('title', 'tutor__full_name', 'class_field__class_name')

@admin.register(RescheduleRequests)
class RescheduleRequestsAdmin(admin.ModelAdmin):
    list_display = ('id', 'schedule', 'requested_by_tutor', 'status', 'requested_at')
    list_filter = ('status',)
    search_fields = ('requested_by_tutor__full_name',)

@admin.register(AssignmentSubmissions)
class AssignmentSubmissionsAdmin(admin.ModelAdmin):
    list_display = ('id', 'assignment', 'student', 'grade', 'submitted_at')
    list_filter = ('grade',)
    search_fields = ('student__full_name', 'assignment__title')

@admin.register(Assignments)
class AssignmentsAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'tutor', 'class_field', 'due_date', 'created_at')
    search_fields = ('title', 'tutor__full_name', 'class_field__class_name')

@admin.register(StudentClasses)
class StudentClassesAdmin(admin.ModelAdmin):
    list_display = ('id', 'student', 'class_field')
    search_fields = ('student__full_name', 'class_field__class_name')

@admin.register(TutorClasses)
class TutorClassesAdmin(admin.ModelAdmin):
    list_display = ('id', 'tutor', 'class_field')
    search_fields = ('tutor__full_name', 'class_field__class_name')

@admin.register(BimbelRating)
class BimbelRatingAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'tutor', 'professionalism', 'attendance',
        'subject_mastery', 'communication', 'created_at'
    )
    search_fields = ('tutor__full_name',)
    list_filter = ('created_at',)
