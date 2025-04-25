import uuid
import random
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.utils.html import strip_tags
from datetime import datetime, timedelta
from django.utils.timezone import is_naive, make_aware
from django.contrib.auth.hashers import make_password, check_password
from .models import Users, SignupTokens
from .serializers import SignupSerializer, SigninSerializer, RequestResetSerializer, VerifyResetTokenSerializer, ResetPasswordSerializer
from .utils import generate_simple_token
from django.core.mail import send_mail, EmailMultiAlternatives
from django.urls import reverse

class SignupView(APIView):
    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            token_str = serializer.validated_data['token']

            # Cek apakah email sudah digunakan
            if Users.objects.filter(email=email).exists():
                return Response({'email': 'Email sudah digunakan'}, status=status.HTTP_400_BAD_REQUEST)

            # Cek apakah token valid
            try:
                token = SignupTokens.objects.get(token=token_str, is_used=False)
            except SignupTokens.DoesNotExist:
                return Response({'token': 'Token tidak valid atau sudah digunakan.'}, status=status.HTTP_400_BAD_REQUEST)

            # Simpan user
            hashed_password = make_password(password)
            user = Users.objects.create(
                username=username,
                email=email,
                password=hashed_password,
                role=token.role
            )

            # Tandai token sebagai sudah digunakan
            token.is_used = True
            token.save()

            # Kirim email selamat datang (HTML)
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <body style="font-family: Arial, sans-serif; background-color: #f9f9f9; padding: 20px;">
              <div style="max-width: 600px; margin: auto; background-color: #ffffff; padding: 30px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                <h2 style="color: #6b21a8;">🎓 Selamat Datang di Aplikasi Bimbel!</h2>
                <p>Halo <strong>{username}</strong>,</p>
                <p>Terima kasih telah mendaftar di <strong>Manajemen Bimbel</strong>. Akun kamu berhasil dibuat!</p>

                <h4 style="color: #6b21a8;">📄 Informasi Akun:</h4>
                <ul>
                  <li><strong>Username:</strong> {username}</li>
                  <li><strong>Email:</strong> {email}</li>
                </ul>

                <p>Silakan login ke platform kami dan mulai belajar:</p>
                <a href="http://localhost:3000/auth/signin" style="display:inline-block; padding:10px 20px; background-color:#9333ea; color:white; border-radius:5px; text-decoration:none;">🔐 Login Sekarang</a>

                <p style="margin-top: 30px;">Jika kamu punya pertanyaan, silakan hubungi tim support kami.</p>
                <p>Semangat belajar! 💪</p>
                <p style="color: #aaa;">— Tim Bimbel</p>
              </div>
            </body>
            </html>
            """
            send_mail(
                subject='🎓 Selamat Datang di Aplikasi Bimbel!',
                message=strip_tags(html_content),
                from_email='listarte14@gmail.com',  # atau ganti sesuai config EMAIL_HOST_USER
                recipient_list=[email],
                fail_silently=False,
                html_message=html_content
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

                # === Setup Reset Link ===
                reset_link = f"http://localhost:3000/auth/reset_token?email={email}"

                # === Compose HTML Email ===
                html_content = f"""
                <html>
                  <body style="font-family: Arial, sans-serif; background-color: #f9f9f9; padding: 20px;">
                    <div style="max-width: 600px; margin: auto; background: #fff; padding: 30px; border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
                      <h2 style="color: #6B21A8;">Reset Password Bimbel</h2>
                      <p>Halo <strong>{user.username}</strong>,</p>
                      <p>Kami menerima permintaan untuk mereset password akun kamu.</p>

                      <p style="font-size: 16px;">🔐 Kode OTP kamu adalah:</p>
                      <h1 style="text-align: center; color: #6B21A8;">{token}</h1>

                      <p>Kamu juga bisa langsung klik link berikut untuk melanjutkan proses reset password:</p>
                      <a href="{reset_link}" style="display: inline-block; padding: 10px 20px; background-color: #6B21A8; color: #fff; text-decoration: none; border-radius: 5px;">Verifikasi Sekarang</a>

                      <p style="margin-top: 20px;">⏳ <strong>Catatan:</strong> Kode OTP hanya berlaku selama <strong>10 menit</strong>.</p>

                      <p>Jika kamu tidak merasa melakukan permintaan ini, silakan abaikan email ini.</p>

                      <hr style="margin: 30px 0;">
                      <p style="font-size: 13px; color: #888;">Email ini dikirim otomatis oleh sistem Bimbel App. Jangan membalas email ini.</p>
                      <p style="font-size: 13px; color: #888;">© 2025 Bimbel App. All rights reserved.</p>
                    </div>
                  </body>
                </html>
                """

                # === Kirim Email ===
                subject = '[Bimbel] Reset Password dan Kode OTP Anda'
                text_content = strip_tags(html_content)

                msg = EmailMultiAlternatives(
                    subject=subject,
                    body=text_content,
                    from_email='listarte14@gmail.com',  # Bisa diganti sesuai SMTP-mu
                    to=[email]
                )
                msg.attach_alternative(html_content, "text/html")
                msg.send()

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

