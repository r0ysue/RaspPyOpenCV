from time import sleep
from picamera import PiCamera

camera = PiCamera()
camera.resolution = (1024, 768)
camera.start_preview()
# 相机预热时间
sleep(2)
camera.capture('foo.jpg')