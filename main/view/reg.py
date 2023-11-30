import pickle
from datetime import datetime
import os
import cv2
import imutils
import numpy as np
import tensorflow as tf
from imutils.video import VideoStream
from main.src.anti_spoof_predict import AntiSpoofPredict
from main.src.generate_patches import CropImage
from main.src.utility import parse_model_name
from main import facenet
from main.align import detect_face
from main.models import Classroom, Attendance, StudentInfo, StudentClassDetails
import warnings

# ...

# Trước khi gọi hàm có cảnh báo
with warnings.catch_warnings():
    warnings.simplefilter("ignore")

model_test = AntiSpoofPredict(0)
image_cropper = CropImage()
model_dir = "main/resources/anti_spoof_models"


# Function to draw a progress bar


def insert_attendance(id_classroom, student_id):
    classroom = Classroom.objects.get(pk=id_classroom)
    current_time = datetime.now()
    begin_time = classroom.begin_time

    time_difference = (datetime.combine(datetime.now(), current_time.time())
                       - datetime.combine(datetime.now(), begin_time))

    if time_difference.total_seconds() > 900:
        attendance_status = 3
    else:
        attendance_status = 2

    students_in_class = StudentInfo.objects.filter(classroom=classroom)

    for student in students_in_class:
        attendance, created = Attendance.objects.get_or_create(
            id_student=student,
            id_classroom=classroom,
            check_in_time__date=datetime.now(),
            defaults={
                'check_in_time': datetime.now(),
                'attendance_status': 1,
            })

    student_info = StudentInfo.objects.get(id_student=student_id)

    try:
        attendance, created = Attendance.objects.get_or_create(
            id_student=student_info,
            id_classroom=classroom,
            check_in_time__date=datetime.now(),
            defaults={
                'check_in_time': datetime.now(),
                'attendance_status': attendance_status,
            }
        )

        if not created:
            attendance.check_in_time = datetime.now()
            attendance.attendance_status = attendance_status  # Thay thế bằng giá trị mong muốn
            attendance.save()
        print("Trạng thái điểm danh", attendance_status, " Mã sv : ", student_id, "Lớp", id_classroom)

    except StudentInfo.DoesNotExist:
        print(f"Student with ID {student_id} does not exist.")
    except Exception as e:
        print(f"An error occurred: {e}")


def draw_progress_bar(frame, progress, x, y, w, h):
    bar_width = 150
    bar_height = 20
    bar_x = x
    bar_y = y - 20
    cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), (0, 0, 0), -1)
    filled_width = int(bar_width * progress)
    cv2.rectangle(frame, (bar_x, bar_y), (bar_x + filled_width, bar_y + bar_height), (0, 255, 0), -1)


