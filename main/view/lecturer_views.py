import os
import time
from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.hashers import check_password, make_password
from django.core.paginator import Paginator
from django.http import Http404
from django.http import StreamingHttpResponse
from django.shortcuts import redirect
from django.shortcuts import render
from django.views.decorators import gzip

from main.decorators import lecturer_required
from main.models import StaffInfo, StudentClassDetails
from main.src.anti_spoof_predict import AntiSpoofPredict
from main.src.generate_patches import CropImage
from main.src.utility import parse_model_name
from main.view.reg import *
from main.models import BlogPost

model_test = AntiSpoofPredict(0)
image_cropper = CropImage()

model_dir = "main/resources/anti_spoof_models"
device_id = 0

for model_name in os.listdir(model_dir):
    h_input, w_input, model_type, scale = parse_model_name(model_name)


@lecturer_required
def lecturer_dashboard_view(request):
    blog_posts = BlogPost.objects.filter(type__in=["ALL", "GV"])
    return render(request, 'lecturer/lecturer_home.html', {'blog_posts': blog_posts})


@lecturer_required
def lecturer_schedule_view(request):
    id_lecturer = request.session.get('id_staff')
    week_start_param = request.GET.get('week_start')

    if week_start_param:
        try:
            week_start = date.fromisoformat(week_start_param)
        except ValueError:
            raise Http404("Invalid date format for week_start parameter")
    else:
        today = date.today()
        week_start = today - timedelta(days=today.weekday())

    end_of_week = week_start + timedelta(days=6)

    lecturer_classes = Classroom.objects.filter(
        id_lecturer__id_staff=id_lecturer,
        begin_date__lte=end_of_week,
        end_date__gte=week_start
    ).order_by('day_of_week_begin', 'begin_time')

    previous_week_start = week_start - timedelta(days=7)
    next_week_start = week_start + timedelta(days=7)

    previous_week_start = previous_week_start.strftime("%Y-%m-%d")
    next_week_start = next_week_start.strftime("%Y-%m-%d")

    context = {
        'lecturer_classes': lecturer_classes,
        'start_of_week': week_start,
        'end_of_week': end_of_week,
        'previous_week_start': previous_week_start,
        'next_week_start': next_week_start,
    }
    return render(request, 'lecturer/lecturer_schedule.html', context)


@lecturer_required
def lecturer_profile_view(request):
    id_lecturer = request.session['id_staff']
    lecturer = StaffInfo.objects.get(id_staff=id_lecturer)

    if request.method == 'POST':
        lecturer.staff_name = request.POST['lecturer_name']
        lecturer.email = request.POST['email']
        lecturer.phone = request.POST['phone']
        lecturer.address = request.POST['address']
        lecturer.birthday = datetime.strptime(request.POST['birthday'], '%d/%m/%Y').date()
        lecturer.save()
        messages.success(request, 'Thay đổi thông tin thành công.')

    context = {'lecturer': lecturer}

    return render(request, 'lecturer/lecturer_profile.html', context)


@lecturer_required
def lecturer_change_password_view(request):
    id_lecturer = request.session['id_staff']
    lecturer = StaffInfo.objects.get(id_staff=id_lecturer)

    if request.method == 'POST':
        old_password = request.POST['old_password']
        new_password = request.POST['new_password']
        confirm_password = request.POST['confirm_password']

        if check_password(old_password, lecturer.password):
            if new_password == confirm_password:
                lecturer.password = make_password(new_password)
                lecturer.save()
                update_session_auth_hash(request, lecturer)
                messages.success(request, 'Đổi mật khẩu thành công.')
            else:
                messages.error(request, 'Mật khẩu mới không khớp.')
        else:
            messages.error(request, 'Mật khẩu cũ không đúng.')

    return render(request, 'lecturer/lecturer_change_password.html')


