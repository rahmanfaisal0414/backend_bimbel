from rest_framework import serializers
from accounts.models import Students, Tutors

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


