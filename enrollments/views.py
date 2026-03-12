from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from courses.models import Batch
from .models import Enrollment
from users.models import CustomUser
import uuid
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from .models import Certificate
from django.db.models import Q
from courses.models import Course

@login_required
def enroll(request, batch_pk):

    batch = get_object_or_404(Batch, pk=batch_pk)
    course = batch.course
    student = request.user

    if not student.is_student:
        messages.error(request, "Only students can enroll.")
        return redirect('courses:detail', pk=course.pk)

    # 🔴 CHECK if student already enrolled in another batch of same course
    existing = Enrollment.objects.filter(
        student=student,
        batch__course=course,
        status='active'
    ).exists()

    if existing:
        messages.warning(request, "You are already enrolled in another batch of this course.")
        return redirect('courses:detail', pk=course.pk)

    # Batch capacity check
    if batch.is_full:
        status = Enrollment.Status.WAITLISTED
        messages.warning(request, "Batch is full. Added to waitlist.")
    else:
        status = Enrollment.Status.ACTIVE

    Enrollment.objects.create(
        student=student,
        batch=batch,
        status=status
    )

    messages.success(request, "Enrollment successful!")
    return redirect('courses:detail', pk=course.pk)

@login_required
def unenroll(request, batch_pk):

    if not (request.user.is_admin_role or request.user.is_superuser):
        messages.error(request, "Only admin can drop enrollments.")
        return redirect('courses:list')

    batch = get_object_or_404(Batch, pk=batch_pk)

    Enrollment.objects.filter(
        student=request.user,
        batch=batch
    ).update(status=Enrollment.Status.DROPPED)

    messages.info(request, f'Dropped from {batch}.')
    return redirect('courses:detail', pk=batch.course_id)


def enrollment_list(request):
    """Admin / instructor view of all enrollments."""

    search_query = request.GET.get('q', '')
    course_filter = request.GET.get('course', '')
    risk_filter = request.GET.get('risk', '')

    if request.user.is_student:
        enrollments = Enrollment.objects.filter(
            student=request.user
        ).select_related('batch__course', 'batch__course__instructor')

    elif request.user.is_instructor:
        enrollments = Enrollment.objects.filter(
            batch__course__instructor=request.user
        ).select_related('student', 'batch__course')

    else:
        enrollments = Enrollment.objects.select_related(
            'student','batch','batch__course'
        ).order_by('-enrolled_at')

    # 🔍 Search
    if search_query:
        enrollments = enrollments.filter(
            Q(student__username__icontains=search_query) |
            Q(student__email__icontains=search_query) |
            Q(student__id__icontains=search_query)
        )

    # 📚 Course Filter
    if course_filter:
        enrollments = enrollments.filter(batch__course__id=course_filter)

    # ⚠ Risk Filter
    if risk_filter:
        enrollments = enrollments.filter(risk_level=risk_filter)

    courses = Course.objects.all()

    context = {
        'enrollments': enrollments,
        'search_query': search_query,
        'courses': courses,
        'selected_course': course_filter,
        'selected_risk': risk_filter
    }

    return render(request, 'enrollments/enrollment_list.html', context)

@login_required
def grade_update(request, pk):
    """Instructor updates a student's grade."""
    enrollment = get_object_or_404(Enrollment, pk=pk)
    if not (request.user == enrollment.batch.course.instructor or
            request.user.is_admin_role or request.user.is_superuser):
        messages.error(request, 'Permission denied.')
        return redirect('enrollments:list')

    if request.method == 'POST':
        grade = request.POST.get('grade', '').strip()
        enrollment.grade = grade
        enrollment.save(update_fields=['grade'])
        messages.success(request, 'Grade updated.')
    return redirect('enrollments:list')

@login_required
def generate_certificate(request, enrollment_id):

    enrollment = get_object_or_404(Enrollment, id=enrollment_id)

    student = enrollment.student
    course = enrollment.batch.course

    certificate_id = str(uuid.uuid4())

    certificate = Certificate.objects.create(
        student=student,
        course=course,
        certificate_id=certificate_id
    )

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="certificate.pdf"'

    p = canvas.Canvas(response)

    p.setFont("Helvetica-Bold", 24)
    p.drawString(200, 750, "Course Completion Certificate")

    p.setFont("Helvetica", 16)
    p.drawString(200, 700, f"This certifies that")

    p.setFont("Helvetica-Bold", 18)
    p.drawString(200, 670, student.username)

    p.setFont("Helvetica", 16)
    p.drawString(200, 640, f"has successfully completed")

    p.setFont("Helvetica-Bold", 18)
    p.drawString(200, 610, course.title)

    p.drawString(200, 560, f"Certificate ID: {certificate_id}")

    p.save()

    return response