# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class AssignmentSubmissions(models.Model):
    assignment = models.ForeignKey('Assignments', models.DO_NOTHING, blank=True, null=True)
    student = models.ForeignKey('Students', models.DO_NOTHING, blank=True, null=True)
    file_url = models.TextField(blank=True, null=True)
    grade = models.IntegerField(blank=True, null=True)
    feedback = models.TextField(blank=True, null=True)
    submitted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'assignment_submissions'


class Assignments(models.Model):
    class_field = models.ForeignKey('Classes', models.DO_NOTHING, db_column='class_id', blank=True, null=True)  # Field renamed because it was a Python reserved word.
    tutor = models.ForeignKey('Tutors', models.DO_NOTHING, blank=True, null=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    due_date = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'assignments'


class Attendance(models.Model):
    student = models.ForeignKey('Students', models.DO_NOTHING, blank=True, null=True)
    schedule = models.ForeignKey('Schedules', models.DO_NOTHING, blank=True, null=True)
    marked_by_tutor = models.BooleanField(blank=True, null=True)
    confirmed_by_student = models.BooleanField(blank=True, null=True)
    timestamp = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'attendance'

class BimbelRating(models.Model):
    tutor = models.ForeignKey('Tutors', on_delete=models.CASCADE)
    professionalism = models.FloatField()  # etika, sopan santun
    attendance = models.FloatField()       # ketepatan waktu, hadir sesuai jadwal
    subject_mastery = models.FloatField()  # penguasaan materi
    communication = models.FloatField()    # cara menyampaikan materi ke murid
    admin_notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'bimbel_rating'


class Classes(models.Model):
    class_name = models.CharField(max_length=100)
    level = models.CharField(max_length=50, blank=True, null=True)
    capacity = models.IntegerField(default=30)
    current_student_count = models.IntegerField(default=0)
    is_deleted = models.BooleanField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'classes'


class Feedbacks(models.Model):
    student = models.ForeignKey('Students', models.DO_NOTHING, blank=True, null=True)
    tutor = models.ForeignKey('Tutors', models.DO_NOTHING, blank=True, null=True)
    rating = models.IntegerField(blank=True, null=True)
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'feedbacks'


class Materials(models.Model):
    class_field = models.ForeignKey(Classes, models.DO_NOTHING, db_column='class_id', blank=True, null=True)  # Field renamed because it was a Python reserved word.
    tutor = models.ForeignKey('Tutors', models.DO_NOTHING, blank=True, null=True)
    title = models.CharField(max_length=255)
    file_url = models.TextField(blank=True, null=True)
    type = models.CharField(max_length=50)
    is_approved = models.BooleanField(blank=True, null=True)
    uploaded_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'materials'


class RescheduleRequests(models.Model):
    schedule = models.ForeignKey('Schedules', models.DO_NOTHING, blank=True, null=True)
    requested_by_tutor = models.ForeignKey('Tutors', models.DO_NOTHING, blank=True, null=True)
    reason = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, blank=True, null=True)
    requested_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'reschedule_requests'


class Schedules(models.Model):
    class_field = models.ForeignKey(Classes, models.DO_NOTHING, db_column='class_id', blank=True, null=True)  # Field renamed because it was a Python reserved word.
    tutor = models.ForeignKey('Tutors', models.DO_NOTHING, blank=True, null=True)
    schedule_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(max_length=20)

    class Meta:
        managed = False
        db_table = 'schedules'


class SignupTokens(models.Model):
    token = models.CharField(unique=True, max_length=100)
    role = models.CharField(max_length=20)
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    class_field = models.ForeignKey('Classes', models.DO_NOTHING, db_column='class_field', blank=True, null=True)
    is_used = models.BooleanField(default=False)
    gender = models.CharField(max_length=10, blank=True, null=True)
    birthdate = models.DateField(blank=True, null=True)
    parent_contact = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'signup_tokens'


class StudentClasses(models.Model):
    student = models.ForeignKey('Students', models.DO_NOTHING, blank=True, null=True)
    class_field = models.ForeignKey(Classes, models.DO_NOTHING, db_column='class_id', blank=True, null=True)  # Field renamed because it was a Python reserved word.

    class Meta:
        managed = False
        db_table = 'student_classes'


class Students(models.Model):
    user = models.ForeignKey('Users', models.DO_NOTHING, blank=True, null=True)
    student_id = models.CharField(max_length=20, blank=True, null=True)
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    gender = models.CharField(max_length=10, blank=True, null=True)
    birthdate = models.DateField(blank=True, null=True)
    parent_contact = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'students'


class TutorClasses(models.Model):
    tutor = models.ForeignKey('Tutors', models.DO_NOTHING, blank=True, null=True)
    class_field = models.ForeignKey(Classes, models.DO_NOTHING, db_column='class_id', blank=True, null=True)  # Field renamed because it was a Python reserved word.

    class Meta:
        managed = False
        db_table = 'tutor_classes'


class Tutors(models.Model):
    user = models.ForeignKey('Users', models.DO_NOTHING, blank=True, null=True)
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, blank=True, null=True)
    expertise = models.CharField(max_length=255, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tutors'


class Users(models.Model):
    username = models.CharField(unique=True, max_length=150)
    email = models.CharField(unique=True, max_length=150)
    password = models.CharField(max_length=255)
    role = models.CharField(max_length=20)
    full_name = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(blank=True, null=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    reset_token = models.CharField(max_length=6, blank=True, null=True)
    reset_token_created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'users'