@lecturer_required
def lecturer_attendance_class_view(request):
    id_lecturer = request.session.get('id_staff')

    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    end_of_week = week_start + timedelta(days=6)

    lecturer_classes = Classroom.objects.filter(
        id_lecturer__id_staff=id_lecturer,
        begin_date__lte=end_of_week,
        end_date__gte=week_start
    ).order_by('day_of_week_begin', 'begin_time')

    day_of_week_today = today.isoweekday()

    context = {
        'lecturer_classes': lecturer_classes,
        'start_of_week': week_start,
        'end_of_week': end_of_week,
        'day_of_week_today': day_of_week_today,
    }

    return render(request, 'lecturer/lecturer_attendance_class.html', context)


@lecturer_required
def lecturer_mark_attendance(request, classroom_id):
    classroom = Classroom.objects.get(pk=classroom_id)
    students_in_class = StudentClassDetails.objects.filter(id_classroom=classroom)
    day_of_week_today = date.today().isoweekday()

    if day_of_week_today != classroom.day_of_week_begin:
        return redirect('lecturer_attendance')

    attendance_list = Attendance.objects.filter(
        id_classroom=classroom,
        check_in_time__date=datetime.now()
    )

    if request.method == 'POST':
        for student in students_in_class:
            student_id = student.id_student
            attendance_status = request.POST.get(f'attendance_status_{student_id.id_student}')

            attendance, created = Attendance.objects.get_or_create(
                id_student=student_id,
                id_classroom=classroom,
                check_in_time__date=datetime.now(),
                defaults={
                    'attendance_status': attendance_status,
                    'check_in_time': datetime.now()
                }
            )

            if not created and attendance_status != str(attendance.attendance_status):
                attendance.attendance_status = attendance_status
                attendance.check_in_time = datetime.now()
                attendance.save()

        return redirect('lecturer_mark_attendance', classroom_id=classroom_id)

    context = {
        'students_in_class': students_in_class,
        'classroom': classroom,
        'attendance_list': attendance_list
    }

    return render(request, 'lecturer/lecturer_mask_attendance.html', context)


def generate_frames(model_dir, device_id):
    model_test = AntiSpoofPredict(device_id)
    image_cropper = CropImage()
    capture = cv2.VideoCapture(1)  # Change this to the desired camera index.

    while True:
        ret, frame = capture.read()
        if not ret:
            break

        image_bbox = model_test.get_bbox(frame)

        prediction = np.zeros((1, 3))
        test_speed = 0
        for model_name in os.listdir(model_dir):
            h_input, w_input, model_type, scale = parse_model_name(model_name)
            param = {
                "org_img": frame,
                "bbox": image_bbox,
                "scale": scale,
                "out_w": w_input,
                "out_h": h_input,
                "crop": True,
            }
            if scale is None:
                param["crop"] = False
            img = image_cropper.crop(**param)
            start = time.time()
            prediction += model_test.predict(img, os.path.join(model_dir, model_name))
            test_speed += time.time() - start

        label = np.argmax(prediction)
        value = prediction[0][label] / 2
        if label == 1:
            result_text = "RealFace Score: {:.2f}".format(value)
            color = (255, 0, 0)
        else:
            result_text = "FakeFace Score: {:.2f}".format(value)
            color = (0, 0, 255)

        cv2.rectangle(
            frame,
            (image_bbox[0], image_bbox[1] - 50),
            (image_bbox[0] + image_bbox[2], image_bbox[1] + image_bbox[3]),
            color, 2)

        cv2.putText(
            frame,
            result_text,
            (image_bbox[0], image_bbox[1]),
            cv2.FONT_HERSHEY_COMPLEX, 1.5 * frame.shape[0] / 1024, color)

        ret, buffer = cv2.imencode('.jpg', frame)
        if ret:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n\r\n')

    capture.release()
    cv2.destroyAllWindows()



@gzip.gzip_page
def live_video_feed2(request, classroom_id):
    print(classroom_id)
    return StreamingHttpResponse(main(classroom_id),
                                 content_type="multipart/x-mixed-replace; boundary=frame")


