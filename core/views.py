from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.http import HttpResponseRedirect

import random
import time

from .models import Student, Level, Semester, Course


# =========================
# 🔹 GLOBAL OTP STORAGE
# =========================
OTP_STORE = {}
OTP_EXPIRY_TIME = 300  # 5 minutes


def generate_otp():
    return str(random.randint(100000, 999999))


# =========================
# 🔹 HOME
# =========================
def home(request):
    return redirect("login")


# =========================
# 🔹 REGISTER
# =========================
def register(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        if password1 != password2:
            messages.error(request, "Passwords do not match ❌")
            return redirect("register")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists ❌")
            return redirect("register")

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1
        )

        # Create Student instance
        Student.objects.create(
            user=user,
            full_name=username,
            matric_number="",
            faculty="",
            department="",
            program=""
        )

        login(request, user)
        messages.success(request, "Account created successfully ✅")
        return redirect("dashboard")

    return render(request, "register.html")


# =========================
# 🔹 LOGIN
# =========================
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            messages.success(request, f"Welcome back {username} 👋")
            return redirect("dashboard")
        else:
            messages.error(request, "Invalid username or password ❌")
            return redirect("login")

    return render(request, "index.html")


# =========================
# 🔹 DASHBOARD
# =========================
def dashboard(request):
    if not request.user.is_authenticated:
        return redirect("login")

    # Get or create Student
    student, created = Student.objects.get_or_create(
        user=request.user,
        defaults={
            'full_name': request.user.username,
            'matric_number': '',
            'faculty': '',
            'department': '',
            'program': ''
        }
    )

    # Get all courses for this student
    courses = Course.objects.filter(
        semester__level__student=student
    ).select_related('semester__level')

    # Calculate CGPA
    total_units = 0
    total_points = 0
    grade_map = {'A': 5, 'B': 4, 'C': 3, 'D': 2, 'E': 1, 'F': 0}

    for course in courses:
        total_units += course.unit
        total_points += course.unit * grade_map.get(course.grade, 0)

    cgpa = total_points / total_units if total_units > 0 else 0

    if cgpa >= 4.5:
        remark = "First Class"
    elif cgpa >= 3.5:
        remark = "Second Class Upper"
    elif cgpa >= 2.5:
        remark = "Second Class Lower"
    elif cgpa >= 1.5:
        remark = "Third Class"
    else:
        remark = "Fail"

    return render(request, "dashboard.html", {
        "username": request.user.username,
        "student": student,
        "courses": courses,
        "cgpa": cgpa,
        "remark": remark
    })


# =========================
# 🔹 SAVE STUDENT PROFILE
# =========================
def save_student(request):
    if not request.user.is_authenticated:
        return redirect("login")

    if request.method == "POST":
        student = Student.objects.get(user=request.user)
        student.full_name = request.POST.get("full_name")
        student.matric_number = request.POST.get("matric_number")
        student.faculty = request.POST.get("faculty")
        student.department = request.POST.get("department")
        student.program = request.POST.get("program")
        student.save()
        messages.success(request, "Profile saved successfully ✅")

    return redirect("dashboard")


# =========================
# 🔹 ADD COURSE
# =========================
def add_course(request):
    if not request.user.is_authenticated:
        return redirect("login")

    if request.method == "POST":
        student = Student.objects.get(user=request.user)

        level_num = int(request.POST.get("level"))
        semester_name = request.POST.get("semester")
        title = request.POST.get("title")
        code = request.POST.get("code")
        unit = int(request.POST.get("unit"))
        grade = request.POST.get("grade")

        # Get or create Level
        level, created = Level.objects.get_or_create(
            student=student,
            level=level_num,
            defaults={'gpa': 0, 'locked': False}
        )

        # Get or create Semester
        semester, created = Semester.objects.get_or_create(
            level=level,
            name=semester_name,
            defaults={'gpa': 0}
        )

        # Create Course
        Course.objects.create(
            semester=semester,
            title=title,
            code=code,
            unit=unit,
            grade=grade
        )

        messages.success(request, "Course added successfully ✅")

    return redirect("dashboard")


# =========================
# 🔹 DELETE COURSE
# =========================
def delete_course(request, course_id):
    if not request.user.is_authenticated:
        return redirect("login")

    if request.method == "POST":
        try:
            course = Course.objects.get(
                id=course_id,
                semester__level__student__user=request.user
            )
            course.delete()
            messages.success(request, "Course deleted successfully ✅")
        except Course.DoesNotExist:
            messages.error(request, "Course not found ❌")

    return redirect("dashboard")


# =========================
# 🔹 LOGOUT
# =========================
def logout_view(request):
    logout(request)
    return redirect("login")


# =========================
# 🔹 REQUEST OTP
# =========================
def otp_request(request):
    if request.method == "POST":
        email = request.POST.get("email")

        if not User.objects.filter(email=email).exists():
            return render(request, "otp_request.html", {
                "error": "No account with this email ❌"
            })

        otp = generate_otp()

        OTP_STORE[email] = {
            "otp": otp,
            "time": time.time()
        }

        send_mail(
            subject="Your OTP Code",
            message=f"Your OTP is {otp}. It expires in 5 minutes.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )

        request.session['email'] = email
        return redirect('otp_verify')

    return render(request, "otp_request.html")


# =========================
# 🔹 VERIFY OTP
# =========================
def otp_verify(request):
    email = request.session.get('email')

    if not email:
        return redirect('otp_request')

    if request.method == "POST":
        user_otp = request.POST.get("otp")
        stored_data = OTP_STORE.get(email)

        if not stored_data:
            return render(request, "otp_verify.html", {
                "error": "OTP expired. Request again ❌"
            })

        if time.time() - stored_data["time"] > OTP_EXPIRY_TIME:
            OTP_STORE.pop(email, None)
            return render(request, "otp_verify.html", {
                "error": "OTP expired. Request new one ❌"
            })

        if stored_data["otp"] == user_otp:
            OTP_STORE.pop(email, None)
            return redirect('reset_password')
        else:
            return render(request, "otp_verify.html", {
                "error": "Invalid OTP ❌"
            })

    return render(request, "otp_verify.html")


# =========================
# 🔹 RESET PASSWORD
# =========================
def reset_password(request):
    email = request.session.get('email')

    if not email:
        return redirect('otp_request')

    if request.method == "POST":
        password1 = request.POST.get("password")
        password2 = request.POST.get("confirm_password")

        if password1 != password2:
            return render(request, "rest_password.html", {
                "error": "Passwords do not match ❌"
            })

        try:
            user = User.objects.get(email=email)
            user.set_password(password1)
            user.save()

            request.session.pop('email', None)

            messages.success(request, "Password reset successful ✅")
            return redirect("login")

        except User.DoesNotExist:
            return render(request, "rest_password.html", {
                "error": "User not found ❌"
            })

    return render(request, "rest_password.html")
