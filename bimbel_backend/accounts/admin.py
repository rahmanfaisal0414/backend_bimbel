from django.contrib import admin
from .models import Users, Students, Tutors, SignupTokens, Classes, Schedules, Attendance, Feedbacks

@admin.register(Users)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'username', 'email', 'role', 'created_at',
        'reset_token', 'reset_token_created_at',  # 👈 Tambahan
    )
    search_fields = ('username', 'email')
    list_filter = ('role',)
    ordering = ('-created_at',)

@admin.register(SignupTokens)
class SignupTokenAdmin(admin.ModelAdmin):
    list_display = ('token', 'role', 'is_used', 'created_at')
    list_filter = ('role', 'is_used')
    search_fields = ('token',)

@admin.register(Students)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'phone_number', 'user')
    search_fields = ('full_name',)

@admin.register(Tutors)
class TutorAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'subject_specialization', 'phone_number', 'user')
    search_fields = ('full_name', 'subject_specialization')

@admin.register(Classes)
class ClassAdmin(admin.ModelAdmin):
    list_display = ('id', 'class_name', 'level', 'created_at')
    search_fields = ('class_name', 'level')

@admin.register(Schedules)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('id', 'subject', 'class_field', 'tutor', 'status', 'schedule_date')
    list_filter = ('status', 'schedule_date')
    search_fields = ('subject',)

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('id', 'student', 'schedule', 'status', 'timestamp')
    list_filter = ('status',)
    search_fields = ('student__full_name',)

@admin.register(Feedbacks)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('id', 'student', 'tutor', 'rating', 'created_at')
    list_filter = ('rating',)
    search_fields = ('student__full_name', 'tutor__full_name')
