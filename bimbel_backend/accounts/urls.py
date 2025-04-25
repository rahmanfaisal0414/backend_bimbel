from django.urls import path
from .views import SignupView, SigninView, GenerateSignupTokenView, RequestPasswordResetView, VerifyResetTokenView, ResetPasswordView

urlpatterns = [
    path('signup/', SignupView.as_view()),
    path('signin/', SigninView.as_view()),
    path('generate-token/', GenerateSignupTokenView.as_view()),
    
       # RESET PASSWORD
    path('request-reset/', RequestPasswordResetView.as_view()),
    path('verify-reset-token/', VerifyResetTokenView.as_view()),
    path('reset-password/', ResetPasswordView.as_view()),
    
    
]

