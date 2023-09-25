from datetime import datetime

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.hashers import check_password, make_password
from django.shortcuts import render, redirect

from main.decorators import admin_required
from main.models import StaffInfo, StudentInfo


@admin_required
def admin_dashboard_view(request):
    return render(request, 'admin/admin_home.html')


@admin_required
def admin_profile_view(request):
    if 'id_staff' in request.session:
        id_staff = request.session['id_staff']
        try:
            admin = StaffInfo.objects.get(id_staff=id_staff)

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
        except StaffInfo.DoesNotExist:
            return redirect('login')
    else:
        request.session['next_url'] = request.path
        return redirect('login')


@admin_required
def admin_change_password_view(request):
    if 'id_staff' in request.session:
        id_staff = request.session['id_staff']

        try:
            admin = StaffInfo.objects.get(id_staff=id_staff)

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

        except StaffInfo.DoesNotExist:
            return redirect('login')
    else:
        request.session['next_url'] = request.path
        return redirect('login')


@admin_required
def admin_student_management_view(request):
    students = StudentInfo.objects.all()
    context = {'list_students': students}
    return render(request, 'admin/admin_student_management.html', context)
