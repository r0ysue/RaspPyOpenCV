import time
import picamera
import numpy as np

# 创建一个数组，表示穿过显示屏中心的十字的1280x720的图像。
# 数组的形状必须是（高度，宽度，颜色）形式
a = np.zeros((720, 1280, 3), dtype=np.uint8)
a[360, :, :] = 0xff
a[:, 640, :] = 0xff

camera = picamera.PiCamera()
camera.resolution = (1280, 720)
camera.framerate = 24
camera.start_preview()

# 将叠加层直接添加到具有透明度的第3层中; 
# 可以省略add_overlay的size参数，因为它的大小与相机的分辨率相同
o = camera.add_overlay(np.getbuffer(a), layer=3, alpha=64)
try:
    # 等待，直到用户终止脚本
    while True:
        time.sleep(1)
finally:
    camera.remove_overlay(o)