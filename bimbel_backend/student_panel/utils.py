from accounts.models import Students, Users

def get_student_by_user(user):
    return Students.objects.get(user=user)

def get_student_by_user_my_schedule(user_id):
    try:
        user = Users.objects.get(id=user_id)
        if user.role != "student":
            raise Exception("User bukan student")
        return Students.objects.get(user=user)
    except:
        raise Exception("Student tidak valid")
