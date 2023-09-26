from django.urls import path

from main.view import admin_views
from main.view import lecturer_views
from main.view import student_views
from . import views

# Create your views here.
urlpatterns = [
    path('', views.home, name='choose_login'),
    path('login', views.login_view, name='login'),

    # Admin
    path('admin/dashboard', admin_views.admin_dashboard_view, name='admin_dashboard'),
    path('admin/profile', admin_views.admin_profile_view, name='admin_profile'),
    path('admin/change-password', admin_views.admin_change_password_view, name='admin_change_password'),
    path('admin/student-management', admin_views.admin_student_management_view, name='admin_student_management'),
    path('admin/student-management/delete/<int:id_student>', admin_views.admin_student_delete,
         name='admin_student_delete'),

    # Lecturer
    path('lecturer/dashboard', lecturer_views.lecturer_dashboard_view, name='lecturer_dashboard'),
    path('lecturer/schedule', lecturer_views.lecturer_schedule_view, name='lecturer_schedule'),
    path('lecturer/profile', lecturer_views.lecturer_profile_view, name='lecturer_profile'),
    path('lecturer/change-password', lecturer_views.lecturer_change_password_view, name='lecturer_change_password'),
    path('lecturer/attendance', lecturer_views.lecturer_attendance_class_view, name='lecturer_attendance'),
    path('lecturer/attendance/<int:classroom_id>', lecturer_views.lecturer_mark_attendance,
         name='lecturer_mark_attendance'),
    path('lecturer/attendance-by-face/', lecturer_views.lecturer_mark_attendance_by_face,
         name='lecturer_mark_attendance_by_face'),
    path('lecturer/attendance-history', lecturer_views.lecturer_attendance_history_view,
         name='lecturer_attendance_history'),

    # Student
    path('student/login', student_views.student_login_view, name='student_login'),
    path('student/dashboard', student_views.student_dashboard_view, name='student_dashboard'),
    path('student/schedule', student_views.student_schedule_view, name='student_schedule'),
    path('student/profile', student_views.student_profile_view, name='student_profile'),
    path('student/change-password', student_views.student_change_password_view, name='student_change_password'),

    # Staff

    path('logout', views.logout_view, name='logout'),

    # Error
    path('error/403', views.error_403_view, name='error_403'),
    path('error/404', views.error_404_view, name='error_404'),
    path('error/405', views.error_404_view, name='error_405'),
    path('error/500', views.error_500_view, name='error_500'),

    path('hashpassword', views.hash_password, name='hash_password'),
]
