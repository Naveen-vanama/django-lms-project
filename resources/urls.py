from django.urls import path
from . import views

app_name = 'resources'

urlpatterns = [
    path('course/<int:course_pk>/', views.resource_list, name='list'),
    path('course/<int:course_pk>/upload/', views.resource_upload, name='upload'),
    path('<int:pk>/delete/', views.resource_delete, name='delete'),
    path('stream/<int:pk>/', views.stream_video, name='stream_video'),
    path("track/<int:resource_id>/", views.track_resource, name="track"),

]