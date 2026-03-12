from django.urls import path
from . import views

app_name = "attendance"

urlpatterns = [
    path('<int:batch_pk>/', views.session_list, name='sessions'),
    path('<int:batch_pk>/take/', views.take_attendance, name='take'),
    path('<int:batch_pk>/report/', views.student_report, name='report'),
]