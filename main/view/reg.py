import pickle
from datetime import datetime

import cv2
import imutils
import numpy as np
import tensorflow as tf
from imutils.video import VideoStream

from main import facenet
from main.align import detect_face
from main.models import Classroom, Attendance, StudentInfo, StudentClassDetails


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
    bar_width = 300
    bar_height = 20
    bar_x = x
    bar_y = y + h
    cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), (0, 0, 0), -1)
    filled_width = int(bar_width * progress)
    cv2.rectangle(frame, (bar_x, bar_y), (bar_x + filled_width, bar_y + bar_height), (0, 255, 0), -1)


def main(id_subject):
    id_subject = id_subject
    MINSIZE = 20
    THRESHOLD = [0.6, 0.7, 0.7]
    FACTOR = 0.709
    INPUT_IMAGE_SIZE = 160
    CLASSIFIER_PATH = 'main/Models/facemodel.pkl'
    FACENET_MODEL_PATH = 'main/Models/20180402-114759.pb'

    with open(CLASSIFIER_PATH, 'rb') as file:
        model, class_names = pickle.load(file)
    print("Custom Classifier, Successfully loaded")

    with tf.Graph().as_default():
        with tf.compat.v1.Session() as sess:
            print('Loading feature extraction model')
            facenet.load_model(FACENET_MODEL_PATH)
            images_placeholder = tf.compat.v1.get_default_graph().get_tensor_by_name("input:0")
            embeddings = tf.compat.v1.get_default_graph().get_tensor_by_name("embeddings:0")
            phase_train_placeholder = tf.compat.v1.get_default_graph().get_tensor_by_name("phase_train:0")
            embedding_size = embeddings.get_shape()[1]
            pnet, rnet, onet = detect_face.create_mtcnn(sess, "main/align")
            cap = VideoStream(src=0).start()
            # Initialize variables for progress tracking
            global justscanned
            global pause_cnt
            justscanned = False
            pause_cnt = 0
            current_face_name = ""
            current_face_progress = 0

            # Initialize an empty list to store recognized names
            recognized_names = []

            while True:
                frame = cap.read()
                frame = imutils.resize(frame, width=600)
                bounding_boxes, _ = detect_face.detect_face(frame, MINSIZE, pnet, rnet, onet, THRESHOLD, FACTOR)
                faces_found = bounding_boxes.shape[0]

                for i in range(faces_found):
                    bb = bounding_boxes[i, 0:4]
                    if bb is not None:
                        x, y, w, h = bb.astype(int)
                        # Check if the bounding box is valid
                        if w > 0 and h > 0:
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
                                        message = f"{best_name} has already been marked."
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
                # ...
                ret, buffer = cv2.imencode('.jpg', frame)
                frame = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            cap.release()
            cv2.destroyAllWindows()
