import os
import uuid
import calendar
from datetime import date, datetime, timedelta
from collections import defaultdict

from django.db.models import Q, Avg
from django.core.files.storage import default_storage
from django.utils import timezone
from django.utils.timezone import localtime
from django.shortcuts import get_object_or_404
from django.contrib.auth.hashers import check_password, make_password

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser

from accounts.models import (
    Users,
    Students,
    Tutors,
    Classes,
    Schedules,
    Attendance,
    Feedbacks,
    SignupTokens,
    StudentClasses,
    AssignmentSubmissions,
    BimbelRating,
    Materials,
    Assignments,
    TutorClasses,
    TutorAvailability,
    AppSettings,
    RescheduleRequests,
    TutorExpertise,
    Subjects,
    ScheduleMaterials,
)

from .utils import get_schedule_status

from .serializers import (
    AdminStudentManagementSerializer,
    AdminStudentDetailSerializer,
    TutorListSerializer,
    AddClassSerializer,
    AddScheduleSerializer,
    MaterialListSerializer,
    ProfileUpdateSerializer,
)


class AdminDashboardView(APIView):
    def get(self, request):
        stats = {
            "Total Tutor": Tutors.objects.count(),
            "Total Student": Students.objects.count(),
            "Total Class": Classes.objects.count(),
        }

        today = date.today()
        schedules = Schedules.objects.select_related("tutor", "tutor__user").filter(schedule_date=today).order_by("start_time")

        schedule_data = []
        for sched in schedules:
            photo_url = "/media/profile/default-avatar.png"
            if sched.tutor and sched.tutor.user and sched.tutor.user.photo_url:
                photo_url = sched.tutor.user.photo_url

            schedule_data.append({
                "id": sched.id,
                "status": "OFFLINE" if sched.room else "ONLINE",
                "subject": ", ".join([
                    te.subject.name for te in TutorExpertise.objects.filter(tutor=sched.tutor)
                ]) if sched.tutor else "Unknown Subject",
                "tutor": sched.tutor.full_name if sched.tutor else "Unknown",
                "time": f"{sched.start_time.strftime('%H:%M')} – {sched.end_time.strftime('%H:%M')}",
                "photo_url": photo_url  
            })


        return Response({
            "stats": [{"label": k, "value": v} for k, v in stats.items()],
            "schedule": schedule_data
        }, status=status.HTTP_200_OK)

    def calculate_average_attendance(self):
        total = Attendance.objects.count()
        if total == 0:
            return "0%"
        present = Attendance.objects.filter(status="present").count()
        return f"{(present / total) * 100:.0f}%"
    
