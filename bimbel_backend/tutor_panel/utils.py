from accounts.models import Tutors
from datetime import datetime, time

def get_tutor_by_user(user):
    return Tutors.objects.get(user=user)

def get_schedule_status(schedule, reschedule_status=None):
    now = datetime.now()

    start_datetime = datetime.combine(schedule.schedule_date, schedule.start_time)
    end_datetime = datetime.combine(schedule.schedule_date, schedule.end_time)

    if schedule.status == "canceled":
        return "canceled"
    
    if reschedule_status and reschedule_status.lower() == "approved":
        return "reschedule"
    
    if now < start_datetime:
        return "upcoming"
    elif start_datetime <= now <= end_datetime:
        return "on_progress"
    else:
        return "completed"