def main(id_subject):
    id_subject = id_subject

    INPUT_IMAGE_SIZE = 160
    CLASSIFIER_PATH = 'main/Models/facemodel.pkl'
    FACENET_MODEL_PATH = 'main/Models/20180402-114759.pb'

    with open(CLASSIFIER_PATH, 'rb') as file:
        model, class_names = pickle.load(file)
    print("Custom Classifier, Successfully loaded")

    # Load feature extraction model outside the session
    facenet.load_model(FACENET_MODEL_PATH)
    graph = tf.compat.v1.get_default_graph()
    images_placeholder = graph.get_tensor_by_name("input:0")
    embeddings = graph.get_tensor_by_name("embeddings:0")
    phase_train_placeholder = graph.get_tensor_by_name("phase_train:0")

    cap = cv2.VideoCapture(0)

    global justscanned
    global pause_cnt
    justscanned = False
    pause_cnt = 0
    current_face_name = ""
    current_face_progress = 0

    # Initialize an empty list to store recognized names
    recognized_names = []
    sess = tf.compat.v1.Session(graph=graph)

    while cap.isOpened():
        isSuccess, frame = cap.read()
        if isSuccess:
            image_bbox = model_test.get_bbox(frame)
            if image_bbox is not None:
                x, y, w, h = (image_bbox[0]), (image_bbox[1] - 50), (image_bbox[0] + image_bbox[2]), (
                        image_bbox[1] + image_bbox[3])
                height, width, _ = frame.shape  # Giả sử frame là hình ảnh

                # Chuyển đổi danh sách boxes thành danh sách bounding boxes kiểu int sử dụng map

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
                    prediction += model_test.predict(img, os.path.join(model_dir, model_name))

                label = np.argmax(prediction)
                value = prediction[0][label] / 2
                if label == 1:
                    cropped = frame[y:h, x:w, :]
                    # Check if the cropped image is not empty
                    if cropped is not None and cropped.size > 0:
                        scaled = cv2.resize(cropped, (INPUT_IMAGE_SIZE, INPUT_IMAGE_SIZE),
                                            interpolation=cv2.INTER_CUBIC)
                        scaled = facenet.prewhiten(scaled)
                        scaled_reshape = scaled.reshape(-1, INPUT_IMAGE_SIZE, INPUT_IMAGE_SIZE, 3)
                        feed_dict = {images_placeholder: scaled_reshape, phase_train_placeholder: False}
                        emb_array = sess.run(embeddings, feed_dict=feed_dict)
                        predictions = model.predict_proba(emb_array)
                        best_class_indices = np.argmax(predictions, axis=1)
                        best_class_probabilities = predictions[
                            np.arange(len(best_class_indices)), best_class_indices]
                        best_name = class_names[best_class_indices[0]]

                        if best_class_probabilities > 0.9:
                            if best_name not in recognized_names:
                                if current_face_name != best_name:
                                    current_face_name = best_name
                                    current_face_progress = 0
                                    justscanned = False
                                elif not justscanned:
                                    current_face_progress += 1
                                    progress = current_face_progress / 30
                                    draw_progress_bar(frame, progress, x, y, w, h)

                                cv2.rectangle(frame, (x, y), (w, h), (0, 255, 0), 2)
                                text_x = x
                                text_y = h + 20
                                cv2.putText(frame, best_name, (text_x, text_y), cv2.FONT_HERSHEY_COMPLEX_SMALL,
                                            1,
                                            (255, 255, 255), thickness=1, lineType=2)
                                cv2.putText(frame, str(round(best_class_probabilities[0], 3)),
                                            (text_x, text_y + 17), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1,
                                            (255, 255, 255), thickness=1, lineType=2)

                                if current_face_progress >= 30:
                                    justscanned = True
                                    recognized_names.append(best_name)
                                    insert = insert_attendance(id_subject, best_name)
                                    print(insert)
                                    if current_face_name != "SUCCESS":
                                        print("Success: Face Recognized as", insert)
                            else:
                                message = f"{best_name} da diem danh."
                                cv2.rectangle(frame, (x, y), (w, h), (0, 0, 255),
                                              2)  # Red bounding box for duplicates
                                cv2.putText(frame, message, (x, y - 10), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1,
                                            (0, 0, 255), thickness=1, lineType=2)
                        else:
                            current_face_name = "UNKNOWN"
                            current_face_progress = 0
                            justscanned = False
                            cv2.rectangle(frame, (x, y), (w, h), (0, 255, 0), 2)
                            text_x = x
                            text_y = h + 20
                            cv2.putText(frame, current_face_name, (text_x, text_y),
                                        cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (255, 255, 255), thickness=1,
                                        lineType=2)
                else:
                    result_text = "Gia mao !!!".format(value)
                    color = (0, 255, 255)
                    cv2.rectangle(
                        frame,
                        (image_bbox[0], image_bbox[1] - 50),
                        (image_bbox[0] + image_bbox[2], image_bbox[1] + image_bbox[3]),
                        # Increase the height by 20 pixels
                        color, 2)

                    cv2.putText(
                        frame,
                        result_text,
                        (image_bbox[0], image_bbox[1]),
                        cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, color, thickness=1,
                        lineType=2)

        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    sess.close()
    cap.release()
    cv2.destroyAllWindows()
