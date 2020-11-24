from io import BytesIO
from time import sleep
from picamera import PiCamera
from PIL import Image

# 创建内存流
stream = BytesIO()
camera = PiCamera()
camera.start_preview()
sleep(2)
camera.capture(stream, format='jpeg')
# 将流的位置倒回到最开始以便读取
stream.seek(0)
image = Image.open(stream)