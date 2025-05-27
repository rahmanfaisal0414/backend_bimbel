# 🔧 Python built-in
import os
from datetime import date, datetime, timedelta
from urllib.parse import urljoin

# 🔌 Django
from django.conf import settings
from django.core.files.storage import default_storage
from django.contrib.auth.hashers import check_password, make_password
from django.shortcuts import get_object_or_404
from django.utils.timezone import localtime, now
from django.db.models import Avg, Q

# 🌐 DRF
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

# 🧠 Models
from accounts.models import (
    Users,
    Students,
    Classes,
    Schedules,
    Assignments,
    AssignmentSubmissions,
    Attendance,
    StudentClasses,
    AppSettings,
    Feedbacks,
    TutorExpertise,
    Tutors,
    Materials,
    ScheduleMaterials,
    RescheduleRequests,
    ScheduleAssignments,
)

# ⚙️ Utilities
from .utils import get_student_by_user, get_student_by_user_my_schedule


class StudentHomeView(APIView):
    def get(self, request):
        user_id = request.query_params.get("user_id")
        if not user_id:
            return Response({"error": "user_id diperlukan"}, status=status.HTTP_400_BAD_REQUEST)

        # ✅ Validasi user dan student
        try:
            user = Users.objects.get(id=user_id, role="student")
            student = Students.objects.get(user=user)
        except Users.DoesNotExist:
            return Response({"error": "User tidak ditemukan"}, status=status.HTTP_404_NOT_FOUND)
        except Students.DoesNotExist:
            return Response({"error": "Profil siswa tidak ditemukan"}, status=status.HTTP_404_NOT_FOUND)

        # ✅ Ambil kelas siswa
        student_class = Classes.objects.filter(studentclasses__student=student).first()
        if not student_class:
            return Response({"error": "Siswa belum memiliki kelas"}, status=status.HTTP_404_NOT_FOUND)

        # 📊 Summary
        assigned_total = Assignments.objects.filter(class_field=student_class).count()
        assigned_done = AssignmentSubmissions.objects.filter(student=student).count()
        average_score = AssignmentSubmissions.objects.filter(student=student, grade__isnull=False).aggregate(avg=Avg('grade'))['avg'] or 0

        today = date.today()
        now = datetime.now().time()

        past_schedule_ids = Schedules.objects.filter(
            class_field=student_class
        ).filter(
            Q(schedule_date__lt=today) |
            Q(schedule_date=today, end_time__lt=now)
        ).values_list("id", flat=True)

        # Step 2: Ambil hanya absensi dari jadwal tersebut
        attendance_total = Attendance.objects.filter(
            student=student,
            schedule_id__in=past_schedule_ids
        ).count()

        attendance_present = Attendance.objects.filter(
            student=student,
            schedule_id__in=past_schedule_ids,
            confirmed_by_student=True,
            marked_by_tutor=True
        ).count()


        summary = {
            "assigned_tasks": f"{assigned_done}/{assigned_total}",
            "average_score": f"{round(average_score)}%" if assigned_done else "0%",
            "attendance_rate": f"{round((attendance_present / attendance_total) * 100)}%" if attendance_total else "0%",
        }


        # 📌 Recent Assignments
        recent_assignments_qs = Assignments.objects.filter(class_field=student_class).order_by("-created_at")[:3]
        assignment_data = []
        for a in recent_assignments_qs:
            submission = AssignmentSubmissions.objects.filter(student=student, assignment=a).first()

            # ⛏️ Fix: datetime vs date comparison
            if submission:
                status_text = "Completed"
            else:
                status_text = "In Progress" if a.due_date and a.due_date.date() < date.today() else "Not Started"

            assignment_data.append({
                "id": a.id,
                "title": a.title,
                "subject": a.subject.name if a.subject else "-",
                "tutor_name": a.tutor.full_name if a.tutor else "-",
                "status": status_text
            })

        # 🕑 Upcoming Classes
        today = date.today()
        upcoming_qs = Schedules.objects.filter(
            class_field=student_class,
            schedule_date__gte=today
        ).select_related("subject").order_by("schedule_date", "start_time")[:3]

        upcoming_data = []
        for s in upcoming_qs:
            upcoming_data.append({
                "id": s.id,
                "subject": s.subject.name if s.subject else "-",
                "room": s.room or "-",
                "date": s.schedule_date.strftime("%B %d"), 
                "time": f"{s.start_time.strftime('%H:%M')} - {s.end_time.strftime('%H:%M')}",
                "mode": s.status.upper() 
            })

        return Response({
            "summary": summary,
            "recent_assignments": assignment_data,
            "upcoming_classes": upcoming_data
        }, status=status.HTTP_200_OK)

