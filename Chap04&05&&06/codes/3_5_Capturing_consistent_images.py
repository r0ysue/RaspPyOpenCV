from time import sleep
from picamera import PiCamera

camera = PiCamera(resolution=(1280, 720), framerate=30)
# 设置 ISO 的值
camera.iso = 100
# 等自动增益稳定
sleep(2)
# 固定值
camera.shutter_speed = camera.exposure_speed
camera.exposure_mode = 'off'
g = camera.awb_gains
camera.awb_mode = 'off'
camera.awb_gains = g
# 最后，拍几张固定设置下的照片
camera.capture_sequence(['image%02d.jpg' % i for i in range(10)])