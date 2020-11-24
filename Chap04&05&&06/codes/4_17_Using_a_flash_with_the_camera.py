import picamera

with picamera.PiCamera() as camera:
    camera.flash_mode = 'on'
    camera.capture('foo4_17.jpg')