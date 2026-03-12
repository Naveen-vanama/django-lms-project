from django.db import models
from django.conf import settings


class Course(models.Model):
    """A course offered by the college."""

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        INACTIVE = 'inactive', 'Inactive'
        ARCHIVED = 'archived', 'Archived'

    title = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)

    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='courses_teaching',
        limit_choices_to={'role': 'instructor'},
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE
    )

    thumbnail = models.ImageField(
        upload_to='course_thumbnails/',
        blank=True,
        null=True
    )

    credits = models.PositiveSmallIntegerField(default=3)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.code} – {self.title}"


# =====================================================


class Batch(models.Model):
    """A specific run/section of a course."""

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='batches'
    )

    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()

    max_students = models.PositiveIntegerField(default=30)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_date']
        verbose_name_plural = 'Batches'

    def __str__(self):
        return f"{self.course.code} – {self.name}"

    @property
    def enrolled_count(self):
        return self.course_enrollments.count()

    @property
    def is_full(self):
        return self.enrolled_count >= self.max_students


# =====================================================


class Group(models.Model):
    """A sub-group within a batch."""

    batch = models.ForeignKey(
        Batch,
        on_delete=models.CASCADE,
        related_name='groups'
    )

    name = models.CharField(max_length=100)

    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='course_groups',
        blank=True,
        limit_choices_to={'role': 'student'},
    )

    def __str__(self):
        return f"{self.batch} – {self.name}"


# =====================================================
# ENROLLMENT MODEL (FIXED related_name)
# =====================================================

class Enrollment(models.Model):
    """Student enrollment in a batch."""

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='course_enrollments',   # ✅ FIXED
        limit_choices_to={'role': 'student'},
    )

    batch = models.ForeignKey(
        Batch,
        on_delete=models.CASCADE,
        related_name='course_enrollments'   # ✅ FIXED
    )

    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'batch')

    def __str__(self):
        return f"{self.student} → {self.batch}"


# =====================================================
# RESOURCE MODEL (FIXED related_name)
# =====================================================

class Resource(models.Model):
    """Learning materials for a batch."""

    batch = models.ForeignKey(
        Batch,
        on_delete=models.CASCADE,
        related_name='course_resources'   # ✅ FIXED
    )

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    video = models.FileField(
        upload_to='videos/',
        blank=True,
        null=True
    )

    file = models.FileField(
        upload_to='resources/',
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title