from django.urls import path
from .views import SignupView, SigninView, GenerateSignupTokenView, RequestPasswordResetView, VerifyResetTokenView, ResetPasswordView

urlpatterns = [
    path('auth/signup/', SignupView.as_view()),
    path('auth/signin/', SigninView.as_view()),
    path('auth/generate-token/', GenerateSignupTokenView.as_view()),
    
       # RESET PASSWORD
    path('auth/request-reset/', RequestPasswordResetView.as_view()),
    path('auth/verify-reset-token/', VerifyResetTokenView.as_view()),
    path('auth/reset-password/', ResetPasswordView.as_view()),
]

