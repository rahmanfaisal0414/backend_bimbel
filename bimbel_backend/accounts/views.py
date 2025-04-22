import uuid
import random
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from datetime import datetime, timedelta
from django.utils.timezone import is_naive, make_aware
from django.contrib.auth.hashers import make_password, check_password
from .models import Users, SignupTokens
from .serializers import SignupSerializer, SigninSerializer, RequestResetSerializer, VerifyResetTokenSerializer, ResetPasswordSerializer
from .utils import generate_simple_token
from django.core.mail import send_mail
from django.urls import reverse

class SignupView(APIView):
    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            token_str = serializer.validated_data['token']

            if Users.objects.filter(email=email).exists():
                return Response({'email': 'Email sudah digunakan'}, status=status.HTTP_400_BAD_REQUEST)

            try:
                token = SignupTokens.objects.get(token=token_str, is_used=False)
            except SignupTokens.DoesNotExist:
                return Response({'token': 'Token tidak valid atau sudah digunakan.'}, status=status.HTTP_400_BAD_REQUEST)

            hashed_password = make_password(password)
            user = Users.objects.create(
                username=username,
                email=email,
                password=hashed_password,
                role=token.role
            )

            token.is_used = True
            token.save()

            # Kirim notifikasi email
            send_mail(
                subject='Selamat Datang di Aplikasi Bimbel!',
                message=f"Halo {username}, akun kamu berhasil dibuat di platform Bimbel 🎉\n\nSelamat belajar!",
                from_email=None,
                recipient_list=[email],
                fail_silently=False
            )

            return Response({'message': 'Signup berhasil', 'user_id': user.id}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SigninView(APIView):
    def post(self, request):
        serializer = SigninSerializer(data=request.data)
        if serializer.is_valid():
            identifier = serializer.validated_data['identifier']
            password = serializer.validated_data['password']

            try:
                user = Users.objects.get(username=identifier)
            except Users.DoesNotExist:
                try:
                    user = Users.objects.get(email=identifier)
                except Users.DoesNotExist:
                    return Response({'error': 'Username/Email tidak ditemukan'}, status=status.HTTP_404_NOT_FOUND)

            if check_password(password, user.password):
                return Response({
                    'message': 'Login berhasil',
                    'user_id': user.id,
                    'role': user.role
                })

            return Response({'error': 'Password salah'}, status=status.HTTP_401_UNAUTHORIZED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# BONUS: Admin bisa generate token langsung
class GenerateSignupTokenView(APIView):
    def post(self, request):
        role = request.data.get('role')
        if role not in ['student', 'tutor']:
            return Response({'error': 'Role tidak valid'}, status=status.HTTP_400_BAD_REQUEST)

        # Cari token unik yang belum pernah dipakai
        while True:
            token = generate_simple_token()
            if not SignupTokens.objects.filter(token=token).exists():
                break

        SignupTokens.objects.create(token=token, role=role, is_used=False)
        return Response({'token': token}, status=status.HTTP_201_CREATED)
    
class RequestPasswordResetView(APIView):
    def post(self, request):
        serializer = RequestResetSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = Users.objects.get(email=email)
                token = str(random.randint(100000, 999999))

                user.reset_token = token
                user.reset_token_created_at = timezone.now()
                user.save()

                # === Kirim Email ke Gmail ===
                reset_link = f"http://localhost:3000/auth/reset_token?email={email}"  # frontend Next.js
                message = f"""
Halo {user.username},

Berikut adalah kode OTP untuk reset password akun Bimbel kamu:

🔒 Kode OTP: {token}

Atau langsung klik link berikut untuk verifikasi:
{reset_link}

Kode berlaku selama 10 menit.

Terima kasih,
Tim Bimbel
"""
                send_mail(
                    subject='Reset Password Bimbel - OTP Anda',
                    message=message,
                    from_email=None,
                    recipient_list=[email],
                    fail_silently=False
                )

                return Response({'message': 'Kode reset berhasil dikirim ke email'}, status=200)

            except Users.DoesNotExist:
                return Response({'error': 'Email tidak ditemukan'}, status=404)

        return Response(serializer.errors, status=400)


class VerifyResetTokenView(APIView):
    def post(self, request):
        serializer = VerifyResetTokenSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            token = serializer.validated_data['token']
            try:
                user = Users.objects.get(email=email, reset_token=token)

                created_at = user.reset_token_created_at
                if created_at and is_naive(created_at):
                    created_at = make_aware(created_at)

                if created_at and timezone.now() - created_at > timedelta(minutes=10):
                    return Response({'error': 'Token kedaluwarsa'}, status=400)

                return Response({'message': 'Token valid'}, status=200)

            except Users.DoesNotExist:
                return Response({'error': 'Token tidak valid'}, status=400)
        return Response(serializer.errors, status=400)


class ResetPasswordView(APIView):
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            new_password = serializer.validated_data['new_password']
            confirm_password = serializer.validated_data['confirm_password']

            if new_password != confirm_password:
                return Response({'error': 'Password tidak cocok'}, status=400)

            try:
                user = Users.objects.get(email=email)
                user.password = make_password(new_password)
                user.reset_token = None
                user.reset_token_created_at = None
                user.save()
                return Response({'message': 'Password berhasil direset'}, status=200)
            except Users.DoesNotExist:
                return Response({'error': 'User tidak ditemukan'}, status=404)

        return Response(serializer.errors, status=400)

