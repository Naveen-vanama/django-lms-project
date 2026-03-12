"""URL configuration for myproject."""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .views import home

urlpatterns = [
    path('', home, name='home'), 
    path('admin/', admin.site.urls),
    path('users/', include('users.urls', namespace='users')),
    path('courses/', include('courses.urls', namespace='courses')),
    path('enrollments/', include('enrollments.urls', namespace='enrollments')),
    path('resources/', include('resources.urls', namespace='resources')),
    path('attendance/', include('attendance.urls', namespace='attendance')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)