def lecturer_mark_attendance_by_face(request, classroom_id):
    classroom = Classroom.objects.get(pk=classroom_id)
    students_in_class = StudentClassDetails.objects.filter(id_classroom=classroom)
    day_of_week_today = date.today().isoweekday()

    if day_of_week_today != classroom.day_of_week_begin:
        return redirect('lecturer_attendance')

    attendance_list = Attendance.objects.filter(
        id_classroom=classroom,
        check_in_time__date=datetime.now()
    )

    context = {
        'students_in_class': students_in_class,
        'classroom': classroom,
        'attendance_list': attendance_list
    }

    return render(request, 'lecturer/lecturer_mask_attendance_by_face.html', context)


@lecturer_required
def lecturer_history_list_classroom_view(request):
    id_lecturer = request.session.get('id_staff')
    classroom_per_page = 5
    page_number = request.GET.get('page')

    classrooms = Classroom.objects.filter(
        id_lecturer__id_staff=id_lecturer
    ).order_by('day_of_week_begin', 'begin_time')

    paginator = Paginator(classrooms, classroom_per_page)
    page = paginator.get_page(page_number)

    context = {'classrooms': page}

    return render(request, 'lecturer/lecturer_history_list_classroom.html', context)


@lecturer_required
def lecturer_attendance_history_view(request, classroom_id):
    classroom = Classroom.objects.get(pk=classroom_id)
    students_attendance = Attendance.objects.filter(id_classroom=classroom).order_by('id_student')

    student_per_page = 5
    page_number = request.GET.get('page')
    pagniator = Paginator(students_attendance, student_per_page)
    page = pagniator.get_page(page_number)

    context = {
        'students_attendance': page,
        'classroom': classroom
    }

    return render(request, 'lecturer/lecturer_attendance_history.html', context)


@lecturer_required
def lecturer_list_classroom_view(request):
    id_lecturer = request.session.get('id_staff')
    classroom_per_page = 5
    page_number = request.GET.get('page')

    classrooms = Classroom.objects.filter(
        id_lecturer__id_staff=id_lecturer
    ).order_by('day_of_week_begin', 'begin_time')

    paginator = Paginator(classrooms, classroom_per_page)
    page = paginator.get_page(page_number)

    context = {'classrooms': page}

    return render(request, 'lecturer/lecturer_list_classroom.html', context)


@lecturer_required
def lecturer_calculate_attendance_points_view(request, classroom_id):
    classroom = Classroom.objects.get(pk=classroom_id)
    students_in_class = StudentClassDetails.objects.filter(id_classroom=classroom)
    student_per_page = 5
    page_number = request.GET.get('page')

    student_attendance_counts = []
    for student in students_in_class:
        absent_count = Attendance.objects.filter(id_classroom=classroom, id_student=student.id_student,
                                                 attendance_status=1).count()
        present_count = Attendance.objects.filter(id_classroom=classroom, id_student=student.id_student,
                                                  attendance_status=2).count()
        late_count = Attendance.objects.filter(id_classroom=classroom, id_student=student.id_student,
                                               attendance_status=3).count()

        total_number_attendance = absent_count + late_count + present_count
        total_attendance_present = late_count + present_count
        total_attendance_percentage = round((((absent_count * 0) + (late_count * 0.5) + present_count) / 9) * 3, 2)

        student_attendance_counts.append({
            'student': student,
            'absent_count': absent_count,
            'late_count': late_count,
            'present_count': present_count,
            'total_number_attendance': total_number_attendance,
            'total_attendance_present': total_attendance_present,
            'total_attendance_percentage': total_attendance_percentage
        })

        paginator = Paginator(student_attendance_counts, student_per_page)
        page = paginator.get_page(page_number)

    context = {
        'students_in_class': page,
        'classroom': classroom,
    }

    return render(request, 'lecturer/lecturer_calculate_attendance_points.html', context)
