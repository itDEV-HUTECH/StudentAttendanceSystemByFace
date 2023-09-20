from django.shortcuts import render

from main.decorators import admin_required


@admin_required
def admin_dashboard_view(request):
    return render(request, 'admin/admin_home.html')
