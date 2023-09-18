from django.contrib.auth.hashers import make_password
from django.shortcuts import render, redirect


def home(request):
    if 'id_lecturer' in request.session:
        return redirect('lecturer_dashboard')
    if 'id_student' in request.session:
        return redirect('student_dashboard')
    else:
        return render(request, 'choose_login.html')


def logout_view(request):
    request.session.clear()
    return redirect('choose_login')


def hash_password(request):
    if request.method == 'POST':
        password = request.POST['password']
        hash_password = make_password(password)
        return render(request, 'hash_password.html', {'hash_password': hash_password})
    else:
        return render(request, 'hash_password.html')
