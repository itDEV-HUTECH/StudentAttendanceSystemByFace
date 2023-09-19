from django.shortcuts import render


def admin_dashboard_view(request):
    if 'id_staff' in request.session:
        return render(request, 'admin/admin_dashboard.html')
    else:
        return render(request, 'login.html')
