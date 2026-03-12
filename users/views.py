from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import HttpResponseForbidden
import json

from .forms import LoginForm, RegisterForm, ProfileUpdateForm
from .models import CustomUser
from courses.models import Course, Batch
from enrollments.models import Enrollment
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from resources.utils import calculate_progress
from resources.models import ResourceView
from attendance.models import AttendanceRecord
from users.models import Notification
from attendance.models import AttendanceSession
from django.shortcuts import get_object_or_404
from resources.models import Resource

# LOGIN VIEW

def login_view(request):

    if request.user.is_authenticated:
        return redirect('users:redirect_dashboard')

    form = LoginForm(request, data=request.POST or None)

    if request.method == 'POST' and form.is_valid():
        user = form.get_user()

        #  Approval Check
        if not user.is_approved:
            messages.error(request, "Your account is pending admin approval.")
            return redirect('users:login')

        #  Active Check
        if not user.is_active:
            messages.error(request, "Your account is inactive.")
            return redirect('users:login')

        login(request, user)
        messages.success(request, f"Welcome {user.username}!")

        return redirect('users:redirect_dashboard')

    return render(request, 'users/login.html', {'form': form})


# 🔄 ROLE BASED REDIRECT

@login_required
def redirect_dashboard(request):
    user = request.user

    if user.is_admin_role or user.is_superuser:
        return redirect('users:admin_dashboard')

    elif user.is_instructor:
        return redirect('users:instructor_dashboard')

    else:
        return redirect('users:student_dashboard')



# 🔓 LOGOUT

def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('users:login')



# 📝 REGISTER (Pending Approval)

def register_view(request):
    form = RegisterForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        user = form.save(commit=False)

        # 🔒 Require admin approval
        user.is_active = False
        user.is_approved = False
        user.save()

        messages.success(
            request,
            "Registration successful! Your account is under review. "
            "Admin will approve your account soon."
        )

        return redirect('users:login')

    return render(request, 'users/register.html', {'form': form})



# 📊 ADMIN DASHBOARD (ONLY ADMIN)

@login_required
def admin_dashboard(request):

    if not (request.user.is_admin_role or request.user.is_superuser):
        return redirect('users:redirect_dashboard')

    # ================= BASIC COUNTS =================
    total_enrollments = Enrollment.objects.count()
    total_courses = Course.objects.count()
    total_students = CustomUser.objects.filter(role='student').count()
    total_instructors = CustomUser.objects.filter(role='instructor').count()

    # ================= COURSE PERFORMANCE =================
    courses = Course.objects.annotate(
        enrolled_students=Count("batches__enrollments", distinct=True)
    )

    course_names = []
    course_student_counts = []
    course_colors = []

    max_count = max(
        [course.enrolled_students for course in courses],
        default=0
    )

    for course in courses:

        count = course.enrolled_students

        course_names.append(course.title)
        course_student_counts.append(count)

        if max_count > 0:
            percent = int((count / max_count) * 100)
        else:
            percent = 0

        if percent >= 75:
            color = "#22c55e"
        elif percent >= 40:
            color = "#f59e0b"
        else:
            color = "#ef4444"

        course_colors.append(color)
        course.enrolled_students = count
        course_names.append(course.title)
        course_student_counts.append(count)

        if count > max_count:
            max_count = count

    # Second loop → calculate percent + color
    for course in courses:
        if max_count > 0:
            percent = int((course.enrolled_students / max_count) * 100)
        else:
            percent = 0

        course.enrollment_percent = percent

        # Color logic
        if percent >= 75:
            course.color = "#22c55e"   # Green
        elif percent >= 40:
            course.color = "#f59e0b"   # Orange
        else:
            course.color = "#ef4444"   # Red

        course_colors.append(course.color)

    # ================= RISK CALCULATION =================
    enrollments = Enrollment.objects.all()

    high_risk = 0
    medium_risk = 0
    low_risk = 0

    for enrollment in enrollments:
        if enrollment.risk_level == "High":
            high_risk += 1
        elif enrollment.risk_level == "Medium":
            medium_risk += 1
        else:
            low_risk += 1

    risk_data = [low_risk, medium_risk, high_risk]


    # ================= ATTENDANCE TREND =================

    attendance_records = AttendanceRecord.objects.select_related('session')

    attendance_map = {}

    for record in attendance_records:

       # Make sure session and date exist
        if record.session and record.session.date:

            date_str = record.session.date.strftime("%Y-%m-%d")

            if date_str not in attendance_map:
                attendance_map[date_str] = 0

            attendance_map[date_str] += 1


        # Sort dates for chart
        attendance_dates = sorted(attendance_map.keys())
        attendance_counts = [attendance_map[d] for d in attendance_dates]

    # ================= CONTEXT =================
    context = {
        "total_enrollments": total_enrollments,
        "total_courses": total_courses,
        "total_students": total_students,
        "total_instructors": total_instructors,
        "courses": courses,
        "course_names": json.dumps(course_names),
        "course_student_counts": json.dumps(course_student_counts),
        "risk_data": json.dumps(risk_data),
        "course_colors": json.dumps(course_colors),

        # NEW DATA FOR CHART
        "attendance_dates": json.dumps(attendance_dates),
        "attendance_counts": json.dumps(attendance_counts),
    }

    return render(request, "users/admin_dashboard.html", context)

# INSTRUCTOR DASHBOARD

