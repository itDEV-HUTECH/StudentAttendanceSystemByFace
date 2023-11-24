import base64
import os

import cv2
from facenet_pytorch import MTCNN

color = (255, 0, 0)

thickness = 2

max_images = 300
device_id = 0

capturing_done = False
from src.anti_spoof_predict import AntiSpoofPredict

max_images = 300
device_id = 0


def capture(ID):
    image_count = 0
    max_images = 300  # Set the desired number of images to capture
    model_test = AntiSpoofPredict(device_id)
    capture = cv2.VideoCapture(0)
    output_dir = f"./main/data/test_images/{ID}"
    print(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    captured_images = []  # List to store captured images

    while image_count < max_images:
        ret, frame = capture.read()
        image_bbox = model_test.get_bbox(frame)
        if image_bbox is not None:
            x, y, w, h = (image_bbox[0]), (image_bbox[1] - 50), (image_bbox[0] + image_bbox[2]), (
                    image_bbox[1] + image_bbox[3])
            cropped_face = frame[y:h, x:w]
            if cropped_face is not None and cropped_face.size != 0:
                cropped_face = cv2.resize(cropped_face, (160, 160))

                image_filename = os.path.join(output_dir, f"{image_count}.jpg")
                cv2.imwrite(image_filename, cropped_face)

                cv2.rectangle(frame, (x, y), (w, h), color, thickness)
                image_count += 1

                cv2.putText(frame, f"Image Count: {image_count}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                            (255, 255, 255), 1)

                captured_images.append(cropped_face)  # Store the captured image

        ret, buffer = cv2.imencode('.jpg', frame)
        if ret:
            base64_image = base64.b64encode(buffer).decode('utf-8')

            # Send the image as base64 to the client
            response_data = {
                'image': base64_image,
                'image_count': image_count
            }

    return captured_images, response_data


