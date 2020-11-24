import os
import numpy as np
import picamera
from picamera.array import PiMotionAnalysis

class GestureDetector(PiMotionAnalysis):
    QUEUE_SIZE = 10 # 要分析的连续帧数
    THRESHOLD = 4.0 # 任一轴所需的最小平均运动量

    def __init__(self, camera):
        super(GestureDetector, self).__init__(camera)
        self.x_queue = np.zeros(self.QUEUE_SIZE, dtype=np.float)
        self.y_queue = np.zeros(self.QUEUE_SIZE, dtype=np.float)
        self.last_move = ''

    def analyze(self, a):
        # 滚动队列并使用新均值覆盖第一个元素（相当于pop和append，但速度更快）
        self.x_queue[1:] = self.x_queue[:-1]
        self.y_queue[1:] = self.y_queue[:-1]
        self.x_queue[0] = a['x'].mean()
        self.y_queue[0] = a['y'].mean()
        # 计算x，y两个队列的平均值
        x_mean = self.x_queue.mean()
        y_mean = self.y_queue.mean()
        # 将左/上转换为-1，将右/下转换为1，将低于阈值的移动转换为0
        x_move = (
            '' if abs(x_mean) < self.THRESHOLD else
            'left' if x_mean < 0.0 else
            'right')
        y_move = (
            '' if abs(y_mean) < self.THRESHOLD else
            'down' if y_mean < 0.0 else
            'up')
        # 更新展示
        movement = ('%s %s' % (x_move, y_move)).strip()
        if movement != self.last_move:
            self.last_move = movement
            if movement:
                print(movement)

with picamera.PiCamera(resolution='VGA', framerate=24) as camera:
    with GestureDetector(camera) as detector:
        camera.start_recording(
            os.devnull, format='h264', motion_output=detector)
        try:
            while True:
                camera.wait_recording(1)
        finally:
            camera.stop_recording()