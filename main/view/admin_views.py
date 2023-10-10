from datetime import datetime

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.hashers import check_password, make_password
from django.core.paginator import Paginator
from django.shortcuts import render, redirect

from main.decorators import admin_required
from main.models import StaffInfo, StudentInfo


@admin_required
def admin_dashboard_view(request):
    return render(request, 'admin/admin_home.html')


@admin_required
def admin_profile_view(request):
    id_admin = request.session['id_staff']
    admin = StaffInfo.objects.get(id_staff=id_admin)

    if request.method == 'POST':
        admin.staff_name = request.POST['admin_name']
        admin.email = request.POST['email']
        admin.phone = request.POST['phone']
        admin.address = request.POST['address']
        admin.birthday = datetime.strptime(request.POST['birthday'], '%d/%m/%Y').date()
        admin.save()
        messages.success(request, 'Thay đổi thông tin thành công.')

    context = {'admin': admin}

    return render(request, 'admin/admin_profile.html', context)


@admin_required
def admin_change_password_view(request):
    id_admin = request.session['id_staff']
    admin = StaffInfo.objects.get(id_staff=id_admin)

    if request.method == 'POST':
        old_password = request.POST['old_password']
        new_password = request.POST['new_password']
        confirm_password = request.POST['confirm_password']

        if check_password(old_password, admin.password):
            if new_password == confirm_password:
                admin.password = make_password(new_password)
                admin.save()
                update_session_auth_hash(request, admin)
                messages.success(request, 'Đổi mật khẩu thành công.')
            else:
                messages.error(request, 'Mật khẩu mới không khớp.')
        else:
            messages.error(request, 'Mật khẩu cũ không đúng.')

    return render(request, 'admin/admin_change_password.html')


@admin_required
def admin_student_management_view(request):
    students = StudentInfo.objects.all()
    per_page = 10
    paginator = Paginator(students, per_page)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    context = {
        'list_students': page,
    }
    return render(request, 'admin/admin_student_management.html', context)


@admin_required
def admin_student_add(request):
    if request.method == 'POST':
        id_student = request.POST['id_student']
        student_name = request.POST['student_name']
        email = request.POST['email']
        phone = request.POST['phone']
        address = request.POST['address']
        birthday = datetime.strptime(request.POST['birthday'], '%d/%m/%Y').date()
        PathImageFolder = request.POST['PathImageFolder']
        password = make_password(request.POST['id_student'])
        student = StudentInfo(id_student=id_student,
                              student_name=student_name,
                              email=email, phone=phone,
                              address=address,
                              birthday=birthday,
                              PathImageFolder=PathImageFolder,
                              password=password)
        student.save()
        messages.success(request, 'Thêm sinh viên thành công.')
        return redirect('admin_student_management')
    return render(request, 'admin/modal-popup/popup_add_student.html')

@admin_required
def admin_student_delete(request, id_student):
    StudentInfo.objects.filter(id_student=id_student).delete()
    return redirect('admin_student_management')
