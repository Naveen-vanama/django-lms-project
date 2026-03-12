from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import AttendanceSession, AttendanceRecord
from courses.models import Batch
from enrollments.models import Enrollment


# ==============================
# SESSION LIST
# ==============================
@login_required
def session_list(request, batch_pk):
    batch = get_object_or_404(Batch, pk=batch_pk)
    sessions = batch.sessions.all().order_by('-date')

    return render(request, 'attendance/session_list.html', {
        'batch': batch,
        'sessions': sessions
    })


# ==============================
# TAKE ATTENDANCE
# ==============================
@login_required
def take_attendance(request, batch_pk):
    batch = get_object_or_404(Batch, pk=batch_pk)
    instructor = batch.course.instructor

    if not (request.user == instructor or request.user.is_admin_role or request.user.is_superuser):
        messages.error(request, 'Permission denied.')
        return redirect('attendance:sessions', batch_pk=batch_pk)

    enrolled_students = Enrollment.objects.filter(
        batch=batch,
        status='active'
    ).select_related('student')

    if request.method == 'POST':
        date = request.POST.get('date')
        topic = request.POST.get('topic', '')

        session, _ = AttendanceSession.objects.get_or_create(
            batch=batch,
            date=date,
            defaults={'topic': topic, 'created_by': request.user}
        )

        for enrollment in enrolled_students:
            status = request.POST.get(f'status_{enrollment.student_id}', 'absent')
            note = request.POST.get(f'note_{enrollment.student_id}', '')

            AttendanceRecord.objects.update_or_create(
                session=session,
                student=enrollment.student,
                defaults={
                    'status': status,
                    'note': note
                }
            )

        messages.success(request, f'Attendance saved for {date}.')
        return redirect('attendance:sessions', batch_pk=batch_pk)

    return render(request, 'attendance/take_attendance.html', {
        'batch': batch,
        'enrolled_students': enrolled_students,
        'status_choices': AttendanceRecord.AttendanceStatus.choices,
    })


# ==============================
# STUDENT REPORT
# ==============================
@login_required
def student_report(request, batch_pk):
    batch = get_object_or_404(Batch, pk=batch_pk)

    student = request.user if request.user.is_student else None

    if 'student_id' in request.GET and not request.user.is_student:
        from users.models import CustomUser
        student = get_object_or_404(CustomUser, pk=request.GET['student_id'])

    if not student:
        return redirect('attendance:sessions', batch_pk=batch_pk)

    sessions = batch.sessions.all().order_by('-date')

    record_qs = AttendanceRecord.objects.filter(
        session__batch=batch,
        student=student
    )

    records = {}
    for r in record_qs:
        records[r.session_id] = r.status

    total = sessions.count()
    present = sum(1 for status in records.values() if status == 'present')
    rate = round((present / total) * 100, 1) if total else 0

    return render(request, 'attendance/student_report.html', {
        'batch': batch,
        'student': student,
        'sessions': sessions,
        'records': records,
        'total': total,
        'present': present,
        'rate': rate,
    })