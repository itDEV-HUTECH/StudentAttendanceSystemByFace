from django.urls import path

from . import views

# Create your views here.
urlpatterns = [
    path('', views.home, name='choose_login'),

    path('admin/', views.admin_login_view, name='admin_login'),

    path('lecturer/login', views.lecturer_login_view, name='lecturer_login'),
    path('lecturer/dashboard', views.lecturer_dashboard_view, name='lecturer_dashboard'),

    path('student/login', views.student_login_view, name='student_login'),
    path('student/dashboard', views.student_dashboard_view, name='student_dashboard'),
    path('student/schedule', views.student_schedule_view, name='student_schedule'),
    path('student/profile', views.student_profile_view, name='student_profile'),
    path('student/account-setting', views.student_account_setting_view, name='student_account_setting'),

    path('logout', views.logout_view, name='logout'),
    path('hashpassword', views.hash_password, name='hash_password'),
]
