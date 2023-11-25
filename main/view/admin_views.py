import math
import os
import pickle
from datetime import datetime

import cv2
import numpy as np
import tensorflow as tf
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.hashers import check_password, make_password
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.http import StreamingHttpResponse
from django.shortcuts import render, redirect
from sklearn.svm import SVC

from main import facenet
from main.decorators import admin_required
from main.models import StaffInfo, StudentInfo, StaffRole, Role, Classroom
from main.src.anti_spoof_predict import AntiSpoofPredict

color = (255, 0, 0)
thickness = 2
max_images = 300
device_id = 0
CAPTURE_STATUS = 0  # Đặt giá trị ban đầu cho biến toàn cục

TRAIN_STATUS = 0
mode = 'TRAIN'  # Change to 'TRAIN' to train the classifier
data_dir = 'main/Dataset/FaceData/processed'
model = 'main/Models/20180402-114759.pb'
classifier_filename = 'main/Models/facemodel.pkl'
use_split_dataset = False

batch_size = 90
image_size = 160
seed = 666
min_nrof_images_per_class = 20
nrof_train_images_per_class = 10


# The rest of the code remains the same
# Define the function to split the dataset

@admin_required
def admin_dashboard_view(request):
    return render(request, 'admin/admin_home.html')


@admin_required
def dashboard_add_news_view(request):
    return render(request, 'admin/admin_add_news.html')


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
    student_per_page = 10
    paginator = Paginator(students, student_per_page)
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
def admin_student_delete(id_student):
    StudentInfo.objects.filter(id_student=id_student).delete()
    return redirect('admin_student_management')


@admin_required
def admin_student_get_info(request, id_student):
    try:
        student = StudentInfo.objects.get(id_student=id_student)
        student_data = {
            'id_student': student.id_student,
            'student_name': student.student_name,
            'email': student.email,
            'phone': student.phone,
            'address': student.address,
            'birthday': student.birthday.strftime('%d/%m/%Y'),
            'PathImageFolder': student.PathImageFolder,
        }
        return JsonResponse({'student': student_data})
    except StudentInfo.DoesNotExist:
        return JsonResponse({'error': 'Không tìm thấy học sinh'}, status=404)


@admin_required
def admin_lecturer_management_view(request):
    lecturer = StaffInfo.objects.filter(roles__name='Lecturer')
    per_page = 10
    paginator = Paginator(lecturer, per_page)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    context = {
        'list_lecturers': page,
    }
    return render(request, 'admin/admin_lecturer_management.html', context)


@admin_required
def admin_lecturer_add(request):
    if request.method == 'POST':
        id_staff = request.POST['id_staff']
        staff_name = request.POST['staff_name']
        email = request.POST['email']
        phone = request.POST['phone']
        address = request.POST['address']
        birthday = datetime.strptime(request.POST['birthday'], '%d/%m/%Y').date()
        password = make_password(request.POST['id_staff'])
        lecturer = StaffInfo(id_staff=id_staff,
                             staff_name=staff_name,
                             email=email, phone=phone,
                             address=address,
                             birthday=birthday,
                             password=password
                             )
        lecturer.save()
        lecturer_role, created = Role.objects.get_or_create(name='Lecturer')
        lecturer_role = StaffRole(staff=lecturer, role=lecturer_role)
        messages.success(request, 'Thêm sinh viên thành công.')
        lecturer_role.save()
        return redirect('admin_lecturer_management')
    return render(request, 'admin/admin_add_lecturer.html')


@admin_required
def admin_lecturer_delete(id_staff):
    StaffInfo.objects.filter(id_staff=id_staff).delete()
    return redirect('admin_lecturer_management')
    # return render(request, 'admin/admin_edit_student.html')


@admin_required
def admin_lecturer_edit(request, id_staff):
    Staff = StaffInfo.objects.get(id_staff=id_staff)
    context = {'staff': Staff}
    if request.method == 'POST':
        Staff.staff_name = request.POST['staff_name']
        Staff.email = request.POST['email']
        Staff.phone = request.POST['phone']
        Staff.address = request.POST['address']
        Staff.birthday = datetime.strptime(request.POST['birthday'], '%d/%m/%Y').date()
        Staff.save()
        messages.success(request, 'Thay đổi thông tin thành công.')
        return redirect('admin_lecturer_management')
    return render(request, 'admin/admin_edit_lecturer.html', context)


