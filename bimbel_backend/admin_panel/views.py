from datetime import date

from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from collections import defaultdict
from rest_framework.views import APIView
import calendar

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
)

from .serializers import (
    AdminStudentManagementSerializer,
    AdminStudentDetailSerializer,
    TutorListSerializer,
)

class AdminDashboardView(APIView):
    def get(self, request):
        stats = {
            "Total Tutor": Tutors.objects.all().count(),    # Ganti
            "Total Student": Students.objects.all().count(), # Ganti
            "Total Class": Classes.objects.all().count(),    # Ganti
            "Average Attendance": self.calculate_average_attendance()
        }

        today = date.today()
        schedules = Schedules.objects.filter(schedule_date=today)  # Ini sudah oke

        schedule_data = [
            {
                "status": sched.status,
                "subject": sched.subject,
                "tutor": sched.tutor.full_name if sched.tutor else "Unknown",
                "time": f"{sched.start_time.strftime('%H:%M')} – {sched.end_time.strftime('%H:%M')}"
            }
            for sched in schedules
        ]

        return Response({
            "stats": [{"label": k, "value": v} for k, v in stats.items()],
            "schedule": schedule_data
        }, status=status.HTTP_200_OK)

    def calculate_average_attendance(self):
        attendances = Attendance.objects.all()
        total_records = attendances.count()
        if total_records == 0:
            return "0%"
        
        present_count = attendances.filter(status="present").count()
        average_percentage = (present_count / total_records) * 100
        return f"{average_percentage:.0f}%"
    
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
                'role': user.role
            }, status=status.HTTP_200_OK)

        except Users.DoesNotExist:
            return Response({'error': 'User tidak ditemukan'}, status=status.HTTP_404_NOT_FOUND)
   
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

        # Optional: ganti kelas
        new_class_id = data.get("class_id")
        if new_class_id:
            try:
                new_class = Classes.objects.get(id=new_class_id)
            except Classes.DoesNotExist:
                return Response({"error": "Class not found"}, status=status.HTTP_404_NOT_FOUND)

            # Cek apakah sudah pernah pindah ke kelas yang sama
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
            user.is_active = not user.is_active  # toggle aktif/nonaktif
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
            queryset = queryset.filter(expertise__iexact=subject)

        # Ambil semua jadwal
        schedule_raw = Schedules.objects.select_related('tutor').all()
        schedule_map = defaultdict(lambda: defaultdict(set))
        for s in schedule_raw:
            if s.tutor_id:
                time_range = f"{s.start_time.strftime('%H:%M')}–{s.end_time.strftime('%H:%M')}"
                day_name = calendar.day_name[s.schedule_date.weekday()]
                schedule_map[s.tutor_id][time_range].add(day_name)

        final_schedule = {}
        for tutor_id, time_blocks in schedule_map.items():
            blocks = []
            for time_range, days in time_blocks.items():
                ordered_days = sorted(days, key=lambda d: list(calendar.day_name).index(d))
                hari = ", ".join(ordered_days)
                blocks.append(f"{hari} ({time_range})")
            final_schedule[tutor_id] = ", ".join(blocks)

        # Build response
        response_data = []
        for tutor in queryset:
            tutor_id = f"G{tutor.id:03d}"

            # Rating dari siswa (1–5)
            feedbacks = Feedbacks.objects.filter(tutor=tutor).values_list('rating', flat=True)
            feedback_avg = round(sum(feedbacks) / len(feedbacks), 1) if feedbacks else None

            # Rating dari bimbel (tiap field 0–100, nanti disesuaikan ke 0–5)
            admin_ratings = BimbelRating.objects.filter(tutor=tutor)
            admin_raw_avg = round(sum([
                r.professionalism + r.attendance + r.subject_mastery + r.communication
                for r in admin_ratings
            ]) / (4 * len(admin_ratings)), 1) if admin_ratings else None

            # Konversi ke skala 5
            admin_avg = round((admin_raw_avg / 100) * 5, 1) if admin_raw_avg is not None else None

            # Final rating: 70% bimbel, 30% siswa
            final_rating = None
            if admin_avg is not None and feedback_avg is not None:
                final_rating = round(admin_avg * 0.7 + feedback_avg * 0.3, 1)
            elif admin_avg is not None:
                final_rating = admin_avg
            elif feedback_avg is not None:
                final_rating = feedback_avg

            response_data.append({
                "id": tutor.id,
                "full_name": tutor.full_name,
                "tutor_id": tutor_id,
                "subject": tutor.expertise or "-",
                "rating": final_rating,
                "status": "Active" if tutor.user and tutor.user.is_active else "Inactive",
                "schedule": final_schedule.get(tutor.id, "-")
            })

        return Response({
            "tutors": response_data,
            "total": queryset.count()
        }, status=status.HTTP_200_OK)
        
class SubjectListView(APIView):
    def get(self, request):
        subjects = (
            Tutors.objects
            .exclude(expertise__isnull=True)
            .exclude(expertise__exact="")
            .values_list('expertise', flat=True)
            .distinct()
        )
        subject_data = [{"id": idx + 1, "name": sub} for idx, sub in enumerate(subjects)]
        return Response(subject_data, status=status.HTTP_200_OK)