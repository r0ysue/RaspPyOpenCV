from io import BytesIO
from time import sleep
from picamera import PiCamera

# 创建内存流
my_stream = BytesIO()
camera = PiCamera()
camera.start_preview()
# 相机预热时间
sleep(2)
camera.capture(my_stream, 'jpeg')

from time import sleep
from picamera import PiCamera

# 打开一个叫my_image.jpg的文件
my_file = open('my_image.jpg', 'wb')
camera = PiCamera()
camera.start_preview()
sleep(2)
camera.capture(my_file)
# 此时，my_file.flush()已经被调用,但是还没有关闭
my_file.close()