from picamera import PiCamera
from time import sleep
from fractions import Fraction

# 强制启动传感器的mode 3（长曝光模式）设置帧速率为 1/6fps, 快门速度为6s,
# ISO 设置为 800 (获得最大增益)
camera = PiCamera(
    resolution=(1280, 720),
    framerate=Fraction(1, 6),
    sensor_mode=3)
camera.shutter_speed = 6000000
camera.iso = 800
# 给足够时间让相机调整增益和白平衡
# (也可以用固定白平衡)
sleep(30)
camera.exposure_mode = 'off'
# 最后，捕获一张6s长曝光的图像，
# 由于模式切换也要消耗时间，所以实际会比6s长一点
camera.capture('dark.jpg')