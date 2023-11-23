import os
import time
import warnings

import cv2
import numpy as np
from facenet_pytorch import MTCNN

mtcnn = MTCNN()
from src.anti_spoof_predict import AntiSpoofPredict
from src.generate_patches import CropImage
from src.utility import parse_model_name

warnings.filterwarnings('ignore')


def test(model_dir, device_id):
    model_test = AntiSpoofPredict(device_id)
    image_cropper = CropImage()
    capture = cv2.VideoCapture(1)  # 0 là số thứ tự của camera, có thể thay đổi nếu bạn có nhiều camera.

    while True:
        ret, frame = capture.read()
        if not ret:
            break

        image_bbox = model_test.get_bbox(frame)
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

        print("Prediction cost {:.2f} s".format(test_speed))
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

        ret, buffer = cv2.imencode('.jpg', frame)
        if ret:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n\r\n')

    capture.release()
    cv2.destroyAllWindows()
