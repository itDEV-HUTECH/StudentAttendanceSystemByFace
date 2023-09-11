from datetime import date, timedelta

from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string

from main.models import LecturerInfo, StudentInfo, Classroom


def home(request):
    if 'id_lecturer' in request.session:
        return redirect('lecturer_dashboard')
    if 'id_student' in request.session:
        return redirect('student_dashboard')
    else:
        return render(request, 'choose_login.html')


def admin_login_view(request):
    return render(request, 'admin/admin_login.html')


def lecturer_login_view(request):
    if 'id_lecturer' in request.session:
        return redirect('lecturer_dashboard')

    error_message = None
    if request.method == 'POST':
        id_lecturer = request.POST.get('id_lecturer')
        password = request.POST.get('password')

        try:
            lecturer = LecturerInfo.objects.get(id_lecturer=id_lecturer, password=password)
            request.session['id_lecturer'] = lecturer.id_lecturer
            return redirect('lecturer_dashboard')
        except LecturerInfo.DoesNotExist:
            error_message = "Tên đăng nhập hoặc mật khẩu không đúng."
    return render(request, 'lecturer/lecturer_login.html', {'error_message': error_message})


def lecturer_dashboard_view(request):
    if 'id_lecturer' in request.session:
        return render(request, 'lecturer/lecturer_home.html')
    else:
        return redirect('lecturer_login')


def student_login_view(request):
    if 'id_student' in request.session:
        return redirect('student_dashboard')

    error_message = None
    if request.method == 'POST':
        id_student = request.POST.get('id_student')
        password = request.POST.get('password')

        try:
            student = StudentInfo.objects.get(id_student=id_student, password=password)
            request.session['id_student'] = student.id_student
            return redirect('student_dashboard')
        except StudentInfo.DoesNotExist:
            error_message = "Tên đăng nhập hoặc mật khẩu không đúng."
    return render(request, 'student/student_login.html', {'error_message': error_message})


def student_dashboard_view(request):
    if 'id_student' in request.session:
        return render(request, 'student/student_home.html')
    else:
        return redirect('student_login')


def student_schedule_view(request):
    id_student = request.session.get('id_student')

    if id_student is not None:
        today = date.today()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)

        student_classes = Classroom.objects.filter(
            students__id_student=id_student,
            begin_date__lte=end_of_week,
            end_date__gte=start_of_week
        )

        context = {'student_classes': student_classes}
        return render(request, 'student/student_schedule.html', context)
    else:
        # Nếu không có id_student trong session, xử lý theo yêu cầu của bạn, ví dụ chuyển hướng đến trang đăng nhập
        return redirect('student_dashboard')


def student_profile_view(request):
    if 'id_student' in request.session:
        id_student = request.session['id_student']
        try:
            student = StudentInfo.objects.get(id_student=id_student)

            if request.method == 'POST':
                student.student_name = request.POST['student_name']
                student.email = request.POST['email']
                student.phone = request.POST['phone']
                student.address = request.POST['address']
                student.birthday = request.POST['birthday']
                student.save()
            context = {'student': student}
            return render(request, 'student/student_profile.html', context)
        except StudentInfo.DoesNotExist:
            return redirect('student_login')
    else:
        return redirect('student_login')


def get_classroom_details(request, classroom_id):
    classroom = get_object_or_404(Classroom, id_classroom=classroom_id)

    # Tạo một template để hiển thị thông tin lớp học
    classroom_details_template = 'student/classroom_details.html'

    # Render template thành chuỗi HTML
    classroom_details_html = render_to_string(classroom_details_template, {'classroom': classroom})

    # Trả về thông tin lớp học trong dạng JSON
    return JsonResponse({'classroom_details_html': classroom_details_html})


def logout_view(request):
    if 'id_lecturer' in request.session:
        del request.session['id_lecturer']
    if 'id_student' in request.session:
        del request.session['id_student']
    return redirect('choose_login')
