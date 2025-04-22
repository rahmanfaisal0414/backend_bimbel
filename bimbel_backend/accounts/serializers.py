from rest_framework import serializers

class SignupSerializer(serializers.Serializer):
    username = serializers.CharField()
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    token = serializers.CharField(write_only=True)


class SigninSerializer(serializers.Serializer):
    identifier = serializers.CharField()
    password = serializers.CharField()

class RequestResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

class VerifyResetTokenSerializer(serializers.Serializer):
    email = serializers.EmailField()
    token = serializers.CharField(max_length=6)

class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
