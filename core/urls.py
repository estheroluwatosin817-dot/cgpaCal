from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('logout/', views.logout_view, name='logout'),

    # Save student profile
    path('save-student/', views.save_student, name='save_student'),

    # Add course
    path('add-course/', views.add_course, name='add_course'),

    # Delete course
    path('delete-course/<int:course_id>/', views.delete_course, name='delete_course'),

    # OTP SYSTEM
    path('otp-request/', views.otp_request, name='otp_request'),
    path('otp-verify/', views.otp_verify, name='otp_verify'),
    path('reset-password/', views.reset_password, name='reset_password'),
]
