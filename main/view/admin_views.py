import math
import os
import pickle
from datetime import datetime
import openpyxl

import cv2
import numpy as np
import tensorflow as tf
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.hashers import check_password, make_password
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.db import transaction
from django.http import JsonResponse
from django.http import StreamingHttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from sklearn.svm import SVC
from django.urls import reverse
from django.views.generic.edit import CreateView
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import ListView

from main.forms import BlogForm, EditBlogForm
from main.models import BlogPost

from main import facenet
from main.decorators import admin_required
from main.models import StaffInfo, StudentInfo, StaffRole, Role, Classroom, StudentClassDetails
from main.src.anti_spoof_predict import AntiSpoofPredict
from main.models import BlogPost
from django.views import View
from django.shortcuts import render, redirect

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
class AddBlog(SuccessMessageMixin, CreateView, ListView):
    form_class = BlogForm
    model = BlogPost
    template_name = "admin/admin_notification_management.html"
    context_object_name = 'blog_posts'

    def get_success_url(self):
        return reverse('admin_notification_view')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['blog_posts'] = BlogPost.objects.all()
        context['edit_form'] = EditBlogForm()
        return context


class BlogPostDeleteView(View):
    def get(self, request, pk, *args, **kwargs):
        blog_post = get_object_or_404(BlogPost, id=pk)
        blog_post.delete()
        return redirect('admin_notification_view')


class EditBlogView(View):
    template_name = 'admin/admin_edit_notification.html'

    def get(self, request, blog_post_id):
        blog_post_instance = get_object_or_404(BlogPost, id=blog_post_id)
        edit_form = EditBlogForm(instance=blog_post_instance)
        return render(request, self.template_name, {'edit_form': edit_form})

    def post(self, request, blog_post_id):
        blog_post_instance = get_object_or_404(BlogPost, id=blog_post_id)
        edit_form = EditBlogForm(request.POST, instance=blog_post_instance)
        if edit_form.is_valid():
            edit_form.save()
            # Redirect to a success page or another URL
            return redirect('admin_notification_view')  # Replace with your actual success URL name
        else:
            # Form is not valid, handle accordingly
            return render(request, self.template_name, {'edit_form': edit_form})


@admin_required
def admin_dashboard_view(request):
    blog_posts = BlogPost.objects.all()

    return render(request, 'admin/admin_home.html', {'blog_posts': blog_posts})


@admin_required
def admin_notification_view(request):
    blog_posts = BlogPost.objects.all()
    return render(request, 'admin/admin_notification_management.html', {'blog_posts': blog_posts})


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
        student.student_name = request.POST['student_name_edit']
        student.email = request.POST['email_edit']
        student.phone = request.POST['phone_edit']
        student.address = request.POST['address_edit']
        student.birthday = datetime.strptime(request.POST['birthday_edit'], '%d/%m/%Y').date()
        student.PathImageFolder = request.POST['PathImageFolder_edit']
        print(request.POST['student_name_edit'])
        student.save()
        messages.success(request, 'Thay đổi thông tin thành công.')
        return redirect('admin_student_management')
    return render(request, 'admin/modal-popup/popup_edit_student.html', context)


@admin_required
def admin_student_capture(request, id_student):
    student = StudentInfo.objects.get(id_student=id_student)
    context = {'student': student}
    if request.method == 'POST':
        student.student_name = request.POST['student_name_capture']
        student.email = request.POST['email_capture']
        student.phone = request.POST['phone_capture']
        student.address = request.POST['address_capture']
        student.birthday = datetime.strptime(request.POST['birthday_capture'], '%d/%m/%Y').date()
        student.PathImageFolder = request.POST['PathImageFolder_capture']
        student.save()
        messages.success(request, 'Thay đổi thông tin thành công.')
        return redirect('admin_student_management')
    return render(request, 'admin/modal-popup/popup_capture_student.html', context)


