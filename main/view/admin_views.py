from datetime import datetime

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.hashers import check_password, make_password
from django.core.paginator import Paginator
from django.shortcuts import render, redirect
from django.views.decorators import gzip
from main.decorators import admin_required
from main.models import StaffInfo, StudentInfo
from django.http import StreamingHttpResponse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import os
import cv2
import base64
from django.http import HttpResponse

from main.src.anti_spoof_predict import AntiSpoofPredict

color = (255, 0, 0)
thickness = 2
max_images = 300
device_id = 0
CAPTURE_STATUS = 0  # Đặt giá trị ban đầu cho biến toàn cục


@admin_required
def admin_dashboard_view(request):
    return render(request, 'admin/admin_home.html')


@admin_required
def student_capture(request):
    if request.method == 'POST':
        id_student = request.POST.get('id_student')
        student_name = request.POST.get('student_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        birthday = request.POST.get('birthday')
        PathImageFolder = request.POST.get('PathImageFolder')

        # Process the data and save it to the database

        # Return a response, e.g., a success message
        return JsonResponse({'message': 'Student added successfully'})

    # Handle other HTTP methods if necessary
    return JsonResponse({'error': 'Invalid request method'})


@admin_required
def admin_profile_view(request):
    id_admin = request.session['id_staff']
    admin = StaffInfo.objects.get(id_staff=id_admin)
    if request.method == 'POST':
        admin.staff_name = request.POST['admin_name']
        admin.email = request.POST['email']
        admin.phone = request.POST['phone']
        admin.address = request.POST['address']
        admin.birthday = datetime.strptime(request.POST['birthday'], '%d/%m/%Y').date()
        admin.save()
        messages.success(request, 'Thay đổi thông tin thành công.')

    context = {'admin': admin}

    return render(request, 'admin/admin_profile.html', context)


@admin_required
def admin_change_password_view(request):
    id_admin = request.session['id_staff']
    admin = StaffInfo.objects.get(id_staff=id_admin)

    if request.method == 'POST':
        old_password = request.POST['old_password']
        new_password = request.POST['new_password']
        confirm_password = request.POST['confirm_password']

        if check_password(old_password, admin.password):
            if new_password == confirm_password:
                admin.password = make_password(new_password)
                admin.save()
                update_session_auth_hash(request, admin)
                messages.success(request, 'Đổi mật khẩu thành công.')
            else:
                messages.error(request, 'Mật khẩu mới không khớp.')
        else:
            messages.error(request, 'Mật khẩu cũ không đúng.')

    return render(request, 'admin/admin_change_password.html')


@admin_required
def admin_student_management_view(request):
    students = StudentInfo.objects.all()
    per_page = 10
    paginator = Paginator(students, per_page)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    context = {
        'list_students': page,
    }
    return render(request, 'admin/admin_student_management.html', context)


@admin_required
def admin_student_add(request):
    if request.method == 'POST':
        id_student = request.POST['id_student']
        student_name = request.POST['student_name']
        email = request.POST['email']
        phone = request.POST['phone']
        address = request.POST['address']
        birthday = datetime.strptime(request.POST['birthday'], '%d/%m/%Y').date()
        PathImageFolder = request.POST['PathImageFolder']
        password = make_password(request.POST['id_student'])
        student = StudentInfo(id_student=id_student,
                              student_name=student_name,
                              email=email, phone=phone,
                              address=address,
                              birthday=birthday,
                              PathImageFolder=PathImageFolder,
                              password=password)
        student.save()
        messages.success(request, 'Thêm sinh viên thành công.')
        return redirect('admin_student_management')
    return render(request, 'admin/modal-popup/popup_add_student.html')


@admin_required
def admin_student_edit(request, id_student):
    student = StudentInfo.objects.get(id_student=id_student)
    context = {'student': student}
    if request.method == 'POST':
        student.student_name = request.POST['student_name']
        student.email = request.POST['email']
        student.phone = request.POST['phone']
        student.address = request.POST['address']
        student.birthday = datetime.strptime(request.POST['birthday'], '%d/%m/%Y').date()
        student.PathImageFolder = request.POST['PathImageFolder']
        student.save()
        messages.success(request, 'Thay đổi thông tin thành công.')
        return redirect('admin_student_management')
    return render(request, 'admin/modal-popup/popup_edit_student.html', context)


@admin_required
def admin_student_delete(request, id_student):
    StudentInfo.objects.filter(id_student=id_student).delete()
    return redirect('admin_student_management')


@admin_required
def capture(id, request):
    global CAPTURE_STATUS
    CAPTURE_STATUS = 0  # Sử dụng 'global' ở đầu hàm để thông báo rằng bạn muốn sử dụng biến toàn cục
    image_count = 0
    color = (0, 0, 255)  # BGR color for drawing rectangles
    thickness = 2  # Thickness of the rectangle
    model_test = AntiSpoofPredict(device_id)  # Define the AntiSpoofPredict object (assumed to be a valid class)
    capture = cv2.VideoCapture(2)  # Capture from camera at index 2 (can be adjusted)
    output_dir = f"./main/data/test_images/{id}"
    os.makedirs(output_dir, exist_ok=True)
    while image_count < 300:
        ret, frame = capture.read()
        if not ret:
            break

        image_bbox = model_test.get_bbox(frame)  # Assuming `get_bbox` returns the bounding box of the face
        if image_bbox is not None:
            x, y, w, h = (image_bbox[0]), (image_bbox[1] - 50), (image_bbox[0] + image_bbox[2]), (
                        image_bbox[1] + image_bbox[3])

            cropped_face = frame[y:h, x:w]
            if cropped_face is not None and cropped_face.size != 0:
                cropped_face = cv2.resize(cropped_face, (160, 160))

                image_filename = os.path.join(output_dir, f"{id}_{image_count}.jpg")

                cv2.imwrite(image_filename, cropped_face)

                cv2.rectangle(frame, (x, y), (w, h), color, thickness)
                image_count += 1

                cv2.putText(frame, f"Image Count: {image_count}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                            (255, 255, 255), 1)

        _, buffer = cv2.imencode('.jpg', frame)
        if _:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n\r\n')

        if image_count >= 300:
            CAPTURE_STATUS = 1

    capture.release()
    cv2.destroyAllWindows()


@admin_required
def live_video_feed(request, id_student):
    return StreamingHttpResponse(capture(id_student, request), content_type="multipart/x-mixed-replace;boundary=frame")


# Create a view to check the capture status
@admin_required
def check_capture_status(request):
    print(CAPTURE_STATUS)
    return JsonResponse({'capture_status': CAPTURE_STATUS})
