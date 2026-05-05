from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('logout/', views.logout_view, name='logout'),

    # OTP SYSTEM
    path('otp-request/', views.otp_request, name='otp_request'),
    path('otp-verify/', views.otp_verify, name='otp_verify'),
    path('reset-password/', views.reset_password, name='reset_password'),
]