@login_required
def instructor_dashboard(request):

    user = request.user

    if not user.is_instructor:
        return HttpResponseForbidden("Access Denied")

    instructor_courses = Course.objects.filter(
        instructor=user
    ).annotate(
        enrollment_count=Count('batches__enrollments', distinct=True)
    )

    total_students = Enrollment.objects.filter(
        batch__course__instructor=user
    ).values('student').distinct().count()

    recent_batches = Batch.objects.filter(
        course__instructor=user
    ).order_by('-created_at')[:5]

    context = {
        'courses': instructor_courses,
        'total_students': total_students,
        'recent_batches': recent_batches,
    }

    return render(request, 'users/instructor_dashboard.html', context)



# 🎓 STUDENT DASHBOARD

@login_required
def student_dashboard(request):

    user = request.user

    if not user.is_student:
        return HttpResponseForbidden("Access Denied")

    enrollments = Enrollment.objects.filter(
        student=user
    ).select_related(
        'batch__course',
        'batch__course__instructor'
    )

    risk_messages = []

    for enrollment in enrollments:
        course = enrollment.batch.course

        # ---------- COURSE PROGRESS ----------
        enrollment.progress = calculate_progress(user, course)

        # ---------- ATTENDANCE CALCULATION ----------

        enrollment.attendance_percent = enrollment.attendance_rate



        # ---------- HIGH RISK ----------
        if enrollment.risk_level == "High":

            message = f"You are at HIGH risk in {course.title}. Please contact your instructor immediately."

            risk_messages.append(message)

            if not Notification.objects.filter(
                user=user,
                message__icontains=course.title
            ).exists():

                Notification.objects.create(
                    user=user,
                    message=message
                )

        # ---------- MEDIUM RISK ----------
        elif enrollment.risk_level == "Medium":

            message = f"You are at MEDIUM risk in {course.title}. Improve attendance and complete resources."

            risk_messages.append(message)

            if not Notification.objects.filter(
                user=user,
                message__icontains=course.title
            ).exists():

                Notification.objects.create(
                    user=user,
                    message=message
                )

    context = {
        'enrollments': enrollments,
        'total_courses': enrollments.count(),
        'risk_messages': risk_messages
    }

    return render(request, 'users/student_dashboard.html', context)

# 👤 PROFILE
@login_required
def profile_view(request):

    form = ProfileUpdateForm(
        request.POST or None,
        request.FILES or None,
        instance=request.user
    )

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Profile updated successfully!")
        return redirect('users:profile')

    return render(request, 'users/profile.html', {'form': form})

User = get_user_model()

def forgot_password(request):

    if request.method == "POST":

        email = request.POST.get("email")

        user = User.objects.filter(email=email).first()

        # ❌ If email not found
        if not user:
            messages.error(request, "User does not exist")
            return redirect("users:forgot_password")

        # ✅ Generate OTP
        otp = random.randint(100000, 999999)

        request.session["reset_email"] = email
        request.session["otp"] = str(otp)

        print("OTP:", otp)  # debug

        # ✅ Send Email
        send_mail(
            "Password Reset OTP",
            f"Your OTP for password reset is: {otp}",
            settings.EMAIL_HOST_USER,
            [email],
            fail_silently=False,
        )

        messages.success(request, "OTP sent to your email")

        return redirect("users:verify_otp")

    return render(request, "users/forgot_password.html")

def verify_otp(request):

    if request.method == "POST":

        entered_otp = request.POST.get("otp")
        session_otp = request.session.get("otp")

        if entered_otp == session_otp:
            request.session.pop("otp", None)
            messages.success(request, "OTP verified successfully")
            return redirect("users:reset_password")

        else:
            messages.error(request, "Invalid OTP")
            return redirect("users:verify_otp")

    return render(request, "users/verify_otp.html")

def resend_otp(request):

    email = request.session.get("reset_email")

    # If session expired
    if not email:
        messages.error(request, "Session expired. Please try again.")
        return redirect("users:forgot_password")

    # Generate new OTP
    otp = random.randint(100000, 999999)

    # Save OTP in session
    request.session["otp"] = str(otp)

    # Send email
    send_mail(
        "Password Reset OTP",
        f"Your new OTP is: {otp}",
        settings.EMAIL_HOST_USER,
        [email],
        fail_silently=False,
    )

    print("Resent OTP:", otp)  # debug

    messages.success(request, "New OTP sent to your email")

    return redirect("users:verify_otp")

def reset_password(request):

    email = request.session.get("reset_email")

    if request.method == "POST":

        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if password != confirm_password:
            messages.error(request, "Passwords do not match")
            return redirect("users:reset_password")

        user = User.objects.filter(email=email).first()

        user.set_password(password)
        user.save()

        messages.success(request, "Password reset successful")

        return redirect("users:login")

    return render(request, "users/reset_password.html")

import random
from django.contrib import messages

@login_required
def dashboard_data(request):

    courses = Course.objects.all()

    course_names = []
    course_student_counts = []
    course_colors = []

    max_count = 0

    for course in courses:
        count = Enrollment.objects.filter(batch__course=course).count()

        course_names.append(course.title)
        course_student_counts.append(count)

        if count > max_count:
            max_count = count

    # Calculate colors
    for count in course_student_counts:

        if max_count > 0:
            percent = int((count / max_count) * 100)
        else:
            percent = 0

        if percent >= 75:
            color = "#22c55e"
        elif percent >= 40:
            color = "#f59e0b"
        else:
            color = "#ef4444"

        course_colors.append(color)

    return JsonResponse({
        "course_names": course_names,
        "course_counts": course_student_counts,
        "course_colors": course_colors
    })

@login_required
def resource_detail(request, pk):

    resource = get_object_or_404(Resource, pk=pk)

    # track resource view
    ResourceView.objects.get_or_create(
        student=request.user,
        resource=resource
    )

    return render(request, "resources/resource_detail.html", {
        "resource": resource
    })