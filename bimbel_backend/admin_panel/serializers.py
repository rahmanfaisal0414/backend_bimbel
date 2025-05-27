from rest_framework import serializers
from accounts.models import Students, Tutors, Classes, Schedules, Materials, Feedbacks, Users

class AdminStudentManagementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Students
        fields = ['id', 'full_name']

class AdminStudentDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Students
        fields = '__all__'
        
class TutorListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tutors
        fields = '__all__'
        
class AddClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = Classes
        fields = '__all__'

class AddScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Schedules
        fields = '__all__'

# serializers.py
class MaterialListSerializer(serializers.ModelSerializer):
    class_field = serializers.CharField(source='class_field.class_name')
    tutor = serializers.CharField(source='tutor.full_name', default=None)

    class Meta:
        model = Materials
        fields = '__all__'
        
class FeedbackRawSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedbacks
        fields = '__all__'
        
class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = ['full_name', 'phone', 'address', 'bio']


