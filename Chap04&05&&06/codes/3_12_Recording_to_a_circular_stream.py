import io
import random
import picamera

def motion_detected():
    # 随机返回True (类似运动检测)
    return random.randint(0, 10) == 0

camera = picamera.PiCamera()
stream = picamera.PiCameraCircularIO(camera, seconds=20)
camera.start_recording(stream, format='h264')
try:
    while True:
        camera.wait_recording(1)
        if motion_detected():
            # 保持录制10秒，然后将流写入磁盘
            camera.wait_recording(10)
            stream.copy_to('motion.h264')
finally:
    camera.stop_recording()