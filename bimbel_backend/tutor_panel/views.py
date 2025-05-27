# 🔧 Python built-in
import os
import uuid
from datetime import date, datetime, timedelta
from collections import Counter
from urllib.parse import urljoin

# 🔌 Django & DRF
from django.conf import settings
from django.db import transaction
from django.db.models import Count, Avg
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.core.files.storage import default_storage
from django.contrib.auth.hashers import check_password, make_password

from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView

# 🧠 Models
from accounts.models import (
    Users,
    Tutors,
    Students,
    Classes,
    Schedules,
    Materials,
    Assignments,
    AssignmentSubmissions,
    Attendance,
    ScheduleMaterials,
    Feedbacks,
    TutorExpertise,
    TutorAvailability,
    AppSettings,
    StudentClasses,
    RescheduleRequests,
    TutorClasses,
    Subjects,
    ScheduleAssignments,
)

# ⚙️ Utilities
from .utils import get_tutor_by_user, get_schedule_status

class TutorHomeView(APIView):
    def get(self, request):
        user_id = request.query_params.get("user_id")

        if not user_id:
            return Response({"error": "user_id diperlukan"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = Users.objects.get(id=user_id)
        except Users.DoesNotExist:
            return Response({"error": "User tidak ditemukan"}, status=status.HTTP_404_NOT_FOUND)

        if user.role != 'tutor':
            return Response({"error": "Akses ditolak, bukan tutor"}, status=status.HTTP_403_FORBIDDEN)

        try:
            tutor = get_tutor_by_user(user)
        except:
            return Response({"error": "Profil tutor tidak ditemukan"}, status=status.HTTP_404_NOT_FOUND)

        today = date.today()

        # Jadwal hari ini
        schedules = Schedules.objects.filter(tutor=tutor, schedule_date=today).select_related("class_field", "subject")
        schedule_data = []
        status_counter = Counter()

        for s in schedules:
            subject_name = s.subject.name if s.subject else "-"
            class_name = s.class_field.class_name if s.class_field else "-"
            reschedule_obj = RescheduleRequests.objects.filter(schedule=s).first()
            reschedule_status = reschedule_obj.status if reschedule_obj else None
            dynamic_status = get_schedule_status(s, reschedule_status)

            schedule_data.append({
                "id": s.id,
                "status": dynamic_status,
                "subject": f"{subject_name} - {class_name}",
                "time": f"{s.start_time.strftime('%H:%M')} - {s.end_time.strftime('%H:%M')}" if s.start_time and s.end_time else "-",
                "room": s.room or "-",
            })

            status_counter[dynamic_status] += 1

        # Materi terbaru
        materials = Materials.objects.filter(tutor=tutor).order_by("-uploaded_at")[:5]
        material_data = [
            {
                "id": m.id,
                "title": m.title,
                "status": "Published" if m.is_approved else "Draft",
                "subject": m.subject or "-"
            }
            for m in materials
        ]

        # Tugas terbaru dan jumlah submit
        assignments = Assignments.objects.filter(tutor=tutor).order_by("-created_at")
        assignment_data = []
        for a in assignments:
            submit_count = AssignmentSubmissions.objects.filter(assignment=a).count()
            assignment_data.append({
                "id": a.id,
                "title": a.title,
                "class": a.class_field.class_name if a.class_field else "-",
                "submits": submit_count,
                "date": a.due_date.strftime("%d %B %Y") if a.due_date else "-"
            })

        # Ringkasan
        summary = {
            "classes_today": schedules.count(),
            "materials_uploaded": Materials.objects.filter(tutor=tutor).count(),
            "assignments_review": AssignmentSubmissions.objects.filter(assignment__tutor=tutor).count()
        }

        return Response({
            "schedule": schedule_data,
            "materials": material_data,
            "assignments": assignment_data,
            "summary": summary,
            "status_summary_today": dict(status_counter) 
        }, status=status.HTTP_200_OK)

class TutorUserInfoView(APIView):
    def get(self, request):
        user_id = request.query_params.get("user_id")

        if not user_id:
            return Response({"error": "user_id diperlukan"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = Users.objects.get(id=user_id)
        except Users.DoesNotExist:
            return Response({"error": "User tidak ditemukan"}, status=status.HTTP_404_NOT_FOUND)

        if user.role != "tutor":
            return Response({"error": "User ini bukan tutor"}, status=status.HTTP_403_FORBIDDEN)

        try:
            tutor = Tutors.objects.get(user=user)
        except Tutors.DoesNotExist:
            return Response({"error": "Data tutor tidak ditemukan"}, status=status.HTTP_404_NOT_FOUND)

        # Ambil daftar subject dari relasi many-to-many via TutorExpertise
        subjects = TutorExpertise.objects.filter(tutor=tutor).select_related("subject")
        subject_names = [s.subject.name for s in subjects]

        return Response({
            "user_id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "email": user.email,
            "role": user.role,
            "photo_url": user.photo_url,
            "phone": user.phone,
            "address": user.address,
            "bio": user.bio,
            "date_joined": user.date_joined.isoformat() if user.date_joined else None,
            "expertise": subject_names,
        })
        
class TutorProfileView(APIView):
    def get(self, request):
        user_id = request.query_params.get("user_id")
        if not user_id:
            return Response({"error": "user_id is required"}, status=400)

        try:
            user = Users.objects.get(id=user_id)
        except Users.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

        if user.role != "tutor":
            return Response({"error": "Unauthorized"}, status=403)

        return Response({
            "full_name": user.full_name,
            "email": user.email,
            "phone": user.phone,
            "address": user.address,
            "bio": user.bio,
            "photo_url": user.photo_url or "/media/profile/default-avatar.png"
        })

    def put(self, request):
        user_id = request.query_params.get("user_id")
        if not user_id:
            return Response({"error": "user_id is required"}, status=400)

        try:
            user = Users.objects.get(id=user_id)
        except Users.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

        # Ambil data dari form
        user.full_name = request.data.get("full_name", user.full_name)
        user.phone = request.data.get("phone", user.phone)
        user.address = request.data.get("address", user.address)
        user.bio = request.data.get("bio", user.bio)

        # Upload foto jika ada
        if "photo_url" in request.FILES:
            file = request.FILES["photo_url"]
            file_name = f"profile/tutor_{user.id}_{file.name}"
            file_path = os.path.join(settings.MEDIA_ROOT, file_name)

            # Simpan file
            with default_storage.open(file_path, 'wb+') as destination:
                for chunk in file.chunks():
                    destination.write(chunk)

            user.photo_url = f"/media/{file_name}"

        user.save()

        return Response({"message": "Profile updated successfully."})
    
class TutorChangePasswordView(APIView):
    def put(self, request):
        user_id = request.query_params.get("user_id")
        if not user_id:
            return Response({"error": "user_id is required"}, status=400)

        try:
            user = Users.objects.get(id=user_id)
        except Users.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

        if user.role != "tutor":
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

        # Ubah password
        user.password = make_password(new_password)
        user.save()

        return Response({"message": "Password berhasil diubah."}, status=200)
    
class TutorNotificationSettingsView(APIView):
    def get(self, request):
        keys = [
            'schedule_reminder',
            'assignment_reminder',
            'feedback_alert'
        ]
        settings = {key: "false" for key in keys}

        for key in keys:
            try:
                setting = AppSettings.objects.get(key=key)
                settings[key] = setting.value
            except AppSettings.DoesNotExist:
                continue

        return Response(settings, status=200)


class UpdateTutorSettingView(APIView):
    def post(self, request):
        key = request.data.get("key")
        value = request.data.get("value")

        if key not in ['schedule_reminder', 'assignment_reminder', 'feedback_alert']:
            return Response({"error": "Invalid setting key"}, status=400)

        setting, created = AppSettings.objects.get_or_create(key=key)
        setting.value = value
        setting.save()

        return Response({"message": "Setting updated successfully."}, status=200)
    
class TutorAvailabilityListView(APIView):
    def get(self, request):
        user_id = request.query_params.get('user_id')
        try:
            tutor = Tutors.objects.get(user__id=user_id)
        except Tutors.DoesNotExist:
            return Response({'error': 'Tutor tidak ditemukan'}, status=404)

        availability = TutorAvailability.objects.filter(tutor=tutor)
        data = [
            {
                'id': a.id,
                'day_of_week': a.day_of_week,
                'start_time': a.start_time.strftime('%H:%M'),
                'end_time': a.end_time.strftime('%H:%M'),
            }
            for a in availability
        ]
        return Response(data)

class AddTutorAvailabilityView(APIView):
    def post(self, request):
        user_id = request.query_params.get('user_id')
        day = request.data.get('day_of_week')
        start = request.data.get('start_time')
        end = request.data.get('end_time')

        if not all([user_id, day, start, end]):
            return Response({'error': 'Semua field wajib diisi'}, status=400)

        try:
            tutor = Tutors.objects.get(user__id=user_id)
        except Tutors.DoesNotExist:
            return Response({'error': 'Tutor tidak ditemukan'}, status=404)

        # Konversi string ke time object
        try:
            start_time_obj = datetime.strptime(start, "%H:%M").time()
            end_time_obj = datetime.strptime(end, "%H:%M").time()
        except ValueError:
            return Response({'error': 'Format waktu tidak valid (HH:MM)'}, status=400)

        availability = TutorAvailability.objects.create(
            tutor=tutor,
            day_of_week=day,
            start_time=start_time_obj,
            end_time=end_time_obj
        )

        return Response({
            'id': availability.id,
            'day_of_week': availability.day_of_week,
            'start_time': availability.start_time.strftime('%H:%M'),
            'end_time': availability.end_time.strftime('%H:%M'),
        }, status=201)

class DeleteTutorAvailabilityView(APIView):
    def delete(self, request, availability_id):
        try:
            availability = TutorAvailability.objects.get(id=availability_id)
            availability.delete()
            return Response({'message': 'Berhasil dihapus'}, status=200)
        except TutorAvailability.DoesNotExist:
            return Response({'error': 'Data tidak ditemukan'}, status=404)
        
class TutorFeedbackListView(APIView):
    def get(self, request):
        user_id = request.query_params.get("user_id")
        if not user_id:
            return Response({"error": "user_id diperlukan"}, status=400)

        try:
            tutor = Tutors.objects.get(user__id=user_id)
        except Tutors.DoesNotExist:
            return Response({"error": "Tutor tidak ditemukan"}, status=404)

        feedbacks = Feedbacks.objects.filter(
            tutor=tutor,
            is_approved=True,
            student__isnull=False
        ).select_related("student").order_by("-created_at")

        data = []
        for fb in feedbacks:
            sender = fb.student.full_name if fb.student else "Unknown"
            subject = ", ".join([
                te.subject.name for te in TutorExpertise.objects.filter(tutor=tutor)
            ]) or "-"

            # Ambil nama kelas dari StudentClasses
            student_class = StudentClasses.objects.filter(student=fb.student).select_related("class_field").first()
            class_name = student_class.class_field.class_name if student_class and student_class.class_field else "-"

            summary = fb.comment[:50] + "..." if fb.comment else "-"

            data.append({
                "id": fb.id,
                "sender": sender,
                "sender_role": "student",
                "subject": subject,
                "class": class_name, 
                "rating": fb.rating,
                "summary": summary,
                "is_approved": fb.is_approved
            })

        return Response(data, status=200)
    
class TutorFeedbackDetailView(APIView):
    def get(self, request, feedback_id):
        user_id = request.query_params.get("user_id")
        if not user_id:
            return Response({"error": "user_id diperlukan"}, status=400)

        try:
            tutor = Tutors.objects.get(user__id=user_id)
        except Tutors.DoesNotExist:
            return Response({"error": "Tutor tidak ditemukan"}, status=404)

        try:
            feedback = Feedbacks.objects.select_related("student").get(
                id=feedback_id, tutor=tutor, is_approved=True, student__isnull=False
            )
        except Feedbacks.DoesNotExist:
            return Response({"error": "Feedback tidak ditemukan"}, status=404)

        # Ambil class siswa (jika ada)
        student_class = StudentClasses.objects.filter(student=feedback.student).select_related("class_field").first()
        class_name = student_class.class_field.class_name if student_class and student_class.class_field else "-"

        # Ambil subject dari TutorExpertise
        subject_list = [
            te.subject.name for te in TutorExpertise.objects.filter(tutor=tutor).select_related("subject")
        ]
        subject_str = ", ".join(subject_list) if subject_list else "-"

        data = {
            "id": feedback.id,
            "sender": feedback.student.full_name if feedback.student else "Unknown",
            "subject": subject_str,
            "class": class_name,
            "rating": feedback.rating,
            "comment": feedback.comment or "-",
            "created_at": feedback.created_at.isoformat() if feedback.created_at else ""
        }

        return Response(data, status=200)

class TutorScheduleListView(APIView):
    def get(self, request):
        user_id = request.query_params.get("user_id")

        if not user_id:
            return Response({"error": "user_id diperlukan"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = Users.objects.get(id=user_id)
        except Users.DoesNotExist:
            return Response({"error": "User tidak ditemukan"}, status=status.HTTP_404_NOT_FOUND)

        if user.role != "tutor":
            return Response({"error": "Akses ditolak, bukan tutor"}, status=status.HTTP_403_FORBIDDEN)

        try:
            tutor = Tutors.objects.get(user=user)
        except Tutors.DoesNotExist:
            return Response({"error": "Data tutor tidak ditemukan"}, status=status.HTTP_404_NOT_FOUND)

        schedules = Schedules.objects.filter(tutor=tutor).select_related("class_field", "subject").order_by("-schedule_date")

        data = []
        status_counter = Counter()

        for s in schedules:
            class_name = s.class_field.class_name if s.class_field else "-"
            date_str = s.schedule_date.strftime("%d/%m/%Y") if s.schedule_date else "-"
            time_str = f"{s.start_time.strftime('%H:%M')}–{s.end_time.strftime('%H:%M')}" if s.start_time and s.end_time else "-"
            subject_name = s.subject.name if s.subject else "-"

            reschedule_obj = RescheduleRequests.objects.filter(schedule=s).first()
            reschedule_status = reschedule_obj.status if reschedule_obj else None
            dynamic_status = get_schedule_status(s, reschedule_status)

            status_counter[dynamic_status] += 1

            data.append({
                "id": s.id,
                "date": date_str,
                "time": time_str,
                "subject": subject_name,
                "class_name": class_name,
                "room": s.room or "-",
                "mode": "Online" if s.room is None or s.room == "-" else "Offline",
                "status": dynamic_status,
            })

        return Response({
            "schedules": data,
            "summary": dict(status_counter)
        }, status=200)

class TutorScheduleDetailView(APIView):
    def get(self, request, schedule_id):
        user_id = request.query_params.get("user_id")
        if not user_id:
            return Response({"error": "user_id diperlukan"}, status=400)

        try:
            tutor = Tutors.objects.get(user__id=user_id)
            schedule = Schedules.objects.select_related("class_field", "subject").get(id=schedule_id, tutor=tutor)
        except (Tutors.DoesNotExist, Schedules.DoesNotExist):
            return Response({"error": "Jadwal tidak ditemukan"}, status=404)

        # Semua materi berdasarkan subject & class (untuk opsi pemilihan materi)
        materials = Materials.objects.filter(
            subject=schedule.subject.name,
            class_field=schedule.class_field
        )

        material_data = [
            {
                "id": m.id,
                "title": m.title,
                "type": m.type,
                "status": "Published" if m.is_approved else "Draft",
                "file_url": request.build_absolute_uri(settings.MEDIA_URL + m.file_url) if m.file_url else ""
            } for m in materials
        ]

        # Materi yang dipilih khusus untuk jadwal ini
        selected_materials = Materials.objects.filter(
            id__in=ScheduleMaterials.objects.filter(schedule=schedule).values_list('material_id', flat=True)
        )

        selected_material_data = [
            {
                "id": m.id,
                "title": m.title,
                "type": m.type,
                "status": "Published" if m.is_approved else "Draft",
                "file_url": request.build_absolute_uri(settings.MEDIA_URL + m.file_url) if m.file_url else ""
            } for m in selected_materials
        ]

        assignment_ids = ScheduleAssignments.objects.filter(schedule=schedule).values_list("assignment_id", flat=True)
        assignments = Assignments.objects.filter(id__in=assignment_ids)

        assignment_data = []
        for a in assignments:
            count = AssignmentSubmissions.objects.filter(assignment=a).count()
            assignment_data.append({
                "title": a.title,
                "due_date": a.due_date.strftime('%Y-%m-%d') if a.due_date else "-",
                "submits": count,
            })


        # Tambahkan ini
        student_ids = StudentClasses.objects.filter(class_field=schedule.class_field).values_list('student_id', flat=True)
        with transaction.atomic():
            for student_id in student_ids:
                Attendance.objects.get_or_create(schedule=schedule, student_id=student_id)

        # Kemudian baru ini jalan
        attendance_qs = Attendance.objects.filter(schedule=schedule).select_related("student")

        attendance_data = []
        for a in attendance_qs:
            attendance_data.append({
                "student_id": a.student.id if a.student else None,
                "student_name": a.student.full_name if a.student else "-",
                "marked_by_tutor": a.marked_by_tutor,
                "confirmed_by_student": a.confirmed_by_student,
                "timestamp": a.timestamp.strftime('%Y-%m-%d %H:%M') if a.timestamp else "-"
            })

        # Reschedule
        reschedule = RescheduleRequests.objects.filter(schedule=schedule).order_by("-requested_at").first()
        reschedule_data = {
            "reason": reschedule.reason,
            "status": reschedule.status,
            "requested_at": reschedule.requested_at.strftime('%Y-%m-%d %H:%M') if reschedule.requested_at else "-"
        } if reschedule else None

        # Rangkuman
        student_count = StudentClasses.objects.filter(class_field=schedule.class_field).count()

        return Response({
            "schedule": {
                "subject": schedule.subject.name if schedule.subject else "-",
                "class_name": schedule.class_field.class_name if schedule.class_field else "-",
                "schedule_date": schedule.schedule_date.isoformat(),
                "start_time": schedule.start_time.strftime('%H:%M'),
                "end_time": schedule.end_time.strftime('%H:%M'),
                "room": schedule.room or "-",
                "status": get_schedule_status(schedule, reschedule_data["status"] if reschedule_data else None),
                "mode": "Offline" if schedule.room else "Online",
            },
            "summary": {
                "student_count": student_count,
                "attendance_count": len(attendance_data),
                "material_count": len(selected_material_data),
                "assignment_count": len(assignment_data),
                "reschedule_status": reschedule_data["status"] if reschedule_data else "-",
            },
            "materials": selected_material_data,
            "assignments": assignment_data,
            "attendance": attendance_data,
            "reschedule": reschedule_data,
            "material_options": material_data
        }, status=200)
        
class SelectMaterialView(APIView):
    def post(self, request, schedule_id):
        material_ids = request.data.get("material_ids", [])
        user_id = request.data.get("user_id")

        if not user_id:
            return Response({"error": "user_id wajib diisi"}, status=400)

        try:
            tutor = Tutors.objects.get(user__id=user_id)
            schedule = Schedules.objects.get(id=schedule_id, tutor=tutor)
        except:
            return Response({"error": "Data tidak valid"}, status=404)

        # Hapus semua materi yang sudah dipilih sebelumnya
        ScheduleMaterials.objects.filter(schedule=schedule).delete()

        # Kalau ada materi baru, tambahkan
        if material_ids:
            materials = Materials.objects.filter(id__in=material_ids)
            for m in materials:
                ScheduleMaterials.objects.create(schedule=schedule, material=m)

        return Response({"message": "Materi untuk jadwal berhasil diperbarui"}, status=200)


class AddAssignmentView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, schedule_id):
        title = request.data.get("title", "").strip()
        description = request.data.get("description", "").strip()
        due_date = request.data.get("due_date", "")
        user_id = request.data.get("user_id")
        uploaded_file = request.FILES.get("file")

        if not (title and description and due_date and user_id):
            return Response({"error": "Semua field wajib diisi"}, status=400)

        try:
            tutor = Tutors.objects.get(user__id=user_id)
            schedule = Schedules.objects.get(id=schedule_id, tutor=tutor)
            subject_obj = schedule.subject
        except:
            return Response({"error": "Data tidak valid"}, status=404)

        file_url = None
        if uploaded_file:
            filename = f"tugas/{datetime.now().strftime('%Y%m%d%H%M%S')}_{uploaded_file.name}"
            file_path = os.path.join(settings.MEDIA_ROOT, filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)
            file_url = f"/media/{filename}"

        # ✅ Simpan tugas terlebih dahulu
        new_assignment = Assignments.objects.create(
            class_field=schedule.class_field,
            subject=subject_obj,
            tutor=tutor,
            title=title,
            description=description,
            due_date=due_date,
            created_at=datetime.now(),
            file_url=file_url
        )

        # ✅ Kaitkan tugas ke jadwal lewat ScheduleAssignments
        ScheduleAssignments.objects.create(
            schedule=schedule,
            assignment=new_assignment
        )

        return Response({"message": "Tugas berhasil ditambahkan"}, status=201)

class MarkAttendanceView(APIView):
    def post(self, request, schedule_id):
        attendance_data = request.data.get("attendance", [])

        for item in attendance_data:
            student_id = item.get("student_id")
            marked = item.get("marked_by_tutor", False)

            Attendance.objects.update_or_create(
                schedule_id=schedule_id,
                student_id=student_id,
                defaults={
                    "marked_by_tutor": marked,
                    "timestamp": datetime.now()
                }
            )

        return Response({"message": "Absensi berhasil diperbarui"}, status=200)

class RequestRescheduleView(APIView):
    def post(self, request, schedule_id):
        user_id = request.data.get("user_id")
        reason = request.data.get("reason", "").strip()

        if not user_id or not reason:
            return Response({"error": "user_id dan reason wajib diisi"}, status=400)

        try:
            tutor = Tutors.objects.get(user__id=user_id)
            schedule = Schedules.objects.get(id=schedule_id, tutor=tutor)
        except:
            return Response({"error": "Data tidak valid"}, status=404)

        # ✅ setelah schedule didefinisikan
        existing = RescheduleRequests.objects.filter(schedule=schedule, status="Pending").exists()
        if existing:
            return Response({"error": "Permintaan reschedule sebelumnya masih pending"}, status=400)

        RescheduleRequests.objects.create(
            schedule=schedule,
            requested_by_tutor=tutor,
            reason=reason,
            status="Pending",
            requested_at=datetime.now()
        )

        return Response({"message": "Permintaan reschedule berhasil dikirim"}, status=201)

class TutorTeachingDashboardView(APIView):
    def get(self, request):
        user_id = request.query_params.get("user_id")

        if not user_id:
            return Response({"error": "user_id diperlukan"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = Users.objects.get(id=user_id)
        except Users.DoesNotExist:
            return Response({"error": "User tidak ditemukan"}, status=status.HTTP_404_NOT_FOUND)

        if user.role != 'tutor':
            return Response({"error": "Akses ditolak, bukan tutor"}, status=status.HTTP_403_FORBIDDEN)

        try:
            tutor = Tutors.objects.get(user=user)
        except Tutors.DoesNotExist:
            return Response({"error": "Profil tutor tidak ditemukan"}, status=status.HTTP_404_NOT_FOUND)

        # Materials
        material_qs = Materials.objects.filter(tutor=tutor).select_related("class_field").order_by("-uploaded_at")
        materials = []
        for m in material_qs:
            materials.append({
                "id": m.id,
                "title": m.title,
                "subject": m.subject or "-",
                "classRange": m.class_field.class_name if m.class_field else "-",
                "type": m.type,
                "uploadDate": m.uploaded_at.strftime("%Y-%m-%d") if m.uploaded_at else "-"
            })

        # Assignments
        assignment_qs = Assignments.objects.filter(tutor=tutor).select_related("class_field").order_by("-created_at")
        assignments = []
        for a in assignment_qs:
            submit_count = AssignmentSubmissions.objects.filter(assignment=a).count()
            assignments.append({
                "id": a.id,
                "title": a.title,
                "classRange": a.class_field.class_name if a.class_field else "-",
                "dueDate": a.due_date.strftime("%Y-%m-%d") if a.due_date else "-",
                "fileUrl": a.file_url,
                "submissions": submit_count,
                "createdAt": a.created_at.strftime("%Y-%m-%d") if a.created_at else "-"
            })

        return Response({
            "materials": materials,
            "assignments": assignments
        }, status=status.HTTP_200_OK)

class TutorAddMaterialView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        try:
            title = request.data.get("title", "").strip()
            material_type = request.data.get("type", "").strip()
            subject = request.data.get("subject", "").strip()
            uploaded_file = request.FILES.get("file")
            user_id = request.data.get("user_id")
            class_id = request.data.get("class_id")

            if not all([title, material_type, subject, uploaded_file, user_id, class_id]):
                return Response({"error": "Semua field wajib diisi."}, status=400)

            try:
                tutor = Tutors.objects.get(user__id=user_id)
                class_obj = Classes.objects.get(id=class_id)
            except (Tutors.DoesNotExist, Classes.DoesNotExist):
                return Response({"error": "Tutor atau kelas tidak ditemukan."}, status=404)

            # Ambil pengaturan max size & tipe file
            size_setting = AppSettings.objects.filter(key="max_material_file_size_mb").first()
            types_setting = AppSettings.objects.filter(key="allowed_material_types").first()
            auto_approve_setting = AppSettings.objects.filter(key="tutor_auto_approve_materials").first()

            max_mb = int(size_setting.value) if size_setting else 50
            allowed_types = types_setting.value.split(",") if types_setting else ["pdf", "mp4", "docx"]
            auto_approve = auto_approve_setting.value.lower() == "true" if auto_approve_setting else False

            ext = os.path.splitext(uploaded_file.name)[1][1:].lower()
            size_mb = uploaded_file.size / (1024 * 1024)

            if ext not in allowed_types:
                return Response({
                    "error": f"Tipe file .{ext} tidak diizinkan. Diizinkan: {', '.join(allowed_types)}"
                }, status=400)

            if size_mb > max_mb:
                return Response({
                    "error": f"Ukuran file melebihi batas {max_mb} MB"
                }, status=400)

            # Simpan file
            unique_name = f"{uuid.uuid4().hex}.{ext}"
            saved_path = default_storage.save(f"material/{unique_name}", uploaded_file)

            # Simpan ke database
            Materials.objects.create(
                title=title,
                type=material_type,
                subject=subject,
                file_url=saved_path,
                is_approved=auto_approve, 
                tutor=tutor,
                class_field=class_obj,
                uploaded_at=timezone.now()
            )

            return Response({"message": "Materi berhasil ditambahkan."}, status=201)

        except Exception as e:
            return Response({"error": str(e)}, status=500)


class TutorAddAssignmentView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        try:
            title = request.data.get("title", "").strip()
            description = request.data.get("description", "").strip()
            due_date = request.data.get("due_date")
            class_id = request.data.get("class_id")
            subject_name = request.data.get("subject", "").strip()
            user_id = request.data.get("user_id")
            uploaded_file = request.FILES.get("file")

            if not all([title, due_date, class_id, subject_name, user_id]):
                return Response({"error": "Semua field wajib diisi."}, status=400)

            try:
                tutor = Tutors.objects.get(user__id=user_id)
                class_obj = Classes.objects.get(id=class_id)
                subject_obj = Subjects.objects.get(name=subject_name)
            except (Tutors.DoesNotExist, Classes.DoesNotExist, Subjects.DoesNotExist):
                return Response({"error": "Tutor, kelas, atau subject tidak valid."}, status=404)

            file_url = None
            if uploaded_file:
                ext = os.path.splitext(uploaded_file.name)[1]
                unique_name = f"{uuid.uuid4().hex}{ext}"
                saved_path = default_storage.save(f"tugas/{unique_name}", uploaded_file)
                file_url = f"/media/{saved_path}"

            Assignments.objects.create(
                title=title,
                description=description,
                due_date=due_date,
                file_url=file_url,
                class_field=class_obj,
                subject=subject_obj,
                tutor=tutor,
                created_at=timezone.now()
            )

            return Response({"message": "Tugas berhasil ditambahkan."}, status=201)

        except Exception as e:
            return Response({"error": str(e)}, status=500)
        
class TutorEditMaterialView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def put(self, request, material_id):
        try:
            material = Materials.objects.get(id=material_id)
        except Materials.DoesNotExist:
            return Response({"error": "Materi tidak ditemukan."}, status=404)

        title = request.data.get("title", "").strip()
        material_type = request.data.get("type", "").strip()
        subject = request.data.get("subject", "").strip()
        class_id = request.data.get("class_id")
        user_id = request.data.get("user_id")
        uploaded_file = request.FILES.get("file")

        # Validasi dasar
        if not all([title, material_type, subject, class_id, user_id]):
            return Response({"error": "Semua field wajib diisi."}, status=400)

        # Validasi user dan kelas
        try:
            tutor = Tutors.objects.get(user__id=user_id)
            class_obj = Classes.objects.get(id=class_id)
        except (Tutors.DoesNotExist, Classes.DoesNotExist):
            return Response({"error": "Tutor atau kelas tidak valid."}, status=404)

        # Update field dasar
        material.title = title
        material.type = material_type
        material.subject = subject
        material.class_field = class_obj
        material.tutor = tutor

        # Jika ada file baru diunggah, simpan dan ganti file lama
        if uploaded_file:
            ext = os.path.splitext(uploaded_file.name)[1]
            unique_name = f"{uuid.uuid4().hex}{ext}"
            saved_path = default_storage.save(f"material/{unique_name}", uploaded_file)
            material.file_url = saved_path

        material.uploaded_at = timezone.now()
        material.is_approved = False 
        material.save()

        return Response({"message": "Materi berhasil diperbarui."}, status=200)

class TutorMaterialDetailView(APIView):
    def get(self, request, material_id):
        try:
            material = Materials.objects.select_related("class_field", "tutor").get(id=material_id)
        except Materials.DoesNotExist:
            return Response({"error": "Materi tidak ditemukan."}, status=404)

        # Ambil jadwal yang menggunakan materi ini
        schedule_links = ScheduleMaterials.objects.filter(material=material).select_related("schedule", "schedule__subject", "schedule__class_field")
        used_in = [
            {
                "date": s.schedule.schedule_date,
                "time": f"{s.schedule.start_time} - {s.schedule.end_time}",
                "subject": s.schedule.subject.name if s.schedule.subject else "-",
                "class": s.schedule.class_field.class_name if s.schedule.class_field else "-",
            }
            for s in schedule_links
        ]

        return Response({
            "id": material.id,
            "title": material.title,
            "type": material.type,
            "subject": material.subject,
            "class_id": material.class_field.id if material.class_field else None,
            "class_name": material.class_field.class_name if material.class_field else "-",
            "status": "Published" if material.is_approved else "Draft",
            "uploaded_by": material.tutor.full_name if material.tutor else "Admin",
            "uploaded_at": material.uploaded_at,
            "file_url": request.build_absolute_uri(settings.MEDIA_URL + material.file_url) if material.file_url else None,
            "used_in_schedules": used_in
        })
        
class TutorAssignmentDetailView(APIView):
    def get(self, request, assignment_id):
        try:
            assignment = Assignments.objects.select_related("class_field", "tutor").get(id=assignment_id)
        except Assignments.DoesNotExist:
            return Response({"error": "Assignment not found"}, status=404)

        # Cari subject
        subject_name = "-"
        if assignment.tutor:
            expertise = TutorExpertise.objects.filter(tutor=assignment.tutor).select_related("subject").first()
            if expertise and expertise.subject:
                subject_name = expertise.subject.name

        # Ambil submissions
        submissions = AssignmentSubmissions.objects.filter(assignment=assignment).select_related("student")
        submission_data = [
            {
                "student_name": s.student.full_name if s.student else "-",
                "submitted_at": s.submitted_at.isoformat() if s.submitted_at else None,
                "status": "Submitted" if s.submitted_at else "Not Submitted",  # ✅ Tambahan status
                "grade": s.grade,
                "feedback": s.feedback,
                "file_url": request.build_absolute_uri(urljoin(settings.MEDIA_URL, s.file_url)) if s.file_url else None if s.file_url else None
            }
            for s in submissions
        ]

        return Response({
            "id": assignment.id,
            "title": assignment.title,
            "description": assignment.description,
            "due_date": assignment.due_date.isoformat() if assignment.due_date else None,
            "created_at": assignment.created_at.isoformat() if assignment.created_at else None,
            "file_url": request.build_absolute_uri(settings.MEDIA_URL + assignment.file_url) if assignment.file_url else None,
            "class_id": assignment.class_field.id if assignment.class_field else None,
            "class_name": assignment.class_field.class_name if assignment.class_field else "-",
            "subject": subject_name,
            "uploaded_by": assignment.tutor.full_name if assignment.tutor else "Admin",
            "submission_count": len(submission_data),
            "submissions": submission_data
        })
        
class GradeAssignmentSubmissionView(APIView):
    def post(self, request, assignment_id):
        student_name = request.data.get("student_name")
        grade = request.data.get("grade")
        feedback = request.data.get("feedback")

        try:
            assignment = Assignments.objects.get(id=assignment_id)
        except Assignments.DoesNotExist:
            return Response({"error": "Assignment not found"}, status=404)

        try:
            student = Students.objects.get(full_name=student_name)
        except Students.DoesNotExist:
            return Response({"error": "Student not found"}, status=404)

        try:
            submission, _ = AssignmentSubmissions.objects.get_or_create(
                assignment=assignment,
                student=student,
            )
            submission.grade = grade
            submission.feedback = feedback
            submission.save()
        except Exception as e:
            return Response({"error": str(e)}, status=500)

        return Response({"message": "Penilaian berhasil disimpan"})


class TutorEditAssignmentView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def put(self, request, assignment_id):
        try:
            assignment = Assignments.objects.get(id=assignment_id)
        except Assignments.DoesNotExist:
            return Response({"error": "Tugas tidak ditemukan."}, status=404)

        title = request.data.get("title", "").strip()
        description = request.data.get("description", "").strip()
        due_date = request.data.get("due_date", "")
        class_id = request.data.get("class_id")
        subject = request.data.get("subject", "").strip()
        user_id = request.data.get("user_id")
        uploaded_file = request.FILES.get("file")

        if not all([title, description, due_date, class_id, subject, user_id]):
            return Response({"error": "Semua field wajib diisi."}, status=400)

        try:
            tutor = Tutors.objects.get(user__id=user_id)
            class_obj = Classes.objects.get(id=class_id)
            subject_obj = Subjects.objects.get(name=subject)
        except (Tutors.DoesNotExist, Classes.DoesNotExist, Subjects.DoesNotExist):
            return Response({"error": "Tutor, kelas, atau subject tidak valid."}, status=404)

        assignment.title = title
        assignment.description = description
        assignment.due_date = due_date
        assignment.class_field = class_obj
        assignment.subject = subject_obj
        assignment.tutor = tutor

        if uploaded_file:
            ext = os.path.splitext(uploaded_file.name)[1]
            unique_name = f"{uuid.uuid4().hex}{ext}"
            saved_path = default_storage.save(f"tugas/{unique_name}", uploaded_file)
            assignment.file_url = f"/media/{saved_path}"

        assignment.save()

        return Response({"message": "Tugas berhasil diperbarui."}, status=200)

class TutorMaterialDeleteView(APIView):
    def delete(self, request, material_id):
        material = get_object_or_404(Materials, id=material_id)

        # Cek apakah materi ini sudah digunakan dalam jadwal
        is_used = ScheduleMaterials.objects.filter(material=material).exists()
        if is_used:
            return Response({
                "error": "Materi ini sudah digunakan dalam jadwal dan tidak dapat dihapus."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Jika belum digunakan, hapus materi
        material.delete()
        return Response({"message": "Materi berhasil dihapus."}, status=status.HTTP_200_OK)
    
class TutorAssignmentDeleteView(APIView):
    def delete(self, request, assignment_id):
        try:
            assignment = Assignments.objects.get(id=assignment_id)
        except Assignments.DoesNotExist:
            return Response({"error": "Tugas tidak ditemukan."}, status=404)

        # Cek apakah ada submission yang terkait
        if AssignmentSubmissions.objects.filter(assignment=assignment).exists():
            return Response({
                "error": "Tugas ini memiliki submission dan tidak dapat dihapus."
            }, status=400)

        assignment.delete()
        return Response({"message": "Tugas berhasil dihapus."}, status=200)

class StudentPerformanceView(APIView):
    def get(self, request):
        user_id = request.query_params.get("user_id")
        class_filter = request.query_params.get("class", "")
        subject_filter = request.query_params.get("subject", "")

        if not user_id:
            return Response({"error": "user_id diperlukan"}, status=400)

        try:
            tutor = Tutors.objects.get(user__id=user_id)
        except Tutors.DoesNotExist:
            return Response({"error": "Tutor tidak ditemukan"}, status=404)

        # Ambil semua kelas yang diajar tutor
        tutor_classes = TutorClasses.objects.filter(tutor=tutor).values_list("class_field", flat=True)

        # Ambil semua siswa dari kelas-kelas tersebut
        student_ids = StudentClasses.objects.filter(class_field__in=tutor_classes).values_list("student_id", flat=True)

        # Filter siswa
        students = Students.objects.filter(id__in=student_ids)

        if class_filter:
            students = students.filter(
                id__in=StudentClasses.objects.filter(class_field__class_name=class_filter).values_list("student_id", flat=True)
            )

        data = []

        for student in students:
            user = student.user
            student_class = StudentClasses.objects.filter(student=student).select_related("class_field").first()
            if not student_class:
                continue

            class_name = student_class.class_field.class_name
            subject_name = subject_filter if subject_filter else None

            assignments = Assignments.objects.filter(
                class_field=student_class.class_field,
                tutor=tutor
            )
            if subject_filter:
                assignments = assignments.filter(
                    tutor__in=TutorExpertise.objects.filter(subject__name=subject_filter).values("tutor")
                )

            assignment_ids = assignments.values_list("id", flat=True)
            submissions = AssignmentSubmissions.objects.filter(
                student=student,
                assignment_id__in=assignment_ids
            )

            avg_score = submissions.aggregate(avg=Avg("grade"))["avg"] or 0

            attendance_qs = Attendance.objects.filter(student=student)
            total_attendance = attendance_qs.count()
            confirmed_attendance = attendance_qs.filter(confirmed_by_student=True).count()
            attendance_percent = f"{int((confirmed_attendance / total_attendance) * 100)}%" if total_attendance > 0 else "0%"

            subject_display = subject_name or (
                TutorExpertise.objects.filter(
                    tutor=tutor
                ).values_list("subject__name", flat=True).first() or "-"
            )

            data.append({
                "id": student.id,
                "name": user.full_name,
                "class": class_name,
                "subject": subject_display,
                "avg_score": round(avg_score),
                "attendance": attendance_percent,
            })

        return Response(data, status=200)


class StudentPerformanceDetailView(APIView):
    def get(self, request, student_id):
        try:
            student = Students.objects.select_related("user").get(id=student_id)
        except Students.DoesNotExist:
            return Response({"error": "Siswa tidak ditemukan"}, status=404)

        user = student.user

        student_class = (
            StudentClasses.objects
            .filter(student=student)
            .select_related("class_field")
            .first()
        )
        if not student_class:
            return Response({"error": "Siswa belum memiliki kelas"}, status=400)

        class_field = student_class.class_field
        class_name = class_field.class_name
        class_level = class_field.level or "-"

        # Subject
        subject = (
            TutorExpertise.objects
            .filter(tutor__assignments__class_field=class_field)
            .select_related("subject")
            .values_list("subject__name", flat=True)
            .distinct()
            .first()
        )
        subject_name = subject or "-"

        # Assignments & Submission
        assignments = Assignments.objects.filter(class_field=class_field)
        assignment_ids = assignments.values_list("id", flat=True)
        submissions = AssignmentSubmissions.objects.filter(
            student=student,
            assignment_id__in=assignment_ids,
        )

        avg_score = submissions.aggregate(avg=Avg("grade"))["avg"] or 0

        assignment_data = []
        for a in assignments:
            sub = submissions.filter(assignment=a).first()
            assignment_data.append({
                "title": a.title,
                "grade": sub.grade if sub else None,
                "submitted_at": sub.submitted_at if sub else None,
            })

        # Attendance
        attendance_qs = Attendance.objects.filter(student=student).order_by("timestamp")
        total = attendance_qs.count()
        confirmed = attendance_qs.filter(confirmed_by_student=True).count()
        attendance_percent = f"{int((confirmed / total) * 100)}%" if total > 0 else "0%"

        attendance_data = [
            {
                "date": a.timestamp.strftime("%Y-%m-%d") if a.timestamp else "-",
                "confirmed": a.confirmed_by_student,
            }
            for a in attendance_qs
        ]

        # Feedback
        feedback = Feedbacks.objects.filter(student=student, is_approved=True).order_by("-created_at").first()
        feedback_data = {
            "rating": feedback.rating if feedback else None,
            "comment": feedback.comment if feedback else None,
        }

        return Response({
            "id": student.id,
            "full_name": user.full_name,
            "gender": student.gender or "-",
            "birthdate": student.birthdate.strftime("%Y-%m-%d") if student.birthdate else "-",
            "phone": student.phone or "-",
            "address": student.address or "-",
            "parent_contact": student.parent_contact or "-",
            "class_name": class_name,
            "class_level": class_level,
            "subject": subject_name,
            "avg_score": round(avg_score),
            "assignment_count": assignments.count(),
            "assignments": assignment_data,
            "attendance_percent": attendance_percent,
            "attendance": attendance_data,
            "feedback": feedback_data
        })
        
class TutorGlobalSearchView(APIView):
    def get(self, request):
        user_id = request.query_params.get("user_id")
        query = request.query_params.get("q", "").strip()

        if not user_id or not query:
            return Response({"error": "user_id dan query diperlukan"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            tutor = Tutors.objects.get(user__id=user_id)
        except Tutors.DoesNotExist:
            return Response({"error": "Tutor tidak ditemukan"}, status=status.HTTP_404_NOT_FOUND)

        results = []

        # Materi
        materials = Materials.objects.filter(
            tutor=tutor,
            title__icontains=query
        ).values("id", "title")

        for m in materials:
            results.append({
                "type": "material",
                "id": m["id"],
                "title": m["title"]
            })

        # Tugas
        assignments = Assignments.objects.filter(
            tutor=tutor,
            title__icontains=query
        ).values("id", "title")

        for a in assignments:
            results.append({
                "type": "assignment",
                "id": a["id"],
                "title": a["title"]
            })

        # Schedule
        schedules = Schedules.objects.filter(
            tutor=tutor,
            subject__name__icontains=query
        ).select_related("subject").values("id", "subject__name", "schedule_date")

        for s in schedules:
            results.append({
                "type": "schedule",
                "id": s["id"],
                "title": f"{s['subject__name']} – {s['schedule_date']}"
            })

        # Siswa
        student_ids = StudentClasses.objects.filter(
            class_field__in=TutorClasses.objects.filter(tutor=tutor).values_list("class_field", flat=True)
        ).values_list("student_id", flat=True)

        students = Students.objects.filter(
            id__in=student_ids,
            user__full_name__icontains=query
        ).select_related("user").values("id", "user__full_name")

        for s in students:
            results.append({
                "type": "student",
                "id": s["id"],
                "title": s["user__full_name"]
            })

        return Response(results)

class TutorNotificationStatusView(APIView):
    def get(self, request):
        user_id = request.query_params.get("user_id")
        if not user_id:
            return Response({"error": "user_id diperlukan"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            tutor = Tutors.objects.get(user__id=user_id)
        except Tutors.DoesNotExist:
            return Response({"error": "Tutor tidak ditemukan"}, status=status.HTTP_404_NOT_FOUND)

        # Ambil semua setting notifikasi
        def is_enabled(key):
            try:
                setting = AppSettings.objects.get(key=key)
                return setting.value.lower() == "true"
            except AppSettings.DoesNotExist:
                return False  # default: disabled

        # Tanggal sekarang
        today = date.today()
        seven_days_ago = timezone.now() - timedelta(days=7)

        # Inisialisasi hasil
        approved_reschedules = 0
        new_feedbacks = 0
        submitted_assignments = 0

        # ✅ 1. Notifikasi: reschedule
        if is_enabled("schedule_reminder"):
            approved_reschedules = RescheduleRequests.objects.filter(
                schedule__tutor=tutor,
                status="Approved",
                schedule__schedule_date__gte=today
            ).exclude(
                schedule__status="Rescheduled"
            ).count()

        # ✅ 2. Notifikasi: feedback
        if is_enabled("feedback_alert"):
            new_feedbacks = Feedbacks.objects.filter(
                tutor=tutor,
                is_approved=True,
                created_at__gte=seven_days_ago
            ).count()

        # ✅ 3. Notifikasi: tugas belum dinilai
        if is_enabled("assignment_reminder"):
            submitted_assignments = AssignmentSubmissions.objects.filter(
                assignment__tutor=tutor,
                grade__isnull=True
            ).count()

        total_alerts = sum([approved_reschedules, new_feedbacks, submitted_assignments])

        return Response({
            "has_notification": total_alerts > 0,
            "details": {
                "reschedule_requests": approved_reschedules,
                "new_feedback": new_feedbacks,
                "assignment_submits": submitted_assignments,
            }
        }, status=200)
