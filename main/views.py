from django.contrib.auth.hashers import make_password, check_password
from django.shortcuts import render, redirect

from main.models import StaffInfo


def home(request):
    if 'id_staff' in request.session:
        if 'Admin' in request.session['staff_role']:
            return redirect('admin_dashboard')
        elif 'Lecturer' in request.session['staff_role']:
            return redirect('lecturer_dashboard')
    if 'id_student' in request.session:
        return redirect('student_dashboard')
    else:
        return render(request, 'choose_login.html')


role_to_dashboard = {
    'Admin': 'admin_dashboard',
    'Lecturer': 'lecturer_dashboard',
    'Staff': 'staff_dashboard'
}


def login_view(request):
    if 'id_staff' in request.session:
        if 'Admin' in request.session['staff_role']:
            return redirect('admin_dashboard')
        elif 'Lecturer' in request.session['staff_role']:
            return redirect('lecturer_dashboard')

    error_message = None
    if request.method == 'POST':
        id_staff = request.POST.get('id_staff')
        password = request.POST.get('password')

        try:
            lecturer = StaffInfo.objects.get(id_staff=id_staff)
            if check_password(password, lecturer.password):
                user_roles = lecturer.roles.all()
                request.session['id_staff'] = id_staff
                request.session['staff_role'] = [role.name for role in user_roles]
                for role in user_roles:
                    if role.name in role_to_dashboard:
                        return redirect(role_to_dashboard[role.name])

                error_message = "Vai trò không hợp lệ."

            else:
                error_message = "Tên đăng nhập hoặc mật khẩu không đúng."
        except StaffInfo.DoesNotExist:
            error_message = "Tên đăng nhập hoặc mật khẩu không đúng."

    return render(request, 'login.html', {'error_message': error_message})


def logout_view(request):
    request.session.clear()
    return redirect('choose_login')


def error_403_view(request):
    return render(request, 'error/error-403.html')


def hash_password(request):
    if request.method == 'POST':
        password = request.POST['password']
        hash_password = make_password(password)
        return render(request, 'hash_password.html', {'hash_password': hash_password})
    else:
        return render(request, 'hash_password.html')
