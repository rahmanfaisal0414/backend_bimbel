from django.db import models


class Attendance(models.Model):
    student = models.ForeignKey('Students', models.DO_NOTHING, blank=True, null=True)
    schedule = models.ForeignKey('Schedules', models.DO_NOTHING, blank=True, null=True)
    status = models.CharField(max_length=10, blank=True, null=True)
    timestamp = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'attendance'


class Classes(models.Model):
    class_name = models.CharField(max_length=50)
    level = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

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


class Schedules(models.Model):
    class_field = models.ForeignKey(Classes, models.DO_NOTHING, db_column='class_id', blank=True, null=True)  # Field renamed because it was a Python reserved word.
    tutor = models.ForeignKey('Tutors', models.DO_NOTHING, blank=True, null=True)
    subject = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, blank=True, null=True)
    start_time = models.TimeField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)
    schedule_date = models.DateField(blank=True, null=True)
    

    class Meta:
        managed = False
        db_table = 'schedules'


class SignupTokens(models.Model):
    token = models.CharField(unique=True, max_length=100)
    role = models.CharField(max_length=20)
    is_used = models.BooleanField(blank=True, null=True)
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
    full_name = models.CharField(max_length=100, blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    is_deleted = models.BooleanField(default=False)

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
    full_name = models.CharField(max_length=100, blank=True, null=True)
    subject_specialization = models.CharField(max_length=100, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        managed = False
        db_table = 'tutors'


class Users(models.Model):
    username = models.CharField(unique=True, max_length=50)
    email = models.CharField(unique=True, max_length=100)
    password = models.CharField(max_length=128)
    role = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    reset_token = models.CharField(max_length=6, blank=True, null=True)
    reset_token_created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'users'

        
