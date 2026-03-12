from django.contrib.auth.models import AbstractUser
from django.db import models
import random
from django.conf import settings
from datetime import timedelta
from django.utils import timezone

class CustomUser(AbstractUser):

    class Role(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        INSTRUCTOR = 'instructor', 'Instructor'
        STUDENT = 'student', 'Student'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT,
    )

    phone = models.CharField(max_length=20)
    profile_picture = models.ImageField(
        upload_to='profile_pictures/', blank=True, null=True
    )
    bio = models.TextField(blank=True)
    date_of_birth = models.DateField(null=True, blank=True)

    # 🔥 NEW FIELD
    is_approved = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    # ── Convenience properties ─────────────────────────
    @property
    def is_admin_role(self):
        return self.role == self.Role.ADMIN

    @property
    def is_instructor(self):
        return self.role == self.Role.INSTRUCTOR

    @property
    def is_student(self):
        return self.role == self.Role.STUDENT

class PasswordResetOTP(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=5)

class Notification(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications"
    )

    message = models.CharField(max_length=255)

    is_read = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.message}"