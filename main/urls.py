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
    path('admin/student-management/add', admin_views.admin_student_add, name='admin_student_add'),
    path('admin/student-management/delete/<int:id_student>', admin_views.admin_student_delete,
         name='admin_student_delete'),
    path('admin/student-management/edit/<int:id_student>', admin_views.admin_student_edit, name='admin_student_edit'),
    path('admin/student-management/get-info/<int:id_student>', admin_views.admin_student_get_info,
         name='admin_student_get_info'),
    path('admin/student-management/train', admin_views.train, name='train'),
    path('admin/student-management/live_video_feed/<int:id_student>', admin_views.live_video_feed,
         name='live_video_feed'),
    path('admin/student-management/delete/<int:id_student>', admin_views.admin_student_delete,
         name='admin_student_delete'),
    path('admin/student-management/check_capture_status/', admin_views.check_capture_status,
         name='check_capture_status'),

    # Lecturer
    path('admin/student-management/student_capture', admin_views.student_capture, name='student_capture'),
    path('admin/student-management/capture/cap', admin_views.capture, name='capture'),
    path('lecturer/dashboard', lecturer_views.lecturer_dashboard_view, name='lecturer_dashboard'),
    path('lecturer/schedule', lecturer_views.lecturer_schedule_view, name='lecturer_schedule'),
    path('lecturer/profile', lecturer_views.lecturer_profile_view, name='lecturer_profile'),
    path('lecturer/change-password', lecturer_views.lecturer_change_password_view, name='lecturer_change_password'),
    path('lecturer/attendance', lecturer_views.lecturer_attendance_class_view, name='lecturer_attendance'),
    path('lecturer/attendance/<int:classroom_id>', lecturer_views.lecturer_mark_attendance,
         name='lecturer_mark_attendance'),
    path('lecturer/attendance-by-face/<int:classroom_id>', lecturer_views.lecturer_mark_attendance_by_face,
         name='lecturer_mark_attendance_by_face'),
    path('lecturer/attendance-history', lecturer_views.lecturer_attendance_history_view,
         name='lecturer_attendance_history'),
    path('lecturer/live_video_feed', lecturer_views.live_video_feed, name='live_video_feed'),
    path('lecturer/live_video_feed2/<int:classroom_id>', lecturer_views.live_video_feed2, name='live_video_feed2'),
    path('lecturer/list-classroom', lecturer_views.lecturer_list_classroom_view,
         name='lecturer_list_classroom'),
    path('lecturer/calculate-attendance-points/<int:classroom_id>', lecturer_views.lecturer_calculate_attendance_points_view,
         name='lecturer_calculate_attendance_points'),

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
