from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q

from .models import Course, Batch, Group
from .forms import CourseForm, BatchForm, GroupForm
from enrollments.models import Enrollment


@login_required
def course_list(request):
    query = request.GET.get('q', '')
    courses = Course.objects.select_related('instructor').annotate(
        batch_count=Count('batches', distinct=True),
        student_count=Count('batches__enrollments', distinct=True),
    )
    if query:
        courses = courses.filter(
            Q(title__icontains=query) | Q(code__icontains=query) |
            Q(description__icontains=query)
        )
    # Students only see active courses
    if request.user.is_student:
        courses = courses.filter(status='active')
    return render(request, 'courses/course_list.html', {
        'courses': courses, 'query': query
    })


@login_required
def course_detail(request, pk):
    course = get_object_or_404(Course, pk=pk)
    batches = course.batches.annotate(enrollment_count=Count('enrollments'))
    student_enrolled_batch_ids = []
    if request.user.is_student:
        student_enrolled_batch_ids = list(
            Enrollment.objects.filter(student=request.user, batch__course=course)
            .values_list('batch_id', flat=True)
        )
    return render(request, 'courses/course_detail.html', {
        'course': course,
        'batches': batches,
        'student_enrolled_batch_ids': student_enrolled_batch_ids,
    })


@login_required
def course_create(request):
    if not (request.user.is_admin_role or request.user.is_superuser):
        messages.error(request, 'Permission denied.')
        return redirect('courses:list')
    form = CourseForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Course created successfully!')
        return redirect('courses:list')
    return render(request, 'courses/course_form.html', {'form': form, 'title': 'Create Course'})


@login_required
def course_edit(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if not (request.user.is_admin_role or request.user.is_superuser):
        messages.error(request, 'Permission denied.')
        return redirect('courses:detail', pk=pk)
    form = CourseForm(request.POST or None, request.FILES or None, instance=course)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Course updated successfully!')
        return redirect('courses:detail', pk=pk)
    return render(request, 'courses/course_form.html', {'form': form, 'title': 'Edit Course', 'course': course})


@login_required
def batch_create(request, course_pk):
    course = get_object_or_404(Course, pk=course_pk)
    if not (request.user.is_admin_role or request.user.is_superuser or
            request.user == course.instructor):
        messages.error(request, 'Permission denied.')
        return redirect('courses:detail', pk=course_pk)
    form = BatchForm(request.POST or None, initial={'course': course})
    if request.method == 'POST' and form.is_valid():
        batch = form.save(commit=False)
        batch.course = course
        batch.save()
        messages.success(request, 'Batch created successfully!')
        return redirect('courses:detail', pk=course_pk)
    return render(request, 'courses/batch_form.html', {
        'form': form, 'course': course, 'title': 'Create Batch'
    })


@login_required
def group_create(request, batch_pk):
    batch = get_object_or_404(Batch, pk=batch_pk)
    if not (request.user.is_admin_role or request.user.is_superuser or
            request.user == batch.course.instructor):
        messages.error(request, 'Permission denied.')
        return redirect('courses:detail', pk=batch.course_id)
    form = GroupForm(request.POST or None, batch=batch)
    if request.method == 'POST' and form.is_valid():
        group = form.save(commit=False)
        group.batch = batch
        group.save()
        form.save_m2m()
        messages.success(request, 'Group created successfully!')
        return redirect('courses:detail', pk=batch.course_id)
    return render(request, 'courses/group_form.html', {
        'form': form, 'batch': batch
    })
