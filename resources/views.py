from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import Http404, HttpResponse
from django.conf import settings
import os
import mimetypes

from .models import FileResource
from .forms import FileResourceForm
from courses.models import Course
from .models import ResourceView
from resources.models import ResourceView
from django.http import JsonResponse

# ======================================================
# RESOURCE LIST (Separated by Type)
# ======================================================

@login_required
def resource_list(request, course_pk):

    course = get_object_or_404(Course, pk=course_pk)

    resources = FileResource.objects.filter(
        course=course,
        is_visible=True
    )

    # 👇 Student Batch Filtering
    if request.user.is_student:
        from enrollments.models import Enrollment

        enrolled_batch_ids = Enrollment.objects.filter(
            student=request.user,
            batch__course=course
        ).values_list('batch_id', flat=True)

        resources = resources.filter(
            Q(batch__in=enrolled_batch_ids) | Q(batch__isnull=True)
        )

    # ⭐ NEW CODE (TRACK RESOURCE VIEW)
    from resources.models import ResourceView

    if request.user.is_student:
        for res in resources:
            ResourceView.objects.get_or_create(
                student=request.user,
                resource_id=res.id
                )

    # 👇 Separate by Type
    context = {
        "course": course,
        "videos": resources.filter(resource_type="video"),
        "lectures": resources.filter(resource_type="lecture"),
        "assignments": resources.filter(resource_type="assignment"),
        "readings": resources.filter(resource_type="reading"),
        "others": resources.filter(resource_type="other"),
    }

    return render(request, "resources/resource_list.html", context)

# ======================================================
# RESOURCE UPLOAD
# ======================================================

@login_required
def resource_upload(request, course_pk):
    course = get_object_or_404(Course, pk=course_pk)

    can_upload = (
        request.user == course.instructor or
        request.user.is_admin_role or
        request.user.is_superuser
    )

    if not can_upload:
        messages.error(request, 'Only instructors and admins can upload resources.')
        return redirect('resources:list', course_pk=course_pk)

    form = FileResourceForm(request.POST or None, request.FILES or None, course=course)

    if request.method == 'POST' and form.is_valid():
        resource = form.save(commit=False)
        resource.course = course
        resource.uploaded_by = request.user
        resource.save()

        messages.success(request, 'Resource uploaded successfully!')
        return redirect('resources:list', course_pk=course_pk)

    return render(request, 'resources/resource_form.html', {
        'form': form,
        'course': course
    })


# ======================================================
# RESOURCE DELETE
# ======================================================

@login_required
def resource_delete(request, pk):
    resource = get_object_or_404(FileResource, pk=pk)
    course_pk = resource.course_id

    can_delete = (
        request.user == resource.uploaded_by or
        request.user.is_admin_role or
        request.user.is_superuser
    )

    if not can_delete:
        messages.error(request, 'Permission denied.')
    else:
        resource.delete()
        messages.success(request, 'Resource deleted.')

    return redirect('resources:list', course_pk=course_pk)


# ======================================================
# VIDEO STREAMING (Forward/Backward Support)
# ======================================================

@login_required
def stream_video(request, pk):
    resource = get_object_or_404(FileResource, pk=pk)

    if not resource.file:
        raise Http404("No video file found")

    file_path = resource.file.path

    if not os.path.exists(file_path):
        raise Http404("File not found")

    file_size = os.path.getsize(file_path)
    content_type, _ = mimetypes.guess_type(file_path)

    range_header = request.headers.get('Range', None)

    # 🔹 If no range header → normal response
    if not range_header:
        response = HttpResponse(open(file_path, 'rb'), content_type=content_type)
        response['Content-Length'] = file_size
        response['Accept-Ranges'] = 'bytes'
        return response

    # 🔹 If range header exists (for seek/forward/backward)
    range_value = range_header.replace('bytes=', '')
    start, end = range_value.split('-')

    start = int(start)
    end = int(end) if end else file_size - 1

    length = end - start + 1

    with open(file_path, 'rb') as f:
        f.seek(start)
        data = f.read(length)

    response = HttpResponse(data, status=206, content_type=content_type)
    response['Content-Range'] = f'bytes {start}-{end}/{file_size}'
    response['Accept-Ranges'] = 'bytes'
    response['Content-Length'] = str(length)

    return response



@login_required
def resource_detail(request, pk):

    resource = get_object_or_404(Resource, pk=pk)

    ResourceView.objects.get_or_create(
        student=request.user,
        resource=resource
    )

    return render(request, "resources/resource_detail.html", {
        "resource": resource
    })

@login_required
def track_resource(request, resource_id):

    resource = FileResource.objects.get(id=resource_id)

    ResourceView.objects.get_or_create(
        student=request.user,
        resource=resource
    )

    return JsonResponse({"status":"ok"})