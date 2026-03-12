from .models import ResourceView, Resource
from courses.models import Course
from users.models import CustomUser
from resources.models import FileResource


def calculate_progress(student, course):

    # Total resources in the course
    total_resources = FileResource.objects.filter(course=course).count()

    if total_resources == 0:
        return 0

    # Resources viewed by student
    viewed_resources = ResourceView.objects.filter(
        student=student,
        resource__course=course
    ).count()

    progress = (viewed_resources / total_resources) * 100

    return round(progress, 1)