@admin_required
def admin_student_delete(request, id_student):
    StudentInfo.objects.filter(id_student=id_student).delete()

    # Directory to check for existence and delete
    folder_path = f"./main/Dataset/FaceData/processed/{id_student}"

    # Check if the directory exists
    if os.path.exists(folder_path) and os.path.isdir(folder_path):
        # Remove the directory and its contents recursively
        import shutil
        shutil.rmtree(folder_path)
        print(f"Folder '{folder_path}' and its contents deleted.")
    else:
        print(f"Folder '{folder_path}' does not exist.")

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
        id_lecturer = request.POST['id_lecturer']
        staff_name = request.POST['lecturer_name']
        email = request.POST['email']
        phone = request.POST['phone']
        address = request.POST['address']
        birthday = datetime.strptime(request.POST['birthday'], '%d/%m/%Y').date()
        password = make_password(request.POST['id_lecturer'])
        lecturer = StaffInfo(id_staff=id_lecturer,
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
def admin_lecturer_delete(request, id_staff):
    StaffInfo.objects.filter(id_staff=id_staff).delete()
    return redirect('admin_lecturer_management')


@admin_required
def admin_lecturer_edit(request, id_staff):
    lecturer = StaffInfo.objects.get(id_staff=id_staff)
    context = {'staff': lecturer}
    if request.method == 'POST':
        lecturer.staff_name = request.POST['lecturer_name']
        lecturer.email = request.POST['email']
        lecturer.phone = request.POST['phone']
        lecturer.address = request.POST['address']
        lecturer.birthday = datetime.strptime(request.POST['birthday'], '%d/%m/%Y').date()
        lecturer.save()
        messages.success(request, 'Thay đổi thông tin thành công.')
        return redirect('admin_lecturer_management')
    return render(request, 'admin/modal-popup/popup_edit_lecturer.html', context)


@admin_required
def admin_lecturer_get_info(request, id_staff):
    try:
        lecturer = StaffInfo.objects.get(id_staff=id_staff)
        staff_data = {
            'id_staff': lecturer.id_staff,
            'staff_name': lecturer.staff_name,
            'email': lecturer.email,
            'phone': lecturer.phone,
            'address': lecturer.address,
            'birthday': lecturer.birthday.strftime('%d/%m/%Y'),
        }
        return JsonResponse({'lecturer': staff_data})
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
        name = request.POST['name']
        begin_date = datetime.strptime(request.POST['begin_date'], '%d/%m/%Y').date()
        end_date = datetime.strptime(request.POST['end_date'], '%d/%m/%Y').date()
        day_of_week_begin = request.POST['day_of_week_begin']
        begin_time = request.POST['begin_time']
        end_time = request.POST['end_time']
        id_lecturer = request.POST['id_lecturer']
        schedule = Classroom(name=name,
                             begin_date=begin_date, end_date=end_date,
                             day_of_week_begin=day_of_week_begin,
                             begin_time=begin_time,
                             end_time=end_time,
                             id_lecturer_id=id_lecturer)
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
        schedule.begin_date = datetime.strptime(request.POST['begin_date'], '%d/%m/%Y').date()
        schedule.end_date = datetime.strptime(request.POST['end_date'], '%d/%m/%Y').date()
        schedule.day_of_week_begin = request.POST['day_of_week_begin']
        schedule.begin_time = request.POST['begin_time']
        schedule.end_time = request.POST['end_time']
        schedule.id_lecturer_id = request.POST['lecturer_name']
        schedule.save()
        messages.success(request, 'Thay đổi thông tin thành công.')
        return redirect('admin_schedule_management')
    return render(request, 'admin/modal-popup/popup_edit_schedule.html', context)


@admin_required
def admin_schedule_delete(request, id_classroom):
    Classroom.objects.filter(id_classroom=id_classroom).delete()
    return redirect('admin_schedule_management')


@admin_required
def admin_schedule_get_info(request, id_classroom):
    try:
        schedule = Classroom.objects.get(id_classroom=id_classroom)
        if schedule.id_lecturer is None:
            lecturer_name = 'Hiện chưa có giảng viên phụ trách (Vui lòng thêm giảng viên)'
        else:
            lecturer_name = schedule.id_lecturer.staff_name
        schedule_data = {
            'id_classroom': schedule.id_classroom,
            'name': schedule.name,
            'begin_date': schedule.begin_date.strftime('%d/%m/%Y'),
            'end_date': schedule.end_date.strftime('%d/%m/%Y'),
            'day_of_week_begin': schedule.day_of_week_begin,
            'begin_time': schedule.begin_time,
            'end_time': schedule.end_time,
            'lecturer_name': lecturer_name,
        }
        return JsonResponse({'schedule': schedule_data})
    except Classroom.DoesNotExist:
        return JsonResponse({'error': 'Không tìm thấy lớp học'}, status=404)


@admin_required
def admin_list_classroom_student_view(request):
    classroom_per_page = 10
    page_number = request.GET.get('page')
    search_query = request.GET.get('q', '')
    list_classrooms = Classroom.objects.filter(
        Q(id_classroom__icontains=search_query) | Q(name__icontains=search_query)
    ).annotate(student_count=Count('studentclassdetails__id_student'))
    paginator = Paginator(list_classrooms, classroom_per_page)
    page = paginator.get_page(page_number)
    context = {'list_classrooms': page, 'search_query': search_query}
    return render(request, 'admin/admin_list_classroom_student_management.html', context)


@admin_required
def admin_list_student_in_classroom_view(request, classroom_id):
    classroom = Classroom.objects.get(pk=classroom_id)
    students_in_class = StudentClassDetails.objects.filter(id_classroom=classroom)
    student_per_page = 10
    page_number = request.GET.get('page')
    paginator = Paginator(students_in_class, student_per_page)
    page = paginator.get_page(page_number)
    context = {'students_in_class': page, 'classroom_id': classroom_id, }
    return render(request, 'admin/admin_list_student_classroom_management.html', context)


@admin_required
def admin_list_student_in_class_add_list(request, classroom_id):
    if request.method == 'POST':
        file_path = request.FILES['file_path']
        try:
            classroom = Classroom.objects.get(id_classroom=classroom_id)
        except Classroom.DoesNotExist:
            return render(request, 'error/error_template.html', {'error_message': 'Lớp học không tồn tại.'})

        workbook = openpyxl.load_workbook(file_path)
        sheet = workbook.active
        list_id_student = [row[0].value for row in sheet.iter_rows(min_row=2, max_col=1)]

        with transaction.atomic():
            for id_student in list_id_student:
                try:
                    student = StudentInfo.objects.get(id_student=id_student)
                except StudentInfo.DoesNotExist:
                    student = StudentInfo(id_student=id_student)
                    student.save()

                if not StudentClassDetails.objects.filter(id_classroom=classroom, id_student=student).exists():
                    student_class_detail = StudentClassDetails(id_classroom=classroom, id_student=student)
                    student_class_detail.save()
        return redirect('admin_list_student_in_classroom', classroom_id)
    return render(request, 'admin/admin_list_student_classroom_management.html')


@admin_required
def admin_list_student_in_class_add(request, classroom_id):
    if request.method == 'POST':
        id_student = request.POST.get('id_student')
        if StudentClassDetails.objects.filter(id_classroom_id=classroom_id, id_student_id=id_student).exists():
            messages.warning(request, 'Sinh viên đã tồn tại trong lớp học.')
        else:
            student_in_class = StudentClassDetails(id_classroom_id=classroom_id,
                                                   id_student_id=id_student)
            student_in_class.save()
            messages.success(request, 'Thêm sinh viên vào lớp học thành công.')
        return redirect('admin_list_student_in_classroom', classroom_id)
    return render(request, 'admin/modal-popup/popup_add_student_in_class.html')


@admin_required
def admin_list_student_in_class_delete(request, id_student, id_classroom):
    StudentClassDetails.objects.filter(id_student_id=id_student, id_classroom_id=id_classroom).delete()
    return redirect('admin_list_student_in_classroom', id_classroom)


@admin_required
def admin_list_student_in_class_delete_all(request, id_classroom):
    StudentClassDetails.objects.filter(id_classroom_id=id_classroom).delete()
    return redirect('admin_list_student_in_classroom', id_classroom)


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