@admin_required
def admin_lecturer_get_info(request, id_staff):
    try:
        staff = StaffInfo.objects.get(id_staff=id_staff)
        staff_data = {
            'id_staff': staff.id_staff,
            'staff_name': staff.staff_name,
            'email': staff.email,
            'phone': staff.phone,
            'address': staff.address,
            'birthday': staff.birthday.strftime('%d/%m/%Y'),
        }
        return JsonResponse({'staff': staff_data})
    except StaffInfo.DoesNotExist:
        return JsonResponse({'error': 'Không tìm thấy giảng viên'}, status=404)


@admin_required
def admin_schedule_management_view(request):
    schedule = Classroom.objects.all()
    schedule_per_page = 10
    paginator = Paginator(schedule, schedule_per_page)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    context = {
        'list_schedules': page,
    }

    return render(request, 'admin/admin_schedule_management.html', context)


@admin_required
def admin_schedule_add(request):
    if request.method == 'POST':
        id_classroom = request.POST['id_classroom']
        name = request.POST['name']
        begin_date = request.POST['begin_date']
        end_date = request.POST['end_date']
        day_of_week_begin = request.POST['day_of_week_begin']
        begin_time = request.POST['begin_time']
        end_time = request.POST['end_time']
        id_lecturer= request.POST['id_lecturer']
        schedule = Classroom(id_classroom=id_classroom,
                             name=name,
                             begin_date=begin_date, end_date=end_date,
                             day_of_week_begin=day_of_week_begin,
                             begin_time=begin_time,
                             end_time=end_time,
                             id_lecturer= id_lecturer)
        schedule.save()
        messages.success(request, 'Thêm Thời Khóa Biểu thành công.')
        return redirect('admin_schedule_management')
    return render(request, 'admin/modal-popup/popup_add_schedule.html')


@admin_required
def admin_schedule_edit(request, id_classroom):
    schedule = Classroom.objects.get(id_classroom=id_classroom)
    context = {'schedule': schedule}
    if request.method == 'POST':
        schedule.name = request.POST['name']
        schedule.begin_date = request.POST['begin_date']
        schedule.end_date = request.POST['end_date']
        schedule.day_of_week_begin = request.POST['day_of_week_begin']
        schedule.begin_time = request.POST['begin_time']
        schedule.end_time = request.POST['end_time']
        schedule.id_lecturer = request.POST['id_lecturer']
        schedule.save()
        messages.success(request, 'Thay đổi thông tin thành công.')
        return redirect('admin_schedule_management')
    # return render(request, 'admin/modal-popup/popup_edit_schedule.html', context)
    return render(request, 'admin/admin_edit_schedule.html', context)


@admin_required
def admin_schedule_delete(request, id_classroom):
    Classroom.objects.filter(id_classroom=id_classroom).delete()
    return redirect('admin_schedule_management')


@admin_required
def admin_schedule_get_info(request, id_classroom):
    try:
        schedule = Classroom.objects.get(id_classroom=id_classroom)
        schedule_data = {
            'id_classroom': schedule.id_classroom,
            'name': schedule.name,
            'begin_date': schedule.begin_date,
            'end_date': schedule.end_date,
            'day_of_week_begin': schedule.day_of_week_begin,
            'begin_time': schedule.begin_date,
            'end_time': schedule.end_date,
        }
        return JsonResponse({'schedule': schedule_data})
    except Classroom.DoesNotExist:
        return JsonResponse({'error': 'Không tìm thấy lớp học'}, status=404)


def capture(id, request):
    global CAPTURE_STATUS
    CAPTURE_STATUS = 0  # Sử dụng 'global' ở đầu hàm để thông báo rằng bạn muốn sử dụng biến toàn cục
    image_count = 0
    color = (0, 0, 255)  # BGR color for drawing rectangles
    thickness = 2  # Thickness of the rectangle
    model_test = AntiSpoofPredict(device_id)  # Define the AntiSpoofPredict object (assumed to be a valid class)
    capture = cv2.VideoCapture(0)  # Capture from camera at index 2 (can be adjusted)
    output_dir = f"./main/Dataset/FaceData/processed/{id}"
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