class SidebarUserInfoView(APIView):
    def get(self, request):
        user_id = request.query_params.get('user_id')

        if not user_id:
            return Response({'error': 'user_id diperlukan'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = Users.objects.get(id=user_id)

            return Response({
                'user_id': user.id,
                'username': user.username,
                'full_name':user.full_name,
                'email': user.email,
                'role': user.role,
                'photo_url': user.photo_url,
                'phone': user.phone,
                'address' : user.address,
                'date_joined': user.date_joined.isoformat() if user.date_joined else None,
                'bio': user.bio
            }, status=status.HTTP_200_OK)

        except Users.DoesNotExist:
            return Response({'error': 'User tidak ditemukan'}, status=status.HTTP_404_NOT_FOUND)
        
class GlobalSearchView(APIView):
    def get(self, request):
        query = request.query_params.get('q', '').strip().lower()

        if not query:
            return Response({'error': 'Query kosong'}, status=status.HTTP_400_BAD_REQUEST)

        # Cari tutor berdasarkan subject name
        subject_tutor_ids = TutorExpertise.objects.filter(
            subject__name__icontains=query
        ).values_list("tutor_id", flat=True)

        # Cari schedule berdasarkan tutor yang memiliki subject terkait
        subject_schedule_ids = TutorExpertise.objects.filter(
            subject__name__icontains=query
        ).values_list("tutor_id", flat=True)

        result = {
            'students': list(
                Students.objects.filter(
                    Q(full_name__icontains=query) |
                    Q(student_id__icontains=query)
                ).values('id', 'full_name', 'student_id')[:5]
            ),
            'tutors': [
                {
                    "id": tutor.id,
                    "full_name": tutor.full_name,
                    "expertise": ", ".join([
                        te.subject.name for te in TutorExpertise.objects.filter(tutor=tutor)
                    ])
                }
                for tutor in Tutors.objects.filter(
                    Q(full_name__icontains=query) |
                    Q(id__in=subject_tutor_ids)
                )[:5]
            ],
            'classes': list(
                Classes.objects.filter(
                    Q(class_name__icontains=query)
                ).values('id', 'class_name', 'level')[:5]
            ),
            'schedules': list(
                Schedules.objects.select_related('tutor', 'class_field').filter(
                    Q(tutor__full_name__icontains=query) |
                    Q(class_field__class_name__icontains=query) |
                    Q(room__icontains=query) |
                    Q(tutor__id__in=subject_schedule_ids)
                ).values(
                    'id',
                    'schedule_date',
                    'room',
                    'tutor__full_name'
                )[:5]
            ),
            'materials': list(
                Materials.objects.filter(
                    Q(title__icontains=query) |
                    Q(subject__icontains=query)
                ).values('id', 'title', 'subject')[:5]
            ),
        }

        return Response(result, status=200)
    
class AdminProfileView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response({'error': 'user_id diperlukan'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = Users.objects.get(id=user_id)
        except Users.DoesNotExist:
            return Response({'error': 'User tidak ditemukan'}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            'user_id': user.id,
            'username': user.username,
            'full_name': user.full_name,
            'email': user.email,
            'role': user.role,
            'photo_url': user.photo_url,
            'phone': user.phone,
            'address': user.address,
            'bio': user.bio,
            'date_joined': user.date_joined.isoformat() if user.date_joined else None,
        }, status=status.HTTP_200_OK)

    def put(self, request):
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response({'error': 'user_id diperlukan'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = Users.objects.get(id=user_id)
        except Users.DoesNotExist:
            return Response({'error': 'User tidak ditemukan'}, status=status.HTTP_404_NOT_FOUND)

        # Salin data dan hilangkan field yang tidak boleh diubah
        data = request.data.copy()
        for field in ['email', 'username', 'role', 'photo_url']:
            data.pop(field, None)

        # Upload dan simpan path foto secara manual
        file = request.FILES.get('photo_url')
        if file:
            filename = f'profile/user_{user.id}_{file.name}'
            path = default_storage.save(filename, file)
            user.photo_url = f'/media/{path}' 

        # Validasi data profil lainnya
        serializer = ProfileUpdateSerializer(user, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            user.save()  
            return Response({'message': 'Profil berhasil diperbarui'}, status=status.HTTP_200_OK)

        print("Serializer Errors:", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class ChangePasswordView(APIView):
    def put(self, request):
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response({'error': 'user_id diperlukan'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = Users.objects.get(id=user_id)
        except Users.DoesNotExist:
            return Response({'error': 'User tidak ditemukan'}, status=status.HTTP_404_NOT_FOUND)

        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')

        if not current_password or not new_password or not confirm_password:
            return Response({'error': 'Semua field harus diisi'}, status=400)

        if not check_password(current_password, user.password):
            return Response({'error': 'Password saat ini salah'}, status=400)

        if new_password != confirm_password:
            return Response({'error': 'Konfirmasi password tidak cocok'}, status=400)

        user.password = make_password(new_password)
        user.save()

        return Response({'message': 'Password berhasil diubah'}, status=200)
   
class AdminStudentManagementView(APIView):
    def get(self, request):
        search = request.query_params.get('search', '')
        filter_class = request.query_params.get('filter_class', '')
        page = int(request.query_params.get('page', 1))
        per_page = 10

        students_qs = Students.objects.select_related('user').all()

        if search:
            students_qs = students_qs.filter(full_name__icontains=search)

        if filter_class:
            students_qs = students_qs.filter(studentclasses__class_field__class_name=filter_class)

        total_students = students_qs.count()

        start = (page - 1) * per_page
        end = page * per_page
        students_paginated = students_qs[start:end]

        serializer = AdminStudentManagementSerializer(students_paginated, many=True)

        # Olah data di sini
        student_data = []
        for student in serializer.data:
            student_instance = Students.objects.get(id=student['id'])
            user = student_instance.user

            student_class = "N/A"
            student_class_instance = StudentClasses.objects.filter(student=student_instance).order_by('-id').first()
            if student_class_instance:
                student_class = student_class_instance.class_field.class_name

            # Get status
            status_text = "Inactive"
            if user:
                status_text = "Active" if user.is_active else "Inactive"

            # Get attendance
            attendances = Attendance.objects.filter(student=student_instance)
            avg_attendance = "0%"
            if attendances.exists():
                present_count = attendances.filter(confirmed_by_student=True).count()
                avg_attendance = f"{(present_count / attendances.count()) * 100:.0f}%"

            student_data.append({
                'id': student['id'],
                'student_id': f"S{str(student['id']).zfill(3)}",
                'full_name': student['full_name'],
                'class_name': student_class,
                'status': status_text,
                'attendance': avg_attendance,
            })

        return Response({
            'students': student_data,
            'total': total_students
        }, status=status.HTTP_200_OK)
        
class ClassListView(APIView):
    def get(self, request):
        classes = Classes.objects.filter(is_deleted=False)
        data = [
            {
                "id": cls.id,
                "class_name": cls.class_name,
                "capacity": cls.capacity,
                "current_student_count": cls.current_student_count
            }
            for cls in classes
        ]
        return Response(data, status=status.HTTP_200_OK)

class AdminStudentDetailView(APIView):
    def get(self, request, student_id):
        try:
            student = Students.objects.select_related('user').get(id=student_id)
            user = student.user

            # Kelas aktif saat ini
            current_class = StudentClasses.objects.filter(student=student).order_by('-id').first()
            current_class_name = current_class.class_field.class_name if current_class else "N/A"
            class_level = current_class.class_field.level if current_class else "N/A"

            # Riwayat kelas
            class_history_qs = StudentClasses.objects.filter(student=student).select_related('class_field').order_by('id')
            class_history = [
                {
                    "class_name": c.class_field.class_name,
                    "moved_at": c.class_field.created_at.strftime('%Y-%m-%d') if c.class_field.created_at else "-"
                }
                for c in class_history_qs
            ]

            # Attendance
            attendance_qs = Attendance.objects.filter(student=student)
            present_count = attendance_qs.filter(confirmed_by_student=True).count()
            total_meetings = attendance_qs.count()
            attendance_percent = f"{(present_count / total_meetings) * 100:.0f}%" if total_meetings else "0%"

            attendance_history = [
                {
                    "date": att.timestamp.strftime('%Y-%m-%d') if att.timestamp else "-",
                    "status": "Present" if att.confirmed_by_student else "Absent"
                }
                for att in attendance_qs.order_by('-timestamp')[:10]
            ]

            # Assignment grades
            submissions = AssignmentSubmissions.objects.filter(student=student).select_related('assignment')
            assignments = [
                {
                    "title": sub.assignment.title if sub.assignment else "Unknown",
                    "grade": sub.grade or 0,
                    "feedback": sub.feedback or "-"
                }
                for sub in submissions
            ]

            return Response({
                "full_name": student.full_name,
                "student_id": f"{str(student.student_id).zfill(3)}",
                "email": user.email if user else "-",
                "phone": student.phone,
                "address": student.address,
                "gender": student.gender or "-",
                "birthdate": student.birthdate.strftime('%Y-%m-%d') if student.birthdate else "-",
                "parent_contact": student.parent_contact or "-",
                "class_name": current_class_name,
                "class_level": class_level,
                "status": "Active" if user.is_active else "Inactive" if user else "Unknown",
                "attendance": attendance_percent,
                "total_meetings": total_meetings,
                "present_count": present_count,
                "assignments": assignments,
                "attendance_history": attendance_history,
                "class_history": class_history,
            }, status=status.HTTP_200_OK)

        except Students.DoesNotExist:
            return Response({"error": "Student not found"}, status=status.HTTP_404_NOT_FOUND)
        
class AdminTokenListView(APIView):
    def get(self, request):
        tokens = SignupTokens.objects.select_related('class_field').order_by('-id')
        data = [
            {
                "id": token.id,
                "token": token.token,
                "role": token.role.capitalize(),
                "full_name": token.full_name,
                "phone": token.phone,
                "address": token.address,
                "gender": token.gender or "-",
                "birthdate": token.birthdate.strftime('%Y-%m-%d') if token.birthdate else "-",
                "class_name": token.class_field.class_name if token.class_field else "-",
                "is_used": token.is_used,
            }
            for token in tokens
        ]
        return Response({"tokens": data}, status=status.HTTP_200_OK)

class AdminUpdateStudentView(APIView):
    parser_classes = [JSONParser]

    def put(self, request, student_id):
        try:
            student = Students.objects.get(id=student_id)
            user = student.user
        except Students.DoesNotExist:
            return Response({"error": "Student not found"}, status=status.HTTP_404_NOT_FOUND)

        data = request.data

        # Update user (tanpa email)
        user.full_name = data.get("full_name", user.full_name)
        user.save()

        # Update student table
        student.full_name = data.get("full_name", student.full_name)
        student.phone = data.get("phone", student.phone)
        student.address = data.get("address", student.address)
        student.gender = data.get("gender", student.gender)
        student.birthdate = data.get("birthdate", student.birthdate)
        student.parent_contact = data.get("parent_contact", student.parent_contact)
        student.save()

        new_class_id = data.get("class_id")
        if new_class_id:
            try:
                new_class = Classes.objects.get(id=new_class_id)
            except Classes.DoesNotExist:
                return Response({"error": "Class not found"}, status=status.HTTP_404_NOT_FOUND)

            existing = StudentClasses.objects.filter(student=student, class_field=new_class).exists()
            if not existing:
                last_class_rel = StudentClasses.objects.filter(student=student).order_by("-id").first()
                if last_class_rel:
                    last_class = last_class_rel.class_field
                    last_class.current_student_count = max(0, last_class.current_student_count - 1)
                    last_class.save()

                if new_class.current_student_count < new_class.capacity:
                    StudentClasses.objects.create(student=student, class_field=new_class)
                    new_class.current_student_count += 1
                    new_class.save()
                else:
                    return Response({"error": "Class is already full"}, status=400)

        return Response({"message": "Student updated successfully."}, status=200)
    
class ChangeStudentClassView(APIView):
    parser_classes = [JSONParser]

    def post(self, request, student_id):
        class_id = request.data.get("class_id")
        if not class_id:
            return Response({"error": "class_id dibutuhkan"}, status=400)

        try:
            student = Students.objects.get(id=student_id)
            new_class = Classes.objects.get(id=class_id)

            if StudentClasses.objects.filter(student=student, class_field=new_class).exists():
                return Response({"error": "Siswa sudah berada di kelas tersebut"}, status=400)

            last_class_rel = StudentClasses.objects.filter(student=student).order_by("-id").first()
            if last_class_rel:
                last_class = last_class_rel.class_field
                last_class.current_student_count = max(0, last_class.current_student_count - 1)
                last_class.save()

            if new_class.current_student_count >= new_class.capacity:
                return Response({"error": "Kelas penuh"}, status=400)

            StudentClasses.objects.create(student=student, class_field=new_class)
            new_class.current_student_count += 1
            new_class.save()

            return Response({"message": "Kelas siswa berhasil diganti"}, status=200)
        except Students.DoesNotExist:
            return Response({"error": "Siswa tidak ditemukan"}, status=404)
        except Classes.DoesNotExist:
            return Response({"error": "Kelas tidak ditemukan"}, status=404)
        
class DeactivateStudentAccountView(APIView):
    def post(self, request, student_id):
        try:
            student = Students.objects.get(id=student_id)
            user = student.user
            user.is_active = not user.is_active  
            user.save()

            if user.is_active:
                message = "Akun siswa berhasil diaktifkan"
            else:
                message = "Akun siswa berhasil dinonaktifkan"

            return Response({"message": message, "new_status": "Active" if user.is_active else "Inactive"}, status=200)
        except Students.DoesNotExist:
            return Response({"error": "Siswa tidak ditemukan"}, status=404)

class TutorListView(APIView):
    def get(self, request):
        search = request.query_params.get('search', '')
        subject = request.query_params.get('filter_subject', '')

        queryset = Tutors.objects.select_related('user').all()

        if search:
            queryset = queryset.filter(full_name__icontains=search)
        if subject:
            tutor_ids = TutorExpertise.objects.filter(
                subject__name__iexact=subject
            ).values_list("tutor_id", flat=True)
            queryset = queryset.filter(id__in=tutor_ids)

        # Availability mapping
        availability_qs = TutorAvailability.objects.select_related('tutor').all()
        availability_map = defaultdict(list)
        for a in availability_qs:
            waktu = f"{a.day_of_week} ({a.start_time.strftime('%H:%M')}–{a.end_time.strftime('%H:%M')})"
            availability_map[a.tutor_id].append(waktu)

        response_data = []
        for tutor in queryset:
            tutor_id = f"G{tutor.id:03d}"

            # Feedback rating dari siswa
            feedbacks = Feedbacks.objects.filter(tutor=tutor).values_list('rating', flat=True)
            feedback_avg = round(sum(feedbacks) / len(feedbacks), 1) if feedbacks else None

            # Attendance Score
            total_schedule = Schedules.objects.filter(tutor=tutor).count()
            attended = Attendance.objects.filter(schedule__tutor=tutor, marked_by_tutor=True).count()
            attendance_score = (attended / total_schedule) * 100 if total_schedule > 0 else 0

            # Subject Mastery Score
            materials = Materials.objects.filter(tutor=tutor)
            total_material = materials.count()
            approved_material = materials.filter(is_approved=True).count()
            subject_score = (approved_material / total_material) * 100 if total_material > 0 else 0

            # Nilai maksimum dari masing-masing komponen
            PROFILE_MAX = 60
            FEEDBACK_MAX = 40

            # Hitung kelengkapan profil (maks 3 field)
            has_expertise = TutorExpertise.objects.filter(tutor=tutor).exists()
            profile_fields = [
                bool(tutor.phone),
                bool(tutor.address),
                has_expertise,
            ]

            profile_score = (sum(profile_fields) / 3) * PROFILE_MAX  # Skor proporsional

            # Hitung feedback score (misalnya 4 feedback = 4 * 10, maksimal 40)
            feedback_score = min(len(feedbacks) * 10, FEEDBACK_MAX)

            # Gabungan skor professionalism
            professionalism_score = round(profile_score + feedback_score, 1)


            # Admin rating kalkulasi otomatis
            raw_admin_score = (attendance_score + subject_score + professionalism_score) / 3
            admin_avg = round((raw_admin_score / 100) * 5, 1)

            # Final rating gabungan 70:30
            final_rating = None
            if admin_avg and feedback_avg:
                final_rating = round(admin_avg * 0.7 + feedback_avg * 0.3, 1)
            elif admin_avg:
                final_rating = admin_avg
            elif feedback_avg:
                final_rating = feedback_avg

            response_data.append({
                "id": tutor.id,
                "full_name": tutor.full_name,
                "tutor_id": tutor_id,
                "subject": ", ".join([
                    te.subject.name for te in TutorExpertise.objects.filter(tutor=tutor)
                ]) or "-",
                "rating": final_rating,
                "status": "Active" if tutor.user and tutor.user.is_active else "Inactive",
                "availability": ", ".join(availability_map.get(tutor.id, ["-"]))
            })

        return Response({
            "tutors": response_data,
            "total": queryset.count()
        }, status=status.HTTP_200_OK)

class SubjectListView(APIView):
    def get(self, request):
        subjects = Subjects.objects.all().order_by("name")
        subject_data = [{"id": subject.id, "name": subject.name} for subject in subjects]
        return Response(subject_data, status=status.HTTP_200_OK)
    
class TutorDetailView(APIView):
    def get(self, request, tutor_id):
        try:
            tutor = Tutors.objects.select_related("user").get(id=tutor_id)
        except Tutors.DoesNotExist:
            return Response({"error": "Tutor not found"}, status=404)

        user = tutor.user

        # Kelas
        class_qs = TutorClasses.objects.filter(tutor=tutor).select_related("class_field")
        class_data = [
            {
                "class_name": c.class_field.class_name,
                "level": c.class_field.level,
                "student_count": c.class_field.current_student_count,
            }
            for c in class_qs if c.class_field
        ]

        # Tugas
        assignment_qs = Assignments.objects.filter(tutor=tutor)
        assignments = assignment_qs.values("title", "due_date")

        # Materi
        material_qs = Materials.objects.filter(tutor=tutor)
        materials = material_qs.values("title", "type", "uploaded_at", "is_approved")

        # Feedback siswa
        feedback_qs = Feedbacks.objects.filter(tutor=tutor,is_approved=True)
        feedbacks = feedback_qs.values("rating", "comment")
        student_avg = feedback_qs.aggregate(avg=Avg("rating"))["avg"] or 0

        # Availability
        availability_qs = TutorAvailability.objects.filter(tutor=tutor)
        availability_str = ", ".join([
            f"{a.day_of_week} ({a.start_time.strftime('%H:%M')}–{a.end_time.strftime('%H:%M')})"
            for a in availability_qs
        ]) if availability_qs.exists() else "-"

        # Rating admin berbasis sistem
        total_schedule = Schedules.objects.filter(tutor=tutor).count()
        attended = Attendance.objects.filter(schedule__tutor=tutor, marked_by_tutor=True).count()
        attendance_score = (attended / total_schedule) * 100 if total_schedule > 0 else 0

        total_material = material_qs.count()
        approved_material = material_qs.filter(is_approved=True).count()
        subject_score = (approved_material / total_material) * 100 if total_material > 0 else 0

        # Nilai maksimum dari masing-masing komponen
        PROFILE_MAX = 60
        FEEDBACK_MAX = 40

        # Hitung kelengkapan profil (maks 3 field)
        has_expertise = TutorExpertise.objects.filter(tutor=tutor).exists()
        profile_fields = [
            bool(tutor.phone),
            bool(tutor.address),
            has_expertise,
        ]

        profile_score = (sum(profile_fields) / 3) * PROFILE_MAX  # Skor proporsional

        # Hitung feedback score (misalnya 4 feedback = 4 * 10, maksimal 40)
        feedback_score = min(len(feedbacks) * 10, FEEDBACK_MAX)

        # Gabungan skor professionalism
        professionalism_score = round(profile_score + feedback_score, 1)

        raw_admin_score = round((attendance_score + subject_score + professionalism_score) / 3, 1)
        admin_avg = round((raw_admin_score / 100) * 5, 1)

        final_rating = round(admin_avg * 0.7 + student_avg * 0.3, 1)

        return Response({
            "full_name": tutor.full_name,
            "tutor_id": f"G{tutor.id:03d}",
            "email": user.email,
            "phone": tutor.phone,
            "address": tutor.address,
            "expertise": [
                te.subject.name for te in TutorExpertise.objects.filter(tutor=tutor)
            ],
            "status": "Active" if user.is_active else "Inactive",
            "joined_at": user.date_joined.isoformat(),
            "availability": availability_str,
            "classes": list(class_data),
            "assignments": list(assignments),
            "materials": list(materials),
            "feedbacks": list(feedbacks),
            "rating": final_rating,
            "rating_breakdown": {
                "admin": admin_avg,
                "student": round(student_avg, 1),
                "attendance_score": round(attendance_score, 1),
                "subject_mastery_score": round(subject_score, 1),
                "professionalism_score": round(professionalism_score, 1),
                "admin_raw_score": raw_admin_score
            }
        })
        
class UpdateTutorView(APIView):
    def put(self, request, tutor_id):
        try:
            tutor = Tutors.objects.select_related("user").get(id=tutor_id)
        except Tutors.DoesNotExist:
            return Response({"error": "Tutor not found"}, status=404)

        data = request.data
        full_name = data.get("full_name")
        phone = data.get("phone")
        address = data.get("address")
        expertise_list = data.get("expertise", [])  # Expecting list

        if not full_name:
            return Response({"error": "Full name is required"}, status=400)

        tutor.full_name = full_name
        tutor.phone = phone
        tutor.address = address
        tutor.save()

        if tutor.user:
            tutor.user.full_name = full_name
            tutor.user.save()

        # ✅ Update TutorExpertise
        TutorExpertise.objects.filter(tutor=tutor).delete()
        for subject_name in expertise_list:
            try:
                subject = Subjects.objects.get(name__iexact=subject_name)
                TutorExpertise.objects.create(tutor=tutor, subject=subject)
            except Subjects.DoesNotExist:
                continue

        return Response({"message": "Tutor updated successfully"}, status=200)
    
class ToggleTutorAccountView(APIView):
    def post(self, request, tutor_id):
        try:
            tutor = Tutors.objects.select_related("user").get(id=tutor_id)
            user = tutor.user
            user.is_active = not user.is_active  
            user.save()

            message = (
                "Akun tutor berhasil diaktifkan"
                if user.is_active else
                "Akun tutor berhasil dinonaktifkan"
            )

            return Response({
                "message": message,
                "new_status": "Active" if user.is_active else "Inactive"
            }, status=200)

        except Tutors.DoesNotExist:
            return Response({"error": "Tutor tidak ditemukan"}, status=404)
        
class ClassManagementListView(APIView):
    def get(self, request):
        schedules = Schedules.objects.select_related("class_field", "tutor").all()

        result = []
        for schedule in schedules:
            class_obj = schedule.class_field
            tutor_obj = schedule.tutor

            result.append({
                "id": schedule.id, 
                "className": class_obj.class_name if class_obj else "Unknown Class",
                "subject": schedule.subject.name if schedule.subject else "Unknown Subject",
                "tutor": tutor_obj.full_name if tutor_obj else "Unknown Tutor",
                "time": f"{schedule.schedule_date.strftime('%A')}, {schedule.start_time.strftime('%H:%M')}–{schedule.end_time.strftime('%H:%M')}",
                "room": schedule.room if hasattr(schedule, "room") else None,
                "mode": "Offline" if schedule.room else "Online",
                "status": get_schedule_status(schedule),

            })

        return Response(result, status=status.HTTP_200_OK)
    
class AddClassView(APIView):
    def post(self, request):
        serializer = AddClassSerializer(data=request.data)

        if not request.data.get("class_name"):
            return Response({"error": "Class name is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            capacity = int(request.data.get("capacity", 30))
            if capacity < 1:
                return Response({"error": "Capacity must be at least 1."}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
            return Response({"error": "Capacity must be a number."}, status=status.HTTP_400_BAD_REQUEST)

        if serializer.is_valid():
            try:
                class_instance = Classes.objects.create(
                    class_name=serializer.validated_data["class_name"].strip(),
                    level=serializer.validated_data.get("level", None),
                    capacity=serializer.validated_data.get("capacity", 30),
                    current_student_count=0,
                    is_deleted=False,
                    created_at=timezone.now()
                )
                return Response({"message": "Class successfully created.", "id": class_instance.id}, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
class AddScheduleView(APIView):
    def post(self, request):
        data = request.data

        # Field yang wajib dikirim (kecuali room)
        required_fields = [
            "class_name", "subject", "tutor", "mode",
            "start_time", "end_time", "schedule_date"
        ]

        if not all(data.get(field) for field in required_fields):
            return Response({"error": "Semua field wajib diisi kecuali room."}, status=400)

        # Validasi format tanggal
        try:
            schedule_date = datetime.strptime(data["schedule_date"], "%Y-%m-%d").date()
        except ValueError:
            return Response({"error": "Format tanggal tidak valid (gunakan YYYY-MM-DD)."}, status=400)

        # Ambil kelas
        try:
            class_obj = Classes.objects.get(class_name=data["class_name"])
        except Classes.DoesNotExist:
            return Response({"error": "Kelas tidak ditemukan."}, status=404)
        
        try:
            subject_obj = Subjects.objects.get(name__iexact=data["subject"])
        except Subjects.DoesNotExist:
            return Response({"error": "Subject tidak ditemukan."}, status=404)

        # Ambil tutor
        try:
            tutor_ids = TutorExpertise.objects.filter(
                subject__name__iexact=data["subject"]
            ).values_list("tutor_id", flat=True)

            tutor_obj = Tutors.objects.filter(
                id__in=tutor_ids, full_name=data["tutor"]
            ).first()

            if not tutor_obj:
                return Response({"error": "Tutor dengan nama dan subject tersebut tidak ditemukan."}, status=404)

        except Tutors.DoesNotExist:
            return Response({"error": "Tutor dengan nama dan subject tersebut tidak ditemukan."}, status=404)

        # Validasi waktu
        try:
            start_time = datetime.strptime(data["start_time"], "%H:%M").time()
            end_time = datetime.strptime(data["end_time"], "%H:%M").time()
        except ValueError:
            return Response({"error": "Format jam tidak valid (gunakan HH:MM)."}, status=400)

        if start_time >= end_time:
            return Response({"error": "Jam mulai harus lebih awal dari jam selesai."}, status=400)

        # Cek jadwal bentrok untuk tutor
        conflicts = Schedules.objects.filter(
            tutor=tutor_obj,
            schedule_date=schedule_date,
            start_time__lt=end_time,
            end_time__gt=start_time
        )
        if conflicts.exists():
            return Response({"error": "Jadwal tutor bentrok dengan jadwal lain."}, status=400)

        try:
            new_schedule = Schedules.objects.create(
                class_field=class_obj,
                tutor=tutor_obj,
                subject=subject_obj,
                schedule_date=schedule_date,
                start_time=start_time,
                end_time=end_time,
                status = data.get("status", "upcoming"),
                room=data.get("room") if data["mode"] == "Offline" else None
            )

            if not TutorClasses.objects.filter(tutor=tutor_obj, class_field=class_obj).exists():
                TutorClasses.objects.create(tutor=tutor_obj, class_field=class_obj)

            return Response({"message": "Jadwal berhasil ditambahkan", "id": new_schedule.id}, status=201)

        except Exception as e:
            return Response({"error": str(e)}, status=500)
        
class AvailableTutorsView(APIView):
    def get(self, request):
        date_str = request.GET.get("date")
        start_time_str = request.GET.get("start_time")
        end_time_str = request.GET.get("end_time")
        subject = request.GET.get("subject")

        if not (date_str and start_time_str and end_time_str and subject):
            return Response({"error": "Semua parameter harus dikirim"}, status=400)

        try:
            schedule_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            start_time = datetime.strptime(start_time_str, "%H:%M").time()
            end_time = datetime.strptime(end_time_str, "%H:%M").time()
        except ValueError:
            return Response({"error": "Format tanggal/jam tidak valid"}, status=400)

        day_map = {
            "Monday": "Senin",
            "Tuesday": "Selasa",
            "Wednesday": "Rabu",
            "Thursday": "Kamis",
            "Friday": "Jumat",
            "Saturday": "Sabtu",
            "Sunday": "Minggu"
        }
        day_of_week = day_map[schedule_date.strftime('%A')]

        # Ambil semua tutor yang memiliki subject tersebut
        subject_tutor_ids = TutorExpertise.objects.filter(
            subject__name__iexact=subject
        ).values_list("tutor_id", flat=True)

        # Filter tutor yang punya availability sesuai hari dan jam serta subject
        available_tutors = TutorAvailability.objects.filter(
            day_of_week=day_of_week,
            start_time__lte=start_time,
            end_time__gte=end_time,
            tutor_id__in=subject_tutor_ids
        ).select_related('tutor')

        response = []
        for avail in available_tutors:
            tutor = avail.tutor

            # Pastikan tidak bentrok dengan jadwal yang sudah ada
            conflict = Schedules.objects.filter(
                tutor=tutor,
                schedule_date=schedule_date,
                start_time__lt=end_time,
                end_time__gt=start_time
            ).exists()

            if not conflict:
                response.append({
                    "id": tutor.id,
                    "full_name": tutor.full_name,
                })

        return Response({"tutors": response}, status=200)
    
class ScheduleDetailView(APIView):
    def get(self, request, schedule_id):
        schedule = get_object_or_404(Schedules.objects.select_related(
            'class_field', 'tutor'
        ), id=schedule_id)

        class_data = schedule.class_field
        class_name = class_data.class_name
        level = class_data.level
        capacity = class_data.capacity
        current_count = class_data.current_student_count

        tutor_name = schedule.tutor.full_name if schedule.tutor else "-"
        subject = schedule.subject.name if schedule.subject else "-"

        student_qs = StudentClasses.objects.filter(class_field=class_data).select_related('student')
        student_names = [sc.student.full_name for sc in student_qs if sc.student]
        
        reschedule_qs = RescheduleRequests.objects.filter(schedule=schedule, status="Approved").order_by('-requested_at').first()
        reschedule_info = {
            "reason": reschedule_qs.reason,
            "requested_by": reschedule_qs.requested_by_tutor.full_name,
            "requested_at": reschedule_qs.requested_at.isoformat(),
        } if reschedule_qs else None


        # ✅ Materi yang dipilih tutor untuk jadwal ini
        linked_materials = ScheduleMaterials.objects.filter(schedule=schedule).select_related("material")

        materials = [
            {
                "title": sm.material.title,
                "type": sm.material.type,
                "uploaded_at": sm.material.uploaded_at.strftime("%Y-%m-%d %H:%M") if sm.material.uploaded_at else None
            }
            for sm in linked_materials if sm.material
        ]

        return Response({
            "class_name": class_name,
            "level": level,
            "capacity": capacity,
            "current_student_count": current_count,
            "tutor_name": tutor_name,
            "subject": subject,
            "schedule_date": schedule.schedule_date.isoformat(),
            "start_time": schedule.start_time.strftime("%H:%M"),
            "end_time": schedule.end_time.strftime("%H:%M"),
            "room": schedule.room,
            "reschedule_info": reschedule_info,
            "mode": "Offline" if schedule.room else "Online",
            "status": get_schedule_status(schedule),
            "students": student_names,
            "materials": materials,  
        }, status=status.HTTP_200_OK)
        
class EditScheduleView(APIView):
    def put(self, request, schedule_id):
        data = request.data

        # Cek field wajib
        required_fields = [
            "class_name", "subject", "tutor", "mode", "status",
            "start_time", "end_time", "schedule_date"
        ]
        if not all(data.get(field) for field in required_fields):
            return Response({"error": "Semua field wajib diisi kecuali room."}, status=400)

        try:
            schedule = Schedules.objects.get(id=schedule_id)
        except Schedules.DoesNotExist:
            return Response({"error": "Jadwal tidak ditemukan."}, status=404)

        # Validasi waktu & tanggal
        try:
            schedule_date = datetime.strptime(data["schedule_date"], "%Y-%m-%d").date()
            start_time = datetime.strptime(data["start_time"], "%H:%M").time()
            end_time = datetime.strptime(data["end_time"], "%H:%M").time()
        except ValueError:
            return Response({"error": "Format tanggal atau jam tidak valid."}, status=400)

        if start_time >= end_time:
            return Response({"error": "Jam mulai harus lebih awal dari jam selesai."}, status=400)

        # Ambil relasi
        try:
            class_obj = Classes.objects.get(class_name=data["class_name"])
            subject_obj = Subjects.objects.get(id=data["subject"]) 
            tutor_ids = TutorExpertise.objects.filter(subject=subject_obj).values_list("tutor_id", flat=True)

            tutor_obj = Tutors.objects.filter(
                id__in=tutor_ids, full_name=data["tutor"]
            ).first()

            if not tutor_obj:
                return Response({"error": "Tutor dengan nama dan subject tersebut tidak ditemukan."}, status=404)

        except (Classes.DoesNotExist, Tutors.DoesNotExist, Subjects.DoesNotExist):
            return Response({"error": "Kelas, subject, atau tutor tidak valid."}, status=404)

        # Cek bentrok
        conflict = Schedules.objects.exclude(id=schedule_id).filter(
            tutor=tutor_obj,
            schedule_date=schedule_date,
            start_time__lt=end_time,
            end_time__gt=start_time
        ).exists()
        if conflict:
            return Response({"error": "Jadwal tutor bentrok dengan jadwal lain."}, status=400)

        # Update semua field
        schedule.class_field = class_obj
        schedule.tutor = tutor_obj
        schedule.schedule_date = schedule_date
        schedule.start_time = start_time
        schedule.end_time = end_time
        schedule.room = data.get("room") if data["mode"] == "Offline" else None
        schedule.status = data["status"]
        schedule.subject = subject_obj  
        schedule.save()

        return Response({"message": "Jadwal berhasil diperbarui."}, status=200)

    
class CancelScheduleView(APIView):
    def post(self, request, schedule_id):
        try:
            schedule = Schedules.objects.get(id=schedule_id)
        except Schedules.DoesNotExist:
            return Response({"error": "Jadwal tidak ditemukan."}, status=404)

        if schedule.status == "Canceled":
            return Response({"message": "Jadwal sudah dibatalkan sebelumnya."}, status=200)

        schedule.status = "Canceled"
        schedule.save()

        return Response({"message": "Jadwal berhasil dibatalkan."}, status=200)

class LearningMaterialListView(APIView):
    def get(self, request):
        search = request.query_params.get('search', '')
        filter_subject = request.query_params.get('filter_subject', '')

        queryset = Materials.objects.select_related('tutor', 'class_field')

        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(subject__icontains=search)
            )
        if filter_subject:
            queryset = queryset.filter(subject=filter_subject)

        raw_data = MaterialListSerializer(queryset, many=True).data

        transformed_data = []
        for item in raw_data:
            class_name = item["class_field"]
            if isinstance(class_name, dict):
                class_name = class_name.get("class_name", "-")
            
            transformed_data.append({
                "id": item["id"],
                "title": item["title"],
                "subject": item.get("subject", "-"),
                "classRange": class_name,
                "status": "Published" if item["is_approved"] else "Draft",  
                "uploadedBy": "tutor" if item["tutor"] else "Admin",
            })

        total = len(transformed_data)
        published = sum(1 for item in transformed_data if item["status"] == "Published")
        draft = sum(1 for item in transformed_data if item["status"] == "Draft")

        unique_subjects = (
            Materials.objects
            .exclude(subject__isnull=True)
            .exclude(subject__exact="")
            .values_list('subject', flat=True)
            .distinct()
        )

        return Response({
            "materials": transformed_data,
            "stats": {
                "total": total,
                "published": published,
                "draft": draft
            },
            "all_subjects": list(unique_subjects)
        })
        
class AddMaterialView(APIView):
    def post(self, request):
        title = request.data.get("title", "").strip()
        class_id = request.data.get("class_id")
        material_type = request.data.get("type", "").strip()
        is_approved = request.data.get("is_approved") == "true"
        uploaded_file = request.FILES.get("file")
        subject = request.data.get("subject", "").strip()

        if not title or not class_id or not material_type or not uploaded_file:
            return Response({"error": "Semua field wajib diisi."}, status=400)
        if not subject:
            return Response({"error": "Subject wajib diisi."}, status=400)

        try:
            class_obj = Classes.objects.get(id=class_id)
        except Classes.DoesNotExist:
            return Response({"error": "Kelas tidak ditemukan."}, status=404)

        # Ambil setting dari app_settings
        size_setting = AppSettings.objects.filter(key="max_material_file_size_mb").first()
        types_setting = AppSettings.objects.filter(key="allowed_material_types").first()

        max_mb = int(size_setting.value) if size_setting else 50
        allowed_types = types_setting.value.split(",") if types_setting else ["pdf", "mp4", "docx"]

        ext = os.path.splitext(uploaded_file.name)[1][1:].lower()
        size_mb = uploaded_file.size / (1024 * 1024)

        if ext not in allowed_types:
            return Response({"error": f"Tipe file .{ext} tidak diizinkan. Diizinkan: {', '.join(allowed_types)}"}, status=400)

        if size_mb > max_mb:
            return Response({"error": f"Ukuran file melebihi batas {max_mb} MB"}, status=400)

        # Simpan file
        unique_name = f"{uuid.uuid4().hex}.{ext}"
        saved_path = default_storage.save(f"material/{unique_name}", uploaded_file)

        Materials.objects.create(
            title=title,
            class_field=class_obj,
            type=material_type,
            file_url=saved_path,
            is_approved=is_approved,
            tutor=None,
            subject=subject,
            uploaded_at=timezone.now()
        )

        return Response({"message": "Materi berhasil ditambahkan."}, status=201)

class MaterialDetailView(APIView):
    def get(self, request, material_id):
        material = get_object_or_404(Materials.objects.select_related("class_field", "tutor"), id=material_id)

        return Response({
            "id": material.id,
            "title": material.title,
            "type": material.type,
            "subject": material.subject,
            "class_name": material.class_field.class_name if material.class_field else "-",
            "is_approved": material.is_approved,
            "class_id": material.class_field.id if material.class_field else None,"class_id": material.class_field.id if material.class_field else None,
            "uploaded_at": material.uploaded_at.isoformat() if material.uploaded_at else "",
            "uploaded_by": material.tutor.full_name if material.tutor else "Admin",
            "file_url": material.file_url,
        }, status=status.HTTP_200_OK)
        
class DeleteMaterialView(APIView):
    def delete(self, request, material_id):
        material = get_object_or_404(Materials, id=material_id)
        file_path = material.file_url

        # Hapus file dari storage
        if file_path and default_storage.exists(file_path):
            default_storage.delete(file_path)

        material.delete()
        return Response({"message": "Materi berhasil dihapus."}, status=200)
    
class EditMaterialView(APIView):
    def put(self, request, material_id):
        try:
            material = Materials.objects.get(id=material_id)
        except Materials.DoesNotExist:
            return Response({"error": "Materi tidak ditemukan."}, status=404)

        title = request.data.get("title", "").strip()
        material_type = request.data.get("type", "").strip()
        subject = request.data.get("subject", "").strip()
        class_id = request.data.get("class_id")
        is_approved = request.data.get("is_approved") == "true"
        uploaded_file = request.FILES.get("file")

        if not title or not material_type or not subject or not class_id:
            return Response({"error": "Semua field wajib diisi."}, status=400)

        try:
            class_obj = Classes.objects.get(id=class_id)
        except Classes.DoesNotExist:
            return Response({"error": "Kelas tidak ditemukan."}, status=404)

        material.title = title
        material.type = material_type
        material.subject = subject
        material.class_field = class_obj
        material.is_approved = is_approved

        if uploaded_file:
            size_setting = AppSettings.objects.filter(key="max_material_file_size_mb").first()
            types_setting = AppSettings.objects.filter(key="allowed_material_types").first()

            max_mb = int(size_setting.value) if size_setting else 50
            allowed_types = types_setting.value.split(",") if types_setting else ["pdf", "mp4", "docx"]

            ext = os.path.splitext(uploaded_file.name)[1][1:].lower()
            size_mb = uploaded_file.size / (1024 * 1024)

            if ext not in allowed_types:
                return Response({"error": f"Tipe file .{ext} tidak diizinkan. Diizinkan: {', '.join(allowed_types)}"}, status=400)

            if size_mb > max_mb:
                return Response({"error": f"Ukuran file melebihi batas {max_mb} MB"}, status=400)

            unique_name = f"{uuid.uuid4().hex}.{ext}"
            saved_path = default_storage.save(f"material/{unique_name}", uploaded_file)
            material.file_url = saved_path

        material.save()
        return Response({"message": "Materi berhasil diperbarui."})

    
class FeedbackListView(APIView):
    def get(self, request):
        feedbacks = Feedbacks.objects.select_related('student', 'tutor').all().order_by('-created_at')

        data = []
        for fb in feedbacks:
            tutor = fb.tutor
            student = fb.student

            # Deteksi arah feedback
            if student and tutor:
                sender_role = "student"
                receiver_role = "tutor"
                sender = student.full_name
                recipient = tutor.full_name
                target = "Tutor"
            elif student and not tutor:
                sender_role = "student"
                receiver_role = "admin"
                sender = student.full_name
                recipient = "Admin"
                target = "Admin"
            elif tutor and not student:
                sender_role = "tutor"
                receiver_role = "student"
                sender = tutor.full_name
                recipient = "Siswa"
                target = "Student"
            else:
                sender_role = "unknown"
                receiver_role = "unknown"
                sender = "Unknown"
                recipient = "Unknown"
                target = "-"

            data.append({
                "id": fb.id,
                "sender": sender,
                "recipient": recipient,
                "sender_role": sender_role,
                "receiver_role": receiver_role,
                "target": target,
                "rating": fb.rating,
                "summary": fb.comment[:50] + "..." if fb.comment else "-",
                "created_at": fb.created_at.isoformat() if fb.created_at else "",
                "is_approved": fb.is_approved,
                "date": fb.created_at.strftime("%d/%m/%Y") if fb.created_at else "-"
            })

        return Response(data)

class FeedbackDetailView(APIView):
    def get(self, request, id):
        fb = get_object_or_404(Feedbacks.objects.select_related("student", "tutor"), id=id)

        tutor = fb.tutor
        student = fb.student

        if student and tutor:
            sender_role = "student"
            receiver_role = "tutor"
            sender = student.full_name
            recipient = tutor.full_name
            target = "Tutor"
        elif student and not tutor:
            sender_role = "student"
            receiver_role = "admin"
            sender = student.full_name
            recipient = "Admin"
            target = "Admin"
        elif tutor and not student:
            sender_role = "tutor"
            receiver_role = "student"
            sender = tutor.full_name
            recipient = "Siswa"
            target = "Student"
        else:
            sender_role = "unknown"
            receiver_role = "unknown"
            sender = "Unknown"
            recipient = "Unknown"
            target = "-"

        return Response({
            "id": fb.id,
            "sender": sender,
            "recipient": recipient,
            "sender_role": sender_role,
            "receiver_role": receiver_role,
            "target": target,
            "rating": fb.rating or 0,
            "comment": fb.comment or "",
            "created_at": fb.created_at.isoformat() if fb.created_at else "",
            "date": fb.created_at.strftime("%d/%m/%Y") if fb.created_at else "-",
            "is_approved": fb.is_approved,
        }, status=status.HTTP_200_OK)

        
class ApproveFeedbackView(APIView):
    def post(self, request, id):
        fb = get_object_or_404(Feedbacks, id=id)
        if fb.is_approved:
            return Response({"message": "Feedback sudah disetujui."}, status=400)

        fb.is_approved = True
        fb.save()
        return Response({"message": "Feedback berhasil disetujui."}, status=200)

# GET: Ambil mode moderasi feedback
class FeedbackModerationSettingView(APIView):
    def get(self, request):
        setting = AppSettings.objects.filter(key="feedback_moderation_mode").first()
        return Response({"mode": setting.value if setting else "auto"})

# PUT: Ubah mode moderasi feedback
class UpdateFeedbackModerationSettingView(APIView):
    def put(self, request):
        mode = request.data.get("mode")
        if mode not in ["auto", "manual"]:
            return Response({"error": "Mode tidak valid."}, status=400)

        AppSettings.objects.update_or_create(
            key="feedback_moderation_mode", defaults={"value": mode}
        )
        return Response({"message": "Pengaturan moderasi feedback berhasil diperbarui."})
    
class LearningContentSettingsView(APIView):
    def get(self, request):
        max_size = AppSettings.objects.filter(key="max_material_file_size_mb").first()
        allowed_types = AppSettings.objects.filter(key="allowed_material_types").first()
        auto_approve = AppSettings.objects.filter(key="tutor_auto_approve_materials").first()

        return Response({
            "max_material_file_size_mb": int(max_size.value) if max_size else 50,
            "allowed_material_types": allowed_types.value.split(",") if allowed_types else ["pdf", "mp4", "docx"],
            "tutor_auto_approve_materials": auto_approve.value == "true" if auto_approve else False
        })

    def put(self, request):
        max_size = request.data.get("max_material_file_size_mb")
        allowed_types = request.data.get("allowed_material_types")
        tutor_auto = request.data.get("tutor_auto_approve_materials")

        if not max_size or not isinstance(allowed_types, list):
            return Response({"error": "Data tidak valid."}, status=400)

        AppSettings.objects.update_or_create(key="max_material_file_size_mb", defaults={"value": str(max_size)})
        AppSettings.objects.update_or_create(key="allowed_material_types", defaults={"value": ",".join(allowed_types)})
        AppSettings.objects.update_or_create(key="tutor_auto_approve_materials", defaults={"value": "true" if tutor_auto else "false"})

        return Response({"message": "Pengaturan berhasil diperbarui."})

    
class NotificationSettingsView(APIView):
    def get(self, request):
        keys = ['email_notification_admin', 'schedule_reminder']
        settings = AppSettings.objects.filter(key__in=keys)
        data = {s.key: s.value for s in settings}
        return Response(data)

class UpdateSettingView(APIView):
    def post(self, request):
        key = request.data.get("key")
        value = request.data.get("value")

        if not key or value is None:
            return Response({"error": "Key dan value wajib diisi."}, status=400)

        setting, created = AppSettings.objects.get_or_create(key=key)
        setting.value = value
        setting.save(update_fields=["value"])
        return Response({"message": "Pengaturan berhasil diperbarui."})
    
class AdminNotificationStatusView(APIView):
    def get(self, request):
        unseen_reschedules = RescheduleRequests.objects.filter(
            status="Pending",
            schedule__schedule_date__gte=timezone.now().date()  
        ).count()
        unapproved_feedbacks = Feedbacks.objects.filter(is_approved=False).count()
        unapproved_materials = Materials.objects.filter(is_approved=False).count()
        pending_signups = SignupTokens.objects.filter(is_used=False).count()

        total_alerts = sum([
            unseen_reschedules,
            unapproved_feedbacks,
            unapproved_materials,
            pending_signups
        ])

        return Response({
            "has_notification": total_alerts > 0,
            "details": {
                "reschedule_requests": unseen_reschedules,
                "unapproved_feedbacks": unapproved_feedbacks,
                "unapproved_materials": unapproved_materials,
                "pending_signups": pending_signups
            }
        })
        
class AddSubjectView(APIView):
    def post(self, request):
        name = request.data.get("name", "").strip()
        if not name:
            return Response({"error": "Subject name is required"}, status=400)

        if Subjects.objects.filter(name__iexact=name).exists():
            return Response({"error": "Subject already exists"}, status=400)

        Subjects.objects.create(name=name)
        return Response({"message": "Subject created successfully"}, status=201)

class AdminRescheduleListView(APIView):
    def get(self, request):
        reschedules = RescheduleRequests.objects.select_related(
            "schedule", "requested_by_tutor", "schedule__class_field", "schedule__subject"
        )

        data = []
        for r in reschedules:
            schedule = r.schedule
            data.append({
                "id": r.id,
                "schedule_id": schedule.id,
                "tutor": r.requested_by_tutor.full_name,
                "class_name": schedule.class_field.class_name if schedule.class_field else "-",
                "subject": schedule.subject.name if schedule.subject else "-",
                "reason": r.reason,
                "status": r.status,
                "requested_at": r.requested_at,
                "schedule_date": schedule.schedule_date,
                "start_time": schedule.start_time.strftime('%H:%M'),
                "end_time": schedule.end_time.strftime('%H:%M'),
                "mode": schedule.status if schedule.status else "-"  
            })

        return Response(data, status=200)


class AdminApproveReschedule(APIView):
    def post(self, request, reschedule_id):
        try:
            # Cari permintaan reschedule
            reschedule = RescheduleRequests.objects.select_related("schedule").get(id=reschedule_id)
            schedule = reschedule.schedule
        except RescheduleRequests.DoesNotExist:
            return Response({"error": "Permintaan reschedule tidak ditemukan."}, status=404)

        if reschedule.status != "Pending":
            return Response({"error": "Permintaan ini sudah diproses."}, status=400)

        # Setujui permintaan dan tandai jadwal sebagai 'rescheduled'
        reschedule.status = "Approved"
        schedule.status = "rescheduled"

        # Simpan perubahan
        schedule.save()
        reschedule.save()

        return Response({
            "message": "Permintaan reschedule disetujui. Silakan atur ulang jadwal.",
            "redirect_schedule_id": schedule.id
        }, status=status.HTTP_200_OK)


class AdminRejectReschedule(APIView):
    def post(self, request, reschedule_id):
        try:
            # Ambil permintaan reschedule
            r = RescheduleRequests.objects.get(id=reschedule_id)

            # Validasi status
            if r.status != "Pending":
                return Response({"error": "Permintaan ini sudah diproses."}, status=400)

            # Update status
            r.status = "Rejected"
            r.save()

            return Response({
                "message": "Permintaan reschedule ditolak.",
                "reschedule_id": r.id,
                "new_status": r.status
            }, status=200)

        except RescheduleRequests.DoesNotExist:
            return Response({"error": "Permintaan reschedule tidak ditemukan."}, status=404)

