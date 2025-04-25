from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from datetime import date
from accounts.models import Tutors, Students, Classes, Schedules

class AdminDashboardView(APIView):
    def get(self, request):
        stats = {
            "Total Tutor": Tutors.objects.filter(is_deleted=False).count(),
            "Total Student": Students.objects.filter(is_deleted=False).count(),
            "Total Class": Classes.objects.filter(is_deleted=False).count(),
            "Average Attendance": "96%"  # Placeholder sementara
        }

        today = date.today()
        schedules = Schedules.objects.filter(schedule_date=today)
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
