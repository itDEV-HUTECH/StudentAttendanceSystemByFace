from django.contrib import messages
from django.contrib.auth.hashers import check_password
from django.shortcuts import redirect, render

from main.models import LecturerInfo


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


def lecturer_schedule_view(request):
    if 'id_lecturer' in request.session:
        return render(request, 'lecturer/lecturer_schedule.html')
    else:
        return redirect('lecturer_login')


def lecturer_profile_view(request):
    if 'id_lecturer' in request.session:
        id_lecturer = request.session['id_lecturer']
        try:
            lecturer = LecturerInfo.objects.get(id_lecturer=id_lecturer)

            if request.method == 'POST':
                lecturer.lecturer_name = request.POST['lecturer_name']
                lecturer.email = request.POST['email']
                lecturer.phone = request.POST['phone']
                lecturer.address = request.POST['address']
                lecturer.birthday = request.POST['birthday']
                lecturer.save()
                messages.success(request, 'Thay đổi thông tin thành công.')
            context = {'lecturer': lecturer}
            return render(request, 'lecturer/lecturer_profile.html', context)
        except LecturerInfo.DoesNotExist:
            return redirect('lecturer_login')
    else:
        request.session['next_url'] = request.path
        return redirect('lecturer_login')
