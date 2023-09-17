from django.urls import path

from main.view import admin_views
from main.view import lecturer_views
from main.view import student_views
from . import views

# Create your views here.
urlpatterns = [
    path('', views.home, name='choose_login'),

    path('admin/', admin_views.admin_login_view, name='admin_login'),

    path('lecturer/login', lecturer_views.lecturer_login_view, name='lecturer_login'),
    path('lecturer/dashboard', lecturer_views.lecturer_dashboard_view, name='lecturer_dashboard'),

    path('lecturer/profile', lecturer_views.lecturer_profile_view, name='lecturer_profile'),
    path('lecturer/change-password', lecturer_views.lecturer_change_password_view, name='lecturer_change_password'),

    path('student/login', student_views.student_login_view, name='student_login'),
    path('student/dashboard', student_views.student_dashboard_view, name='student_dashboard'),
    path('student/schedule', student_views.student_schedule_view, name='student_schedule'),
    path('student/profile', student_views.student_profile_view, name='student_profile'),
    path('student/change-password', student_views.student_change_password_view, name='student_change_password'),

    path('logout', views.logout_view, name='logout'),
    path('hashpassword', views.hash_password, name='hash_password'),
]
