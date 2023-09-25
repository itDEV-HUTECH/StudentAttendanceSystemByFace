from datetime import date, timedelta, datetime

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.hashers import check_password, make_password
from django.http import Http404
from django.shortcuts import redirect, render

from main.decorators import lecturer_required
from main.models import StaffInfo, Classroom, StudentClassDetails, Attendance


@lecturer_required
def lecturer_dashboard_view(request):
    return render(request, 'lecturer/lecturer_home.html')


@lecturer_required
def lecturer_schedule_view(request):
    id_staff = request.session.get('id_staff')
    week_start_param = request.GET.get('week_start')

    if id_staff is not None:
        if week_start_param:
            try:
                week_start = date.fromisoformat(week_start_param)
            except ValueError:
                raise Http404("Invalid date format for week_start parameter")
        else:
            today = date.today()
            week_start = today - timedelta(days=today.weekday())

        end_of_week = week_start + timedelta(days=6)

        lecturer_classes = Classroom.objects.filter(
            id_lecturer__id_staff=id_staff,
            begin_date__lte=end_of_week,
            end_date__gte=week_start
        )

        previous_week_start = week_start - timedelta(days=7)
        next_week_start = week_start + timedelta(days=7)

        previous_week_start = previous_week_start.strftime("%Y-%m-%d")
        next_week_start = next_week_start.strftime("%Y-%m-%d")

        context = {
            'lecturer_classes': lecturer_classes,
            'start_of_week': week_start,
            'end_of_week': end_of_week,
            'previous_week_start': previous_week_start,
            'next_week_start': next_week_start,
        }
        return render(request, 'lecturer/lecturer_schedule.html', context)
    else:
        request.session['next_url'] = request.path
        return redirect('login')


@lecturer_required
def lecturer_profile_view(request):
    if 'id_staff' in request.session:
        id_staff = request.session['id_staff']
        try:
            lecturer = StaffInfo.objects.get(id_staff=id_staff)

            if request.method == 'POST':
                lecturer.staff_name = request.POST['lecturer_name']
                lecturer.email = request.POST['email']
                lecturer.phone = request.POST['phone']
                lecturer.address = request.POST['address']
                lecturer.birthday = datetime.strptime(request.POST['birthday'], '%d/%m/%Y').date()
                lecturer.save()
                messages.success(request, 'Thay đổi thông tin thành công.')
            context = {'lecturer': lecturer}
            return render(request, 'lecturer/lecturer_profile.html', context)
        except StaffInfo.DoesNotExist:
            return redirect('login')
    else:
        request.session['next_url'] = request.path
        return redirect('login')


@lecturer_required
def lecturer_change_password_view(request):
    if 'id_staff' in request.session:
        id_staff = request.session['id_staff']

        try:
            lecturer = StaffInfo.objects.get(id_staff=id_staff)

            if request.method == 'POST':
                old_password = request.POST['old_password']
                new_password = request.POST['new_password']
                confirm_password = request.POST['confirm_password']

                if check_password(old_password, lecturer.password):
                    if new_password == confirm_password:
                        lecturer.password = make_password(new_password)
                        lecturer.save()
                        update_session_auth_hash(request, lecturer)
                        messages.success(request, 'Đổi mật khẩu thành công.')
                    else:
                        messages.error(request, 'Mật khẩu mới không khớp.')
                else:
                    messages.error(request, 'Mật khẩu cũ không đúng.')

            return render(request, 'lecturer/lecturer_change_password.html')

        except StaffInfo.DoesNotExist:
            return redirect('login')
    else:
        request.session['next_url'] = request.path
        return redirect('login')


@lecturer_required
def lecturer_attendance_class_view(request):
    id_staff = request.session.get('id_staff')

    if id_staff is not None:
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        end_of_week = week_start + timedelta(days=6)

        lecturer_classes = Classroom.objects.filter(
            id_lecturer__id_staff=id_staff,
            begin_date__lte=end_of_week,
            end_date__gte=week_start
        )

        day_of_week_today = today.isoweekday()

        context = {
            'lecturer_classes': lecturer_classes,
            'start_of_week': week_start,
            'end_of_week': end_of_week,
            'day_of_week_today': day_of_week_today,
        }

        return render(request, 'lecturer/lecturer_attendance_class.html', context)
    else:
        request.session['next_url'] = request.path
        return redirect('login')


def lecturer_mark_attendance(request, classroom_id):
    classroom = Classroom.objects.get(pk=classroom_id)
    students_in_class = StudentClassDetails.objects.filter(id_classroom=classroom)
    attendance_list = Attendance.objects.filter(id_classroom=classroom)
    day_of_week_today = date.today().isoweekday()
    if day_of_week_today != classroom.day_of_week_begin:
        return redirect('lecturer_attendance')
    elif request.method == 'POST':
        for student in students_in_class:
            student_id = student.id_student
            attendance_status = request.POST.get(f'attendance_status_{student_id.id_student}')

            attendance = Attendance.objects.filter(
                id_student=student_id,
                id_classroom=classroom,
                check_in_time__date=datetime.now().date()
            ).first()

            if attendance:
                attendance.attendance_status = attendance_status
                attendance.check_in_time = datetime.now()
                attendance.save()
            else:
                attendance = Attendance.objects.create(
                    id_student=student_id,
                    id_classroom=classroom,
                    check_in_time=datetime.now(),
                    attendance_status=attendance_status
                )

        return redirect('lecturer_mark_attendance', classroom_id=classroom_id)

    context = {'students_in_class': students_in_class,
               'classroom': classroom,
               'attendance_list': attendance_list}
    return render(request, 'lecturer/lecturer_mask_attendance.html', context)


def lecturer_attendance_history_view(request):
    return render(request, 'lecturer/lecturer_attendance_history.html')
