from datetime import datetime

def get_schedule_status(schedule, reschedule_status=None):
    if schedule.status == "Canceled":
        return "canceled"
    if reschedule_status == "Pending":
        return "rescheduled"

    now = datetime.now()
    start = datetime.combine(schedule.schedule_date, schedule.start_time)
    end = datetime.combine(schedule.schedule_date, schedule.end_time)

    if now < start:
        return "upcoming"
    elif start <= now <= end:
        return "on_progress"
    else:
        return "completed"