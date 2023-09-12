from django.shortcuts import render


def admin_login_view(request):
    return render(request, 'admin/admin_login.html')
