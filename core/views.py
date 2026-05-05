from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings

import random
import time


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

    return render(request, "dashboard.html", {
        "username": request.user.username
    })


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

        # 🔥 CHECK USER EXISTS
        if not User.objects.filter(email=email).exists():
            return render(request, "otp_request.html", {
                "error": "No account with this email ❌"
            })

        otp = generate_otp()

        OTP_STORE[email] = {
            "otp": otp,
            "time": time.time()
        }

        # 🔥 SEND EMAIL
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

        # 🔥 CHECK EXPIRY
        if time.time() - stored_data["time"] > OTP_EXPIRY_TIME:
            OTP_STORE.pop(email, None)
            return render(request, "otp_verify.html", {
                "error": "OTP expired. Request new one ❌"
            })

        # 🔥 CHECK OTP
        if stored_data["otp"] == user_otp:
            OTP_STORE.pop(email, None)  # remove after success
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

        # 🔥 PASSWORD MATCH CHECK
        if password1 != password2:
            return render(request, "rest_password.html", {
                "error": "Passwords do not match ❌"
            })

        try:
            user = User.objects.get(email=email)
            user.set_password(password1)
            user.save()

            # 🔥 CLEANUP
            request.session.pop('email', None)

            messages.success(request, "Password reset successful ✅")
            return redirect("login")

        except User.DoesNotExist:
            return render(request, "rest_password.html", {
                "error": "User not found ❌"
            })

    return render(request, "rest_password.html")