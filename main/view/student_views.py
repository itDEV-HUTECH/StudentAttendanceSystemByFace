from datetime import date, timedelta

from django.contrib.auth.hashers import check_password
from django.shortcuts import redirect, render

from main.models import StudentInfo, Classroom


def student_login_view(request):
    if 'id_student' in request.session:
        return redirect('student_dashboard')

    error_message = None
    if request.method == 'POST':
        id_student = request.POST.get('id_student')
        password = request.POST.get('password')

        try:
            student = StudentInfo.objects.get(id_student=id_student)
            if check_password(password, student.password):
                request.session['id_student'] = student.id_student
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

    if id_student is not None:
        today = date.today()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)

        student_classes = Classroom.objects.filter(
            students__id_student=id_student,
        )

        context = {
            'student_classes': student_classes,
            'start_of_week': start_of_week,
            'end_of_week': end_of_week,
        }
        return render(request, 'student/student_schedule.html', context)
    else:
        return redirect('student_dashboard')


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
            context = {'student': student}
            return render(request, 'student/student_profile.html', context)
        except StudentInfo.DoesNotExist:
            return redirect('student_login')
    else:
        return redirect('student_login')


def student_account_setting_view(request):
    return render(request, 'student/student_account_setting.html')
