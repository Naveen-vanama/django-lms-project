from django.urls import path
from . import views

app_name = "users"

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('redirect/', views.redirect_dashboard, name='redirect_dashboard'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('instructor-dashboard/', views.instructor_dashboard, name='instructor_dashboard'),
    path('student-dashboard/', views.student_dashboard, name='student_dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path("forgot-password/", views.forgot_password, name="forgot_password"),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path("reset-password/", views.reset_password, name="reset_password"),
    path("resend-otp/", views.resend_otp, name="resend_otp"),
    path("dashboard-data/", views.dashboard_data, name="dashboard_data"),
]