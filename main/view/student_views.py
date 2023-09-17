from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.hashers import make_password, check_password
from django.http import Http404
from django.shortcuts import redirect, render

from main.models import StudentInfo, Classroom


def student_login_view(request):
    if request.user.is_authenticated:
        return redirect('student_dashboard')

    error_message = None
    next_url = request.session.get('next_url')
    if request.method == 'POST':
        id_student = request.POST.get('id_student')
        password = request.POST.get('password')

        try:
            student = StudentInfo.objects.get(id_student=id_student)
            if check_password(password, student.password):
                request.session['id_student'] = student.id_student
                if next_url:
                    return redirect(next_url)
                else:
                    return redirect('student_dashboard')
            else:
                error_message = "Tên đăng nhập hoặc mật khẩu không đúng."
        except StudentInfo.DoesNotExist:
            error_message = "Tên đăng nhập hoặc mật khẩu không đúng."

    return render(request, 'student/student_login.html', {'error_message': error_message})


def student_dashboard_view(request):
    if 'id_student' in request.session:
        return render(request, 'student/student_home.html')
    else:
        return redirect('student_login')


def student_schedule_view(request):
    id_student = request.session.get('id_student')
    week_start_param = request.GET.get('week_start')

    if id_student is not None:
        if week_start_param:
            try:
                week_start = date.fromisoformat(week_start_param)
            except ValueError:
                raise Http404("Invalid date format for week_start parameter")
        else:
            today = date.today()
            week_start = today - timedelta(days=today.weekday())

        end_of_week = week_start + timedelta(days=6)

        # Lọc lớp học dựa trên id sinh viên và tuần hiện tại
        student_classes = Classroom.objects.filter(
            students__id_student=id_student,
            begin_date__lte=end_of_week,
            end_date__gte=week_start
        )

        previous_week_start = week_start - timedelta(days=7)
        next_week_start = week_start + timedelta(days=7)

        previous_week_start = previous_week_start.strftime("%Y-%m-%d")
        next_week_start = next_week_start.strftime("%Y-%m-%d")

        context = {
            'student_classes': student_classes,
            'start_of_week': week_start,
            'end_of_week': end_of_week,
            'previous_week_start': previous_week_start,
            'next_week_start': next_week_start,
        }
        return render(request, 'student/student_schedule.html', context)
    else:
        request.session['next_url'] = request.path
        return redirect('student_login')


def student_profile_view(request):
    if 'id_student' in request.session:
        id_student = request.session['id_student']
        try:
            student = StudentInfo.objects.get(id_student=id_student)

            if request.method == 'POST':
                student.student_name = request.POST['student_name']
                student.email = request.POST['email']
                student.phone = request.POST['phone']
                student.address = request.POST['address']
                student.birthday = request.POST['birthday']
                student.save()
                messages.success(request, 'Thay đổi thông tin thành công.')
            context = {'student': student}
            return render(request, 'student/student_profile.html', context)
        except StudentInfo.DoesNotExist:
            return redirect('student_login')
    else:
        request.session['next_url'] = request.path
        return redirect('student_login')


def student_change_password_view(request):
    if 'id_student' in request.session:
        id_student = request.session['id_student']

        try:
            student = StudentInfo.objects.get(id_student=id_student)

            if request.method == 'POST':
                old_password = request.POST['old_password']
                new_password = request.POST['new_password']
                confirm_password = request.POST['confirm_password']

                if check_password(old_password, student.password):
                    if new_password == confirm_password:
                        student.password = make_password(new_password)
                        student.save()
                        update_session_auth_hash(request, student)
                        messages.success(request, 'Đổi mật khẩu thành công.')
                    else:
                        messages.error(request, 'Mật khẩu mới không khớp.')
                else:
                    messages.error(request, 'Mật khẩu cũ không đúng.')

            return render(request, 'student/student_change_password.html')

        except StudentInfo.DoesNotExist:
            return redirect('student_login')
    else:
        request.session['next_url'] = request.path
        return redirect('student_login')
