from django.db import models
from django.conf import settings
from django.utils import timezone
from courses.models import Batch
from courses.models import Course



class Enrollment(models.Model):

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        DROPPED = 'dropped', 'Dropped'
        COMPLETED = 'completed', 'Completed'
        WAITLISTED = 'waitlisted', 'Waitlisted'

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='enrollments',
        limit_choices_to={'role': 'student'},
    )

    batch = models.ForeignKey(
        Batch,
        on_delete=models.CASCADE,
        related_name='enrollments',
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE
    )

    enrolled_at = models.DateTimeField(auto_now_add=True)

    grade = models.CharField(max_length=5, blank=True)

    end_date = models.DateField(
        null=True,
        blank=True,
        help_text="Student access end date"
    )

    class Meta:
        unique_together = ('student', 'batch')
        ordering = ['-enrolled_at']

    def __str__(self):
        return f"{self.student.username} → {self.batch}"

    # ---------------------------
    # ACCESS CONTROL
    # ---------------------------

    @property
    def is_expired(self):
        if self.end_date:
            return self.end_date < timezone.now().date()
        return False

    @property
    def days_remaining(self):
        if self.end_date:
            remaining = (self.end_date - timezone.now().date()).days
            return remaining if remaining > 0 else 0
        return None

    # ---------------------------
    # ATTENDANCE RATE
    # ---------------------------

    @property
    def attendance_rate(self):
        from attendance.models import AttendanceRecord

        total = AttendanceRecord.objects.filter(
            session__batch=self.batch,
            student=self.student
        ).count()

        present = AttendanceRecord.objects.filter(
            session__batch=self.batch,
            student=self.student,
            status='present'
        ).count()

        if total == 0:
            return 0

        return round((present / total) * 100, 1)

    # ---------------------------
    # RISK LEVEL
    # ---------------------------

    @property
    def risk_level(self):
        rate = self.attendance_rate

        if rate >= 85:
            return "Low"
        elif rate >= 60:
            return "Medium"
        return "High"

    # ---------------------------
    # SUCCESS SCORE
    # ---------------------------

    @property
    def success_score(self):
        grade_score_map = {
            "A+": 95,
            "A": 90,
            "B+": 85,
            "B": 75,
            "C": 65,
        }

        grade_score = grade_score_map.get(self.grade, 70)
        attendance_score = self.attendance_rate

        return round((attendance_score * 0.6) + (grade_score * 0.4), 1)

class Certificate(models.Model):

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE
    )

    issued_at = models.DateTimeField(auto_now_add=True)

    certificate_id = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return f"{self.student} - {self.course}"