def split_dataset(dataset, min_nrof_images_per_class, nrof_train_images_per_class):
    train_set = []
    test_set = []
    for cls in dataset:
        paths = cls.image_paths
        # Remove classes with less than min_nrof_images_per_class
        if len(paths) >= min_nrof_images_per_class:
            np.random.shuffle(paths)
            train_set.append(facenet.ImageClass(cls.name, paths[:nrof_train_images_per_class]))
            test_set.append(facenet.ImageClass(cls.name, paths[nrof_train_images_per_class:]))
    return train_set, test_set


# The main function
def main():
    global TRAIN_STATUS
    TRAIN_STATUS = 0
    model = 'main/Models/20180402-114759.pb'
    with tf.Graph().as_default():
        with tf.compat.v1.Session() as sess:
            np.random.seed(seed)
            if use_split_dataset:
                dataset_tmp = facenet.get_dataset(data_dir)
                train_set, test_set = split_dataset(dataset_tmp, min_nrof_images_per_class, nrof_train_images_per_class)
                if mode == 'TRAIN':
                    dataset = train_set
                elif mode == 'CLASSIFY':
                    dataset = test_set
            else:
                dataset = facenet.get_dataset(data_dir)

            # Check that there are at least one training image per class
            for cls in dataset:
                assert len(cls.image_paths) > 0, 'There must be at least one image for each class in the dataset'

            paths, labels = facenet.get_image_paths_and_labels(dataset)

            print('Number of classes: %d' % len(dataset))
            print('Number of images: %d' % len(paths))

            # Load the model
            print('Loading feature extraction model')
            facenet.load_model(model)

            # Get input and output tensors
            images_placeholder = tf.compat.v1.get_default_graph().get_tensor_by_name("input:0")
            embeddings = tf.compat.v1.get_default_graph().get_tensor_by_name("embeddings:0")
            phase_train_placeholder = tf.compat.v1.get_default_graph().get_tensor_by_name("phase_train:0")
            embedding_size = embeddings.get_shape()[1]

            # Run forward pass to calculate embeddings
            print('Calculating features for images')
            nrof_images = len(paths)
            nrof_batches_per_epoch = int(math.ceil(1.0 * nrof_images / batch_size))
            emb_array = np.zeros((nrof_images, embedding_size))
            for i in range(nrof_batches_per_epoch):
                start_index = i * batch_size
                end_index = min((i + 1) * batch_size, nrof_images)
                paths_batch = paths[start_index:end_index]
                images = facenet.load_data(paths_batch, False, False, image_size)
                feed_dict = {images_placeholder: images, phase_train_placeholder: False}
                emb_array[start_index:end_index, :] = sess.run(embeddings, feed_dict=feed_dict)

            classifier_filename_exp = os.path.expanduser(classifier_filename)

            if mode == 'TRAIN':
                # Train classifier
                print('Training classifier')
                model = SVC(kernel='linear', probability=True)
                model.fit(emb_array, labels)
                # Create a list of class names
                class_names = [cls.name.replace('_', ' ') for cls in dataset]

                # Saving classifier model
                with open(classifier_filename_exp, 'wb') as outfile:
                    pickle.dump((model, class_names), outfile)
                print('Saved classifier model to file "%s"' % classifier_filename_exp)
            TRAIN_STATUS = 1
            output_string = 'Number of classes: %d\nNumber of images: %d\nLoading feature extraction model' % (
                len(dataset), len(paths))
    return TRAIN_STATUS, output_string


@admin_required
def train(request):
    train_result, resuil = main()
    print(train_result, resuil)
    return JsonResponse({'train': train_result, 'resuil': resuil})


@admin_required
def live_video_feed(request, id_student):
    return StreamingHttpResponse(capture(id_student, request), content_type="multipart/x-mixed-replace;boundary=frame")


# Create a view to check the capture status
@admin_required
def check_capture_status(request):
    print(CAPTURE_STATUS)
    return JsonResponse({'capture_status': CAPTURE_STATUS})
