from datetime import date, timedelta, datetime

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.hashers import check_password, make_password
from django.http import Http404
from django.shortcuts import redirect, render
from django.http import StreamingHttpResponse
from django.views.decorators import gzip

from main.decorators import lecturer_required
from main.models import StaffInfo, Classroom, StudentClassDetails, Attendance
from django.http import StreamingHttpResponse
from django.shortcuts import render

import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from PIL import Image
import io

import base64


import os
import cv2
import numpy as np

import time

from main.src.anti_spoof_predict import AntiSpoofPredict
from main.src.generate_patches import CropImage
from main.src.utility import parse_model_name

model_test = AntiSpoofPredict(0)
image_cropper = CropImage()

model_dir = "main/resources/anti_spoof_models"
device_id = 0

model_dir = "main/resources/anti_spoof_models"
device_id = 0

for model_name in os.listdir(model_dir):
    h_input, w_input, model_type, scale = parse_model_name(model_name)

def get_new_box(src_w, src_h, bbox, scale):
    x, y, box_w, box_h = bbox

    scale = min((src_h - 1) / box_h, min((src_w - 1) / box_w, scale))

    new_width = box_w * scale
    new_height = box_h * scale
    center_x, center_y = box_w / 2 + x, box_h / 2 + y

    left_top_x = center_x - new_width / 2
    left_top_y = center_y - new_height / 2
    right_bottom_x = center_x + new_width / 2
    right_bottom_y = center_y + new_height / 2

    if left_top_x < 0:
        right_bottom_x -= left_top_x
        left_top_x = 0

    if left_top_y < 0:
        right_bottom_y -= left_top_y
        left_top_y = 0

    if right_bottom_x > src_w - 1:
        left_top_x -= right_bottom_x - src_w + 1
        right_bottom_x = src_w - 1

    if right_bottom_y > src_h - 1:
        left_top_y -= right_bottom_y - src_h + 1
        right_bottom_y = src_h - 1

    return int(left_top_x), int(left_top_y), int(right_bottom_x), int(right_bottom_y)
def crop(org_img, bbox, scale, out_w, out_h, crop=True):
    if not crop:
        dst_img = cv2.resize(org_img, (out_w, out_h))
    else:
        src_h, src_w, _ = np.shape(org_img)
        left_top_x, left_top_y, right_bottom_x, right_bottom_y = get_new_box(src_w, src_h, bbox, scale)

        img = org_img[left_top_y: right_bottom_y + 1, left_top_x: right_bottom_x + 1]
        dst_img = cv2.resize(img, (out_w, out_h))
    return dst_img


@lecturer_required
def lecturer_dashboard_view(request):
    return render(request, 'lecturer/lecturer_home.html')


@lecturer_required
def lecturer_schedule_view(request):
    id_staff = request.session.get('id_staff')
    week_start_param = request.GET.get('week_start')

    if id_staff is not None:
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
            id_lecturer__id_staff=id_staff,
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
    else:
        request.session['next_url'] = request.path
        return redirect('login')


@lecturer_required
def lecturer_profile_view(request):
    if 'id_staff' in request.session:
        id_staff = request.session['id_staff']
        try:
            lecturer = StaffInfo.objects.get(id_staff=id_staff)

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
        except StaffInfo.DoesNotExist:
            return redirect('login')
    else:
        request.session['next_url'] = request.path
        return redirect('login')


@lecturer_required
def lecturer_change_password_view(request):
    if 'id_staff' in request.session:
        id_staff = request.session['id_staff']

        try:
            lecturer = StaffInfo.objects.get(id_staff=id_staff)

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

        except StaffInfo.DoesNotExist:
            return redirect('login')
    else:
        request.session['next_url'] = request.path
        return redirect('login')


@lecturer_required
def lecturer_attendance_class_view(request):
    id_staff = request.session.get('id_staff')

    if id_staff is not None:
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        end_of_week = week_start + timedelta(days=6)

        lecturer_classes = Classroom.objects.filter(
            id_lecturer__id_staff=id_staff,
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
    else:
        request.session['next_url'] = request.path
        return redirect('login')


def lecturer_mark_attendance(request, classroom_id):
    classroom = Classroom.objects.get(pk=classroom_id)
    students_in_class = StudentClassDetails.objects.filter(id_classroom=classroom)
    attendance_list = Attendance.objects.filter(id_classroom=classroom)
    day_of_week_today = date.today().isoweekday()
    if day_of_week_today != classroom.day_of_week_begin:
        return redirect('lecturer_attendance')
    elif request.method == 'POST':
        for student in students_in_class:
            student_id = student.id_student
            attendance_status = request.POST.get(f'attendance_status_{student_id.id_student}')

            attendance = Attendance.objects.filter(
                id_student=student_id,
                id_classroom=classroom,
                check_in_time__date=datetime.now().date()
            ).first()

            if attendance:
                if attendance_status != str(attendance.attendance_status):
                    attendance.attendance_status = attendance_status
                    attendance.check_in_time = datetime.now()
                    attendance.save()
            else:
                attendance = Attendance.objects.create(
                    id_student=student_id,
                    id_classroom=classroom,
                    check_in_time=datetime.now(),
                    attendance_status=attendance_status
                )

        return redirect('lecturer_mark_attendance', classroom_id=classroom_id)

    context = {'students_in_class': students_in_class,
               'classroom': classroom,
               'attendance_list': attendance_list}
    return render(request, 'lecturer/lecturer_mask_attendance.html', context)




@csrf_exempt
def process_video_frame(request):
    if request.method == 'POST':
        try:
            # Receive the JSON data containing the image_data
            data = json.loads(request.body)
            image_data_url = data.get('image_data', '')
            # Decode the data URL and convert it back to an image
            image_data = base64.b64decode(image_data_url.split(',')[1])
            image = Image.open(io.BytesIO(image_data))
            # Convert the PIL image to a NumPy array (OpenCV format)
            np_array = np.array(image)

            # Convert numpy array to OpenCV image
            frame = cv2.cvtColor(np_array, cv2.COLOR_RGB2BGR)
            image_bbox = model_test.get_bbox(frame)
            height, width, _ = frame.shape  # Giả sử frame là hình ảnh
            prediction = np.zeros((1, 3))
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
            prediction += model_test.predict(img, os.path.join(model_dir, model_name))
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
                (image_bbox[0] + image_bbox[2], image_bbox[1] + image_bbox[3]),  # Increase the height by 20 pixels
                color, 2)

            cv2.putText(
                frame,
                result_text,
                (image_bbox[0], image_bbox[1]),
                cv2.FONT_HERSHEY_COMPLEX, 0.5 * frame.shape[0] / 1024, color)
            _, processed_image_data = cv2.imencode('.jpg', frame)
            processed_image_data_url = "data:image/jpeg;base64," + base64.b64encode(processed_image_data).decode()

            # Return the processed image data URL to the frontend
            return JsonResponse({'processed_image_data': processed_image_data_url})

        except Exception as e:
            return JsonResponse({'error': str(e)})

    return JsonResponse({'error': 'Invalid request method.'})




def lecturer_mark_attendance_by_face(request):
    return render(request, 'lecturer/lecturer_mask_attendance_by_face.html')

def lecturer_attendance_history_view(request):
    return render(request, 'lecturer/lecturer_attendance_history.html')
