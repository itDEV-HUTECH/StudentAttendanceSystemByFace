from django.shortcuts import render, redirect

from main.models import LecturerInfo, StudentInfo


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
            lecturer = LecturerInfo.objects.get(id_lecturer=id_lecturer, password=password)
            request.session['id_lecturer'] = lecturer.id_lecturer
            return redirect('lecturer_dashboard')
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
            student = StudentInfo.objects.get(id_student=id_student, password=password)
            request.session['id_student'] = student.id_student
            return redirect('student_dashboard')
        except StudentInfo.DoesNotExist:
            error_message = "Tên đăng nhập hoặc mật khẩu không đúng."
    return render(request, 'student/student_login.html', {'error_message': error_message})


def student_dashboard_view(request):
    if 'id_student' in request.session:
        return render(request, 'student/student_home.html')
    else:
        return redirect('student_login')


def logout_view(request):
    if 'id_lecturer' in request.session:
        del request.session['id_lecturer']
    if 'id_student' in request.session:
        del request.session['id_student']
    return redirect('choose_login')


def student_schedule_view(request):
    return render(request, 'student/student_schedule.html')


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
