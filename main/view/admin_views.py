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
import tensorflow as tf
import numpy as np
import facenet
import os
import math
import pickle
from sklearn.svm import SVC
from main import facenet
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

def capture(id, request):
    global CAPTURE_STATUS
    CAPTURE_STATUS = 0 # Sử dụng 'global' ở đầu hàm để thông báo rằng bạn muốn sử dụng biến toàn cục
    image_count = 0
    color = (0, 0, 255)  # BGR color for drawing rectangles
    thickness = 2  # Thickness of the rectangle
    model_test = AntiSpoofPredict(device_id)  # Define the AntiSpoofPredict object (assumed to be a valid class)
    capture = cv2.VideoCapture(2)  # Capture from camera at index 2 (can be adjusted)
    output_dir = f"./main/Dataset/FaceData/processed/{id}"
    os.makedirs(output_dir, exist_ok=True)
    while image_count < 300:
        ret, frame = capture.read()
        if not ret:
            break
        image_bbox = model_test.get_bbox(frame)  # Assuming `get_bbox` returns the bounding box of the face
        if image_bbox is not None:
            x, y, w, h = (image_bbox[0]), (image_bbox[1] - 50), (image_bbox[0] + image_bbox[2]), (image_bbox[1] + image_bbox[3])

            cropped_face = frame[y:h, x:w]
            if cropped_face is not None and cropped_face.size != 0:
                cropped_face = cv2.resize(cropped_face, (160, 160))
                image_filename = os.path.join(output_dir, f"{id}_{image_count}.jpg")
                cv2.imwrite(image_filename, cropped_face)
                cv2.rectangle(frame, (x, y), (w, h), color, thickness)
                image_count += 1
                cv2.putText(frame, f"Image Count: {image_count}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
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
            output_string = 'Number of classes: %d\nNumber of images: %d\nLoading feature extraction model' % (len(dataset), len(paths))
    return TRAIN_STATUS,output_string


@admin_required
def train(request):
    train_result, resuil = main()
    print(train_result, resuil)
    return JsonResponse({'train': train_result, 'resuil': resuil})

@admin_required
def live_video_feed(request, id_student):
    return StreamingHttpResponse(capture(id_student,request),content_type="multipart/x-mixed-replace;boundary=frame")

# Create a view to check the capture status
@admin_required
def check_capture_status(request):
    print(CAPTURE_STATUS)
    return JsonResponse({'capture_status': CAPTURE_STATUS })