from datetime import date, timedelta

from django.contrib.auth.hashers import check_password, make_password
from django.shortcuts import render, redirect

from main.models import StudentInfo, Classroom, LecturerInfo


def home(request):
    if 'id_lecturer' in request.session:
        return redirect('lecturer_dashboard')
    if 'id_student' in request.session:
        return redirect('student_dashboard')
    else:
        return render(request, 'choose_login.html')


def admin_login_view(request):
    return render(request, 'admin/admin_login.html')


def lecturer_login_view(request):
    if 'id_lecturer' in request.session:
        return redirect('lecturer_dashboard')

    error_message = None
    if request.method == 'POST':
        id_lecturer = request.POST.get('id_lecturer')
        password = request.POST.get('password')

        try:
            lecturer = LecturerInfo.objects.get(id_lecturer=id_lecturer)
            if check_password(password, lecturer.password):
                request.session['id_lecturer'] = lecturer.id_lecturer
                return redirect('lecturer_dashboard')
            else:
                error_message = "Tên đăng nhập hoặc mật khẩu không đúng."
        except LecturerInfo.DoesNotExist:
            error_message = "Tên đăng nhập hoặc mật khẩu không đúng."

    return render(request, 'lecturer/lecturer_login.html', {'error_message': error_message})


def lecturer_dashboard_view(request):
    if 'id_lecturer' in request.session:
        return render(request, 'lecturer/lecturer_home.html')
    else:
        return redirect('lecturer_login')


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


def logout_view(request):
    if 'id_lecturer' in request.session:
        del request.session['id_lecturer']
    if 'id_student' in request.session:
        del request.session['id_student']
    return redirect('choose_login')


def hash_password(request):
    if request.method == 'POST':
        password = request.POST['password']
        hash_password = make_password(password)
        return render(request, 'hash_password.html', {'hash_password': hash_password})
    else:
        return render(request, 'hash_password.html')