class StudentUserInfoView(APIView):
    def get(self, request):
        user_id = request.query_params.get("user_id")
        if not user_id:
            return Response({"error": "user_id diperlukan"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = Users.objects.get(id=user_id, role="student")
        except Users.DoesNotExist:
            return Response({"error": "User tidak ditemukan"}, status=status.HTTP_404_NOT_FOUND)

        try:
            student = Students.objects.get(user=user)
        except Students.DoesNotExist:
            return Response({"error": "Data siswa tidak ditemukan"}, status=status.HTTP_404_NOT_FOUND)

        # Ambil kelas dari StudentClasses
        student_class = (
            StudentClasses.objects
            .filter(student=student)
            .select_related("class_field")
            .first()
        )
        class_name = student_class.class_field.class_name if student_class and student_class.class_field else None
        class_level = student_class.class_field.level if student_class and student_class.class_field else None

        return Response({
            "full_name": user.full_name,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "photo_url": user.photo_url or "/media/profile/default-avatar.png",
            "date_joined": user.date_joined.isoformat() if user.date_joined else None,
            "phone": user.phone,
            "address": user.address,
            "bio": user.bio,
            "gender": student.gender,
            "birthdate": student.birthdate.isoformat() if student.birthdate else None,
            "parent_contact": student.parent_contact,
            "class_name": class_name,
            "class_level": class_level,
        }, status=status.HTTP_200_OK)
        
class StudentProfileView(APIView):
    def get(self, request):
        user_id = request.query_params.get("user_id")
        if not user_id:
            return Response({"error": "user_id is required"}, status=400)

        try:
            user = Users.objects.get(id=user_id)
        except Users.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

        if user.role != "student":
            return Response({"error": "Unauthorized"}, status=403)

        try:
            student = Students.objects.get(user=user)
        except Students.DoesNotExist:
            return Response({"error": "Student profile not found"}, status=404)

        return Response({
            "full_name": user.full_name,
            "email": user.email,
            "phone": user.phone,
            "address": user.address,
            "bio": user.bio,
            "photo_url": user.photo_url or "/media/profile/default-avatar.png",
            "birthdate": student.birthdate.strftime("%Y-%m-%d") if student.birthdate else "",
            "parent_contact": student.parent_contact,
        })

    def put(self, request):
        user_id = request.query_params.get("user_id")
        if not user_id:
            return Response({"error": "user_id is required"}, status=400)

        try:
            user = Users.objects.get(id=user_id)
        except Users.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

        if user.role != "student":
            return Response({"error": "Unauthorized"}, status=403)

        try:
            student = Students.objects.get(user=user)
        except Students.DoesNotExist:
            return Response({"error": "Student profile not found"}, status=404)

        # Update user data
        user.full_name = request.data.get("full_name", user.full_name)
        user.phone = request.data.get("phone", user.phone)
        user.address = request.data.get("address", user.address)
        user.bio = request.data.get("bio", user.bio)

        if "photo_url" in request.FILES:
            file = request.FILES["photo_url"]
            file_name = f"profile/student_{user.id}_{file.name}"
            file_path = os.path.join(settings.MEDIA_ROOT, file_name)
            with default_storage.open(file_path, 'wb+') as destination:
                for chunk in file.chunks():
                    destination.write(chunk)
            user.photo_url = f"/media/{file_name}"

        user.save()

        # Update student profile
        student.birthdate = request.data.get("birthdate") or None
        student.parent_contact = request.data.get("parent_contact") or ""
        student.save()

        return Response({"message": "Profile updated successfully."})
    
class StudentChangePasswordView(APIView):
    def put(self, request):
        user_id = request.query_params.get("user_id")
        if not user_id:
            return Response({"error": "user_id is required"}, status=400)

        try:
            user = Users.objects.get(id=user_id)
        except Users.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

        if user.role != "student":
            return Response({"error": "Unauthorized"}, status=403)

        current_password = request.data.get("current_password")
        new_password = request.data.get("new_password")
        confirm_password = request.data.get("confirm_password")

        if not all([current_password, new_password, confirm_password]):
            return Response({"error": "Semua field wajib diisi."}, status=400)

        if not check_password(current_password, user.password):
            return Response({"error": "Password saat ini salah."}, status=400)

        if new_password != confirm_password:
            return Response({"error": "Konfirmasi password tidak cocok."}, status=400)

        user.password = make_password(new_password)
        user.save()

        return Response({"message": "Password berhasil diubah."}, status=200)
    
class StudentNotificationSettingsView(APIView):
    def get(self, request):
        user_id = request.query_params.get("user_id")
        if not user_id:
            return Response({"error": "user_id diperlukan"}, status=400)

        keys = ["schedule_reminder", "assignment_reminder"]
        settings = {}

        for key in keys:
            full_key = f"student_{user_id}_{key}"
            setting = AppSettings.objects.filter(key=full_key).first()
            settings[key] = setting.value if setting else "false"

        return Response(settings, status=200)


class UpdateStudentSettingView(APIView):
    def post(self, request):
        user_id = request.query_params.get("user_id")
        key = request.data.get("key")
        value = request.data.get("value")

        if not user_id or not key or value is None:
            return Response({"error": "Key, value, dan user_id wajib diisi."}, status=400)

        if key not in ['schedule_reminder', 'assignment_reminder']:
            return Response({"error": "Invalid setting key"}, status=400)

        full_key = f"student_{user_id}_{key}"
        setting, created = AppSettings.objects.get_or_create(key=full_key)
        setting.value = value
        setting.save()

        return Response({"message": "Setting updated successfully."}, status=200)
    
class AllFeedbacksForStudentView(APIView):
    def get(self, request):
        user_id = request.query_params.get("user_id")
        if not user_id:
            return Response({"error": "user_id diperlukan"}, status=400)

        try:
            student = get_student_by_user(user_id)
        except:
            return Response({"error": "Siswa tidak ditemukan"}, status=404)

        combined_data = []

        # === FEEDBACK DUA ARAH (student → tutor atau tutor → student) ===
        all_feedbacks = Feedbacks.objects.filter(
            student=student,
            is_approved=True
        ).select_related("tutor").order_by("-created_at")

        for fb in all_feedbacks:
            tutor = fb.tutor
            tutor_name = tutor.full_name if tutor else "-"
            subject = tutor.expertise if tutor and tutor.expertise else "-"
            student_class = StudentClasses.objects.filter(student=student).select_related("class_field").first()
            class_name = student_class.class_field.class_name if student_class and student_class.class_field else "-"

            # 🧠 Deteksi siapa pengirimnya
            if tutor and student: 
                # Misalnya default: tutor kirim ke student
                sender_role = "tutor"
                receiver_role = "student"

                # Tapi jika tutor hanya penerima (karena student yang mengirim), ganti
                feedback_from_student = Feedbacks.objects.filter(id=fb.id, student=student, tutor=tutor)
                if feedback_from_student.exists() and fb.comment and fb.rating:
                    # Asumsi: feedback dari student ke tutor
                    sender_role = "student"
                    receiver_role = "tutor"

            elif tutor and not student:
                sender_role = "tutor"
                receiver_role = "unknown"
            else:
                sender_role = "student"
                receiver_role = "admin"

            combined_data.append({
                "id": f"fb-{fb.id}",
                "source": "Umum",
                "tutor_name": tutor_name,
                "subject": subject,
                "class_name": class_name,
                "feedback": fb.comment[:100] if fb.comment else "-",
                "rating_or_grade": f"{fb.rating}/5" if fb.rating else "-",
                "date": fb.created_at.strftime("%d/%m/%Y") if fb.created_at else "-",
                "sender_role": sender_role,
                "receiver_role": receiver_role
            })

        # === FEEDBACK TUGAS DARI TUTOR KE STUDENT ===
        submissions = AssignmentSubmissions.objects.filter(
            student=student,
            feedback__isnull=False
        ).select_related("assignment__tutor", "assignment__class_field").order_by("-submitted_at")

        for sub in submissions:
            assignment = sub.assignment
            if not assignment:
                continue

            combined_data.append({
                "id": f"sub-{sub.id}",
                "source": f"Tugas: {assignment.title}",
                "tutor_name": assignment.tutor.full_name if assignment.tutor else "-",
                "subject": assignment.tutor.expertise if assignment.tutor and assignment.tutor.expertise else "-",
                "class_name": assignment.class_field.class_name if assignment.class_field else "-",
                "feedback": sub.feedback[:100] if sub.feedback else "-",
                "rating_or_grade": str(sub.grade) if sub.grade is not None else "-",
                "date": sub.submitted_at.strftime("%d/%m/%Y") if sub.submitted_at else "-",
                "sender_role": "tutor",
                "receiver_role": "student"
            })

        return Response(combined_data, status=200)

class StudentFeedbackDetailView(APIView):
    def get(self, request, id):
        user_id = request.query_params.get("user_id")
        if not user_id:
            return Response({"error": "user_id diperlukan"}, status=400)

        try:
            student = get_student_by_user(user_id)
        except:
            return Response({"error": "Siswa tidak ditemukan"}, status=404)

        # Cek apakah ID diawali dengan fb- atau sub-
        if id.startswith("fb-"):
            try:
                real_id = int(id.replace("fb-", ""))
            except:
                return Response({"error": "ID feedback tidak valid"}, status=400)

            fb = Feedbacks.objects.filter(id=real_id, student_id=student.id).first()
            if fb:
                tutor = fb.tutor
                subject = ", ".join([
                    te.subject.name for te in TutorExpertise.objects.filter(tutor=tutor)
                ]) if tutor else "-"
                student_class = StudentClasses.objects.filter(
                    student=student).select_related("class_field").first()

                return Response({
                    "id": f"fb-{fb.id}",
                    "sender": tutor.full_name if tutor else "Admin",
                    "subject": subject,
                    "class": student_class.class_field.class_name if student_class and student_class.class_field else "-",
                    "rating": fb.rating or 0,
                    "comment": fb.comment or "",
                    "created_at": fb.created_at.isoformat() if fb.created_at else "",
                    "is_approved": fb.is_approved,
                })

        elif id.startswith("sub-"):
            try:
                real_id = int(id.replace("sub-", ""))
            except:
                return Response({"error": "ID submission tidak valid"}, status=400)

            sub = AssignmentSubmissions.objects.filter(
                id=real_id, student=student).select_related("assignment__tutor", "assignment__class_field").first()

            if sub:
                assignment = sub.assignment
                # Konversi grade (0–100) ke rating (0–5)
                grade = sub.grade or 0
                rating = min(5, grade // 20)

                return Response({
                    "id": f"sub-{sub.id}",
                    "sender": assignment.tutor.full_name if assignment and assignment.tutor else "-",
                    "subject": assignment.tutor.expertise if assignment and assignment.tutor else "-",
                    "class": assignment.class_field.class_name if assignment and assignment.class_field else "-",
                    "rating": rating,
                    "comment": sub.feedback or "",
                    "created_at": sub.submitted_at.isoformat() if sub.submitted_at else "",
                    "is_approved": True
                })

        return Response({"error": "Feedback tidak ditemukan atau bukan milik Anda"}, status=404)

class StudentGiveFeedbackView(APIView):
    def post(self, request):
        data = request.data
        user_id = data.get("user_id")
        comment = data.get("comment", "").strip()
        rating = data.get("rating")
        tutor_id = data.get("tutor_id")

        # Validasi user
        if not user_id:
            return Response({"error": "user_id diperlukan"}, status=400)

        try:
            student = get_student_by_user(user_id)
        except:
            return Response({"error": "Siswa tidak ditemukan"}, status=404)

        if not comment:
            return Response({"error": "Komentar tidak boleh kosong"}, status=400)

        if not rating or not (1 <= int(rating) <= 5):
            return Response({"error": "Rating harus antara 1 - 5"}, status=400)

        # Jika feedback untuk tutor
        if tutor_id:
            try:
                tutor = Tutors.objects.get(id=tutor_id)
            except Tutors.DoesNotExist:
                return Response({"error": "Tutor tidak ditemukan"}, status=404)

            Feedbacks.objects.create(
                student=student,
                tutor=tutor,
                comment=comment,
                rating=rating,
                is_approved=False
            )
        else:
            # Feedback untuk admin
            Feedbacks.objects.create(
                student=student,
                tutor=None,
                comment=comment,
                rating=rating,
                is_approved=False
            )

        return Response({"message": "Feedback berhasil dikirim"}, status=201)
    
class StudentTutorListView(APIView):
    def get(self, request):
        tutors = Tutors.objects.all().order_by("full_name")

        data = [
            {
                "id": tutor.id,
                "full_name": tutor.full_name,
            }
            for tutor in tutors
        ]

        return Response(data, status=200)
    
class StudentLearningDashboardView(APIView):
    def get(self, request):
        user_id = request.query_params.get("user_id")

        if not user_id:
            return Response({"error": "user_id diperlukan"}, status=400)

        try:
            student = Students.objects.get(user__id=user_id)
        except Students.DoesNotExist:
            return Response({"error": "Siswa tidak ditemukan"}, status=404)

        # Ambil class siswa
        student_class = StudentClasses.objects.filter(student=student).select_related("class_field").first()
        if not student_class:
            return Response({"materials": [], "assignments": []})

        class_field = student_class.class_field

        # === Materi ===
        materials_qs = Materials.objects.filter(
            class_field=class_field,
            is_approved=True
        ).order_by("-uploaded_at")

        material_data = []
        for m in materials_qs:
            file_url = None
            if m.file_url:
                file_url = request.build_absolute_uri(settings.MEDIA_URL + m.file_url)

            material_data.append({
                "id": m.id,
                "title": m.title,
                "subject": m.subject or "-",
                "classRange": class_field.class_name,
                "type": m.type,
                "uploadDate": m.uploaded_at.strftime("%Y-%m-%d") if m.uploaded_at else "-",
                "fileUrl": file_url
            })

        # === Tugas ===
        assignments_qs = Assignments.objects.filter(
            class_field=class_field
        ).order_by("-due_date")

        assignment_data = []
        for a in assignments_qs:
            submission = AssignmentSubmissions.objects.filter(
                assignment=a,
                student=student
            ).first()

            file_url = None
            if a.file_url:
                file_url = request.build_absolute_uri(settings.MEDIA_URL + a.file_url)

            assignment_data.append({
                "id": a.id,
                "title": a.title,
                "classRange": class_field.class_name,
                "dueDate": a.due_date.strftime("%Y-%m-%d") if a.due_date else "-",
                "fileUrl": file_url,
                "submitted": submission is not None,
                "grade": submission.grade if submission else None
            })

        return Response({
            "materials": material_data,
            "assignments": assignment_data
        }, status=200)
        
class StudentMaterialDetailView(APIView):
    def get(self, request, material_id):
        try:
            material = Materials.objects.select_related("class_field", "tutor").get(id=material_id, is_approved=True)
        except Materials.DoesNotExist:
            return Response({"error": "Materi tidak ditemukan."}, status=404)

        # Ambil jadwal yang menggunakan materi ini
        schedule_links = ScheduleMaterials.objects.filter(
            material=material
        ).select_related("schedule", "schedule__subject", "schedule__class_field")

        used_in = [
            {
                "date": s.schedule.schedule_date.strftime("%Y-%m-%d") if s.schedule.schedule_date else "-",
                "time": f"{s.schedule.start_time} - {s.schedule.end_time}" if s.schedule.start_time and s.schedule.end_time else "-",
                "subject": s.schedule.subject.name if s.schedule.subject else "-",
                "class": s.schedule.class_field.class_name if s.schedule.class_field else "-"
            }
            for s in schedule_links
        ]

        return Response({
            "id": material.id,
            "title": material.title,
            "type": material.type,
            "subject": material.subject or "-",
            "class_name": material.class_field.class_name if material.class_field else "-",
            "status": "Published" if material.is_approved else "Draft",
            "uploaded_by": material.tutor.full_name if material.tutor else "Admin",
            "uploaded_at": material.uploaded_at.strftime("%Y-%m-%d %H:%M:%S") if material.uploaded_at else "-",
            "file_url": request.build_absolute_uri(settings.MEDIA_URL + material.file_url) if material.file_url else None,
            "used_in_schedules": used_in
        }, status=200)
        
class StudentAssignmentDetailView(APIView):
    def get(self, request, assignment_id):
        user_id = request.query_params.get("user_id")
        if not user_id:
            return Response({"error": "user_id diperlukan"}, status=400)

        try:
            student = Students.objects.get(user__id=user_id)
        except Students.DoesNotExist:
            return Response({"error": "Siswa tidak ditemukan"}, status=404)

        try:
            assignment = Assignments.objects.select_related("class_field", "tutor", "subject").get(id=assignment_id)
        except Assignments.DoesNotExist:
            return Response({"error": "Tugas tidak ditemukan"}, status=404)

        # ✅ Ambil nama subject langsung dari assignment.subject
        subject_name = assignment.subject.name if assignment.subject else "-"

        submission = AssignmentSubmissions.objects.filter(assignment=assignment, student=student).first()

        def get_full_url(file_path):
            if not file_path:
                return None
            if str(file_path).startswith("/media/"):
                return request.build_absolute_uri(file_path)
            return request.build_absolute_uri(settings.MEDIA_URL + str(file_path))

        return Response({
            "id": assignment.id,
            "title": assignment.title,
            "description": assignment.description,
            "subject": subject_name,
            "class_name": assignment.class_field.class_name if assignment.class_field else "-",
            "due_date": assignment.due_date.strftime("%Y-%m-%d") if assignment.due_date else "-",
            "file_url": get_full_url(assignment.file_url),
            "uploaded_by": assignment.tutor.full_name if assignment.tutor else "Admin",
            "created_at": assignment.created_at.strftime("%Y-%m-%d %H:%M"),
            "submission": {
                "submitted": submission is not None,
                "file_url": get_full_url(submission.file_url if submission else None),
                "submitted_at": submission.submitted_at.strftime("%Y-%m-%d %H:%M") if submission and submission.submitted_at else None,
                "grade": submission.grade if submission else None,
                "feedback": submission.feedback if submission else None,
            }
        }, status=200)


class SubmitAssignmentView(APIView):
    def post(self, request, assignment_id):
        user_id = request.data.get("user_id")
        uploaded_file = request.FILES.get("file")

        if not user_id:
            return Response({"error": "user_id wajib diisi"}, status=400)

        if not uploaded_file:
            return Response({"error": "File tugas wajib diunggah"}, status=400)

        try:
            student = Students.objects.get(user__id=user_id)
        except Students.DoesNotExist:
            return Response({"error": "Siswa tidak ditemukan"}, status=404)

        try:
            assignment = Assignments.objects.get(id=assignment_id)
        except Assignments.DoesNotExist:
            return Response({"error": "Tugas tidak ditemukan"}, status=404)

        # Buat nama file unik
        ext = os.path.splitext(uploaded_file.name)[1]
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"{student.full_name.replace(' ', '_')}_{timestamp}{ext}"
        path = f"jawaban_tugas/{filename}"

        # Simpan file
        saved_path = default_storage.save(path, uploaded_file)

        # Simpan atau update submission
        submission, _ = AssignmentSubmissions.objects.update_or_create(
            assignment=assignment,
            student=student,
            defaults={
                "file_url": f"/media/{saved_path}",
                "submitted_at": datetime.now(),
            }
        )

        return Response({"message": "Jawaban berhasil dikirim"}, status=201)
    
class StudentScheduleListView(APIView):
    def get(self, request):
        user_id = request.query_params.get("user_id")
        status_filter = request.query_params.get("status", "").strip().lower()

        if not user_id:
            return Response([], status=200)  

        try:
            student = get_student_by_user_my_schedule(user_id)
        except:
            return Response([], status=200) 

        today = date.today()
        now = datetime.now().time()

        # Ambil semua kelas siswa
        student_classes = student.studentclasses_set.values_list("class_field", flat=True)

        # Filter awal: ambil jadwal dari kelas siswa
        queryset = Schedules.objects.filter(class_field__in=student_classes).select_related("tutor", "subject")

        # Filter berdasarkan status waktu
        if status_filter == "upcoming":
            queryset = queryset.filter(
                Q(schedule_date__gt=today) |
                Q(schedule_date=today, start_time__gt=now)
            )
        elif status_filter == "in_progress":
            queryset = queryset.filter(
                schedule_date=today,
                start_time__lte=now,
                end_time__gte=now
            )
        elif status_filter == "completed":
            queryset = queryset.filter(
                Q(schedule_date__lt=today) |
                Q(schedule_date=today, end_time__lt=now)
            )
        elif status_filter == "rescheduled":
            queryset = queryset.filter(status="rescheduled")
        else:
            return Response([], status=200)  

        # Format data untuk response
        data = []
        for s in queryset:
            data.append({
                "id": s.id,
                "subject": s.subject.name if s.subject else "-",
                "tutor": s.tutor.full_name if s.tutor else "-",
                "date": s.schedule_date.strftime("%d %B %Y"),
                "time": f"{s.start_time.strftime('%H:%M')} - {s.end_time.strftime('%H:%M')}",
                "room": s.room or "-",
                "status": "offline" if s.room else "online",
            })

        return Response(data, status=status.HTTP_200_OK)
    
class StudentScheduleDetailView(APIView):
    def get(self, request, schedule_id):
        user_id = request.query_params.get("user_id")
        if not user_id:
            return Response({"error": "user_id diperlukan"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            student = get_student_by_user(user_id)
        except:
            return Response({"error": "Siswa tidak ditemukan"}, status=status.HTTP_404_NOT_FOUND)

        try:
            schedule = Schedules.objects.select_related("class_field", "tutor", "subject").get(id=schedule_id)
        except Schedules.DoesNotExist:
            return Response({"error": "Jadwal tidak ditemukan"}, status=status.HTTP_404_NOT_FOUND)

        # Schedule Info
        schedule_data = {
            "subject": schedule.subject.name if schedule.subject else "-",
            "class_name": schedule.class_field.class_name if schedule.class_field else "-",
            "schedule_date": schedule.schedule_date.strftime("%Y-%m-%d"),
            "start_time": schedule.start_time.strftime("%H:%M"),
            "end_time": schedule.end_time.strftime("%H:%M"),
            "room": schedule.room or "-",
            "status": schedule.status,
        }

        # Materials
        materials_qs = ScheduleMaterials.objects.filter(schedule=schedule).select_related("material")
        materials = []
        for m in materials_qs:
            file_name = m.material.file_url.split('/')[-1] if m.material.file_url else ''
            file_url = request.build_absolute_uri(f"/media/material/{file_name}") if file_name else None
            materials.append({
                "title": m.material.title,
                "type": m.material.type,
                "status": "Published" if m.material.is_approved else "Draft",
                "file_url": file_url,
            })


        # Assignments khusus yang terkait dengan jadwal ini
        linked_assignments = ScheduleAssignments.objects.filter(schedule=schedule).values_list("assignment_id", flat=True)
        assignments_qs = Assignments.objects.filter(id__in=linked_assignments)

        assignments = []
        for a in assignments_qs:
            submission = AssignmentSubmissions.objects.filter(assignment=a, student=student).first()
            assignments.append({
                "title": a.title,
                "due_date": a.due_date.strftime("%Y-%m-%d") if a.due_date else "-",
                "submitted": submission is not None,
                "grade": submission.grade if submission and submission.grade is not None else None,
            })

        # Attendance (hanya status siswa ini)
        attendance = Attendance.objects.filter(schedule=schedule, student=student).first()
        attendance_data = {
            "marked_by_tutor": attendance.marked_by_tutor if attendance else False,
            "confirmed_by_student": attendance.confirmed_by_student if attendance else False,
            "timestamp": attendance.timestamp.strftime("%Y-%m-%d %H:%M") if attendance and attendance.timestamp else None
        }

        # Reschedule info (jika ada)
        reschedule = RescheduleRequests.objects.filter(schedule=schedule).first()
        reschedule_data = None
        if reschedule:
            reschedule_data = {
                "reason": reschedule.reason,
                "status": reschedule.status,
                "requested_at": reschedule.requested_at.strftime("%Y-%m-%d %H:%M"),
            }

        # Summary
        summary_data = {
            "material_count": len(materials),
            "assignment_count": len(assignments),
            "attendance_status": "Hadir" if attendance and attendance.marked_by_tutor else "Belum Absen",
        }

        return Response({
            "schedule": schedule_data,
            "summary": summary_data,
            "materials": materials,
            "assignments": assignments,
            "attendance": attendance_data,
            "reschedule": reschedule_data,
        }, status=status.HTTP_200_OK)
        
class ConfirmStudentAttendanceView(APIView):
    def post(self, request):
        user_id = request.data.get("user_id")
        schedule_id = request.data.get("schedule_id")

        if not user_id or not schedule_id:
            return Response({"error": "user_id dan schedule_id wajib diisi"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            student = get_student_by_user(user_id)
        except:
            return Response({"error": "Siswa tidak ditemukan"}, status=status.HTTP_404_NOT_FOUND)

        try:
            schedule = Schedules.objects.get(id=schedule_id)
        except Schedules.DoesNotExist:
            return Response({"error": "Jadwal tidak ditemukan"}, status=status.HTTP_404_NOT_FOUND)

        try:
            attendance = Attendance.objects.get(student=student, schedule=schedule)
        except Attendance.DoesNotExist:
            return Response({"error": "Data absensi tidak ditemukan"}, status=status.HTTP_404_NOT_FOUND)

        if not attendance.marked_by_tutor:
            return Response({"error": "Tutor belum menandai kehadiran. Konfirmasi tidak dapat dilakukan."}, status=status.HTTP_400_BAD_REQUEST)

        # Tambahkan batas waktu konfirmasi (24 jam sejak jadwal berakhir)
        end_datetime = datetime.combine(schedule.schedule_date, schedule.end_time)
        deadline = end_datetime + timedelta(hours=12)
        now = datetime.now()

        if now > deadline:
            return Response({"error": "Waktu konfirmasi telah berakhir. Batas waktu adalah 24 jam setelah kelas berakhir."}, status=status.HTTP_403_FORBIDDEN)

        # Simpan konfirmasi
        attendance.confirmed_by_student = True
        attendance.save()

        return Response({"message": "Kehadiran berhasil dikonfirmasi."}, status=status.HTTP_200_OK)
    
class StudentAttendanceListView(APIView):
    def get(self, request):
        user_id = request.query_params.get("user_id")
        if not user_id:
            return Response({"error": "user_id diperlukan"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = Users.objects.get(id=user_id, role="student")
            student = Students.objects.get(user=user)
        except Users.DoesNotExist:
            return Response({"error": "User tidak ditemukan"}, status=status.HTTP_404_NOT_FOUND)
        except Students.DoesNotExist:
            return Response({"error": "Data student tidak ditemukan"}, status=status.HTTP_404_NOT_FOUND)

        attendance_data = (
            Attendance.objects
            .filter(student=student)
            .select_related("schedule", "schedule__tutor", "schedule__subject", "schedule__class_field")
            .order_by("-schedule__schedule_date", "-schedule__start_time")
        )

        results = []
        now = datetime.now()

        for record in attendance_data:
            schedule = record.schedule
            if not schedule:
                continue

            schedule_end_dt = datetime.combine(schedule.schedule_date, schedule.end_time)
            time_diff = now - schedule_end_dt
            is_late = time_diff.total_seconds() > 12 * 3600

            # Logika status
            if record.confirmed_by_student and record.marked_by_tutor:
                attendance_status = "Presents"
            elif record.confirmed_by_student and not record.marked_by_tutor:
                attendance_status = "Student Marked"
            elif not record.confirmed_by_student and record.marked_by_tutor:
                attendance_status = "Pending Confirmation" if not is_late else "Unconfirmed"
            elif not record.marked_by_tutor and not record.confirmed_by_student:
                attendance_status = "Awaiting Mark" if not is_late else "Absent"
            else:
                attendance_status = "Absent"  


            results.append({
                "id": record.id,
                "date": schedule.schedule_date.strftime("%d/%m/%Y"),
                "time": f"{schedule.start_time.strftime('%H:%M')}–{schedule.end_time.strftime('%H:%M')}",
                "subject": schedule.subject.name if schedule.subject else "-",
                "tutor": schedule.tutor.full_name if schedule.tutor else "-",
                "mode": "Offline" if schedule.room else "Online",
                "status": attendance_status
            })

        return Response(results, status=status.HTTP_200_OK)
    
class StudentAttendanceDetailView(APIView):
    def get(self, request, attendance_id):
        user_id = request.query_params.get("user_id")
        if not user_id:
            return Response({"error": "user_id diperlukan"}, status=status.HTTP_400_BAD_REQUEST)

        # Validasi user dan attendance
        try:
            user = Users.objects.get(id=user_id, role="student")
            student = Students.objects.get(user=user)
            attendance = Attendance.objects.select_related("schedule").get(id=attendance_id, student=student)
        except Users.DoesNotExist:
            return Response({"error": "User tidak ditemukan"}, status=status.HTTP_404_NOT_FOUND)
        except Students.DoesNotExist:
            return Response({"error": "Data siswa tidak ditemukan"}, status=status.HTTP_404_NOT_FOUND)
        except Attendance.DoesNotExist:
            return Response({"error": "Data kehadiran tidak ditemukan"}, status=status.HTTP_404_NOT_FOUND)

        schedule = attendance.schedule
        if not schedule:
            return Response({"error": "Jadwal tidak ditemukan"}, status=status.HTTP_404_NOT_FOUND)

        # Jadwal
        schedule_data = {
            "subject": schedule.subject.name if schedule.subject else "-",
            "class_name": schedule.class_field.class_name if schedule.class_field else "-",
            "schedule_date": schedule.schedule_date.strftime("%Y-%m-%d"),
            "start_time": schedule.start_time.strftime("%H:%M"),
            "end_time": schedule.end_time.strftime("%H:%M"),
            "room": schedule.room or "",
            "status": schedule.status,
            "tutor": schedule.tutor.full_name if schedule.tutor else "-",
        }

        # Kehadiran
        attendance_data = {
            "marked_by_tutor": attendance.marked_by_tutor,
            "confirmed_by_student": attendance.confirmed_by_student,
            "timestamp": attendance.timestamp.strftime("%d/%m/%Y %H:%M") if attendance.timestamp else None
        }

        return Response({
            "schedule": schedule_data,
            "attendance": attendance_data,
        })
        
class StudentGlobalSearchView(APIView):
    def get(self, request):
        user_id = request.query_params.get("user_id")
        query = request.query_params.get("q", "").strip()

        if not user_id or not query:
            return Response({"error": "user_id dan query diperlukan"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            student = Students.objects.get(user__id=user_id)
        except Students.DoesNotExist:
            return Response({"error": "Siswa tidak ditemukan"}, status=status.HTTP_404_NOT_FOUND)

        # Ambil semua class yang diikuti oleh student
        student_class_ids = StudentClasses.objects.filter(
            student=student
        ).values_list("class_field_id", flat=True)

        results = []

        # 🔍 Cari Materi
        materials = Materials.objects.filter(
            class_field_id__in=student_class_ids,
            title__icontains=query
        ).values("id", "title")

        for m in materials:
            results.append({
                "type": "material",
                "id": m["id"],
                "title": m["title"]
            })

        # 🔍 Cari Tugas
        assignments = Assignments.objects.filter(
            class_field_id__in=student_class_ids,
            title__icontains=query
        ).values("id", "title")

        for a in assignments:
            results.append({
                "type": "assignment",
                "id": a["id"],
                "title": a["title"]
            })

        # 🔍 Cari Jadwal
        schedules = Schedules.objects.filter(
            class_field_id__in=student_class_ids,
            subject__name__icontains=query
        ).select_related("subject").values("id", "subject__name", "schedule_date")

        for s in schedules:
            results.append({
                "type": "schedule",
                "id": s["id"],
                "title": f"{s['subject__name']} – {s['schedule_date']}"
            })

        return Response(results, status=status.HTTP_200_OK)
    
class StudentNotificationView(APIView):
    def get(self, request):
        user_id = request.query_params.get("user_id")
        if not user_id:
            return Response({"error": "user_id diperlukan"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            student = get_student_by_user(user_id)
        except:
            return Response({"error": "Data student tidak ditemukan"}, status=status.HTTP_404_NOT_FOUND)

        today = now().date()
        current_time = now().time()

        # Fungsi untuk ambil preferensi pengaturan
        def get_pref(key):
            setting = AppSettings.objects.filter(key=f"student_{user_id}_{key}").first()
            return setting and setting.value == "true"

        notif = {}
        has_notification = False

        # Ambil daftar class dari StudentClasses
        student_classes = StudentClasses.objects.filter(student=student).values_list("class_field", flat=True)

        # === Jadwal Mendatang ===
        if get_pref("schedule_reminder"):
            upcoming_schedules = Schedules.objects.filter(
                class_field__in=student_classes
            ).filter(
                Q(schedule_date__gt=today) |
                Q(schedule_date=today, start_time__gt=current_time)
            ).exclude(
                status__in=["completed", "rescheduled", "canceled"]
            ).count()

            notif["upcoming_class"] = upcoming_schedules
            has_notification |= upcoming_schedules > 0

        # === Tugas Belum Dikumpulkan ===
        if get_pref("assignment_reminder"):
            all_assignments = Assignments.objects.filter(
                class_field__in=student_classes,
                due_date__gte=today
            ).values_list("id", flat=True)

            submitted_assignments = AssignmentSubmissions.objects.filter(
                assignment_id__in=all_assignments,
                student=student
            ).values_list("assignment_id", flat=True)

            not_submitted = set(all_assignments) - set(submitted_assignments)

            notif["unsubmitted_assignment"] = len(not_submitted)
            has_notification |= len(not_submitted) > 0

        return Response({
            "has_notification": has_notification,
            "details": notif
        }, status=status.HTTP_200_OK)
