import picamera

camera = picamera.PiCamera()
# 关闭相机的 LED灯
camera.led = False
# 当相机LED灯灭的时候拍张照
camera.capture('foo16.jpg')