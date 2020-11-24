import io
import random
import picamera
from PIL import Image

prior_image = None

def detect_motion(camera):
    global prior_image
    stream = io.BytesIO()
    camera.capture(stream, format='jpeg', use_video_port=True)
    stream.seek(0)
    if prior_image is None:
        prior_image = Image.open(stream)
        return False
    else:
        current_image = Image.open(stream)
        # 将current_image与prior_image进行比较以检测运动。 
        # 留给读者练习！
        result = random.randint(0, 10) == 0
        # 完成运动检测后，将先前图像设为当前图像
        prior_image = current_image
        return result

with picamera.PiCamera() as camera:
    camera.resolution = (1280, 720)
    stream = picamera.PiCameraCircularIO(camera, seconds=10)
    camera.start_recording(stream, format='h264')
    try:
        while True:
            camera.wait_recording(1)
            if detect_motion(camera):
                print('Motion detected!')
                # 一旦检测到运动，就进行分割，分开以记录“运动后”的帧
                camera.split_recording('after.h264')
                # “运动前”的10秒也写入磁盘
                stream.copy_to('before.h264', seconds=10)
                stream.clear()
                # 等到不再检测到运动，然后将记录拆分到内存中的循环缓冲区
                while detect_motion(camera):
                    camera.wait_recording(1)
                print('Motion stopped!')
                camera.split_recording(stream)
    finally:
        camera.stop_recording()