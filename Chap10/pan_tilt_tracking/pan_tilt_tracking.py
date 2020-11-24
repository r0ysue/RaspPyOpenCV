#-*- coding: UTF-8 -*-	
# 调用必需库
from multiprocessing import Manager
from multiprocessing import Process
from imutils.video import VideoStream
from pyimagesearch.objcenter import ObjCenter
from pyimagesearch.pid import PID
from gpiozero import AngularServo
import argparse
import signal
import time
import sys
import cv2

# 定义舵机
pan = AngularServo(19, min_angle=-90, max_angle=90, min_pulse_width=0.5/1000,max_pulse_width=2.5/1000)
tilt = AngularServo(16, min_angle=-90, max_angle=90, min_pulse_width=0.5/1000,max_pulse_width=2.5/1000)
  	
# 键盘终止函数
def signal_handler(sig, frame):
    # 输出状态信息
	print("[INFO] You pressed `ctrl + c`! Exiting...")

	# 关闭舵机
	pan.detach()
	tilt.detach()
  
	# 退出
	sys.exit()

def obj_center(args, objX, objY, centerX, centerY):
	# ctrl+c退出进程
	signal.signal(signal.SIGINT, signal_handler)

	# 启动视频流并缓冲
	#vs = VideoStream(usePiCamera=True).start()
	vs = VideoStream(src=0).start()
	time.sleep(2.0)

	# 初始化人脸中心探测器
	obj = ObjCenter(args["cascade"])

	# 进入循环
	while True:

		# 从视频流抓取图像并旋转
		frame = vs.read()
		frame = cv2.flip(frame, 0)

		# 找到图像中心
		(H, W) = frame.shape[:2]
		centerX.value = W // 2
		centerY.value = H // 2

		# 找到人脸中心
		objectLoc = obj.update(frame, (centerX.value, centerY.value))
		((objX.value, objY.value), rect) = objectLoc

		# 绘制人脸外界矩形
		if rect is not None:
			(x, y, w, h) = rect
			cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

			# 显示图像
			cv2.imshow("Pan-Tilt Face Tracking", frame)
			cv2.waitKey(1)

def pid_process(output, p, i, d, objCoord, centerCoord):
	# ctrl+c退出进程
	signal.signal(signal.SIGINT, signal_handler)
	
 	# 创建一个PID类的对象并初始化
	p = PID(p.value, i.value, d.value)
	p.initialize()

	# 进入循环
	while True:
		# 计算误差
		error = centerCoord.value - objCoord.value

		# 更新输出值
		output.value = p.update(error)

def set_servos(panAngle, tiltAngle):
	# ctrl+c退出进程
	signal.signal(signal.SIGINT, signal_handler)

	# 进入循环
	while True:
		# 偏角变号
		yaw = -1 * panAngle.value
		pitch = -1 * tiltAngle.value
      
		# 设置舵机偏角
		pan.angle = yaw
		tilt.angle = pitch
			

# 启动主程序
if __name__ == "__main__":
	# 建立语法分析器
	ap = argparse.ArgumentParser()
	ap.add_argument("-c", "--cascade", type=str, required=True,help="path to input Haar cascade for face detection")
	args = vars(ap.parse_args())

	# 启动多进程变量管理
	with Manager() as manager:
		# 舵机角度置零
		pan.angle = 0;
		tilt.angle = 0;
      
		# 为图像中心坐标赋初值
		centerX = manager.Value("i", 0)
		centerY = manager.Value("i", 0)

		# 为人脸中心坐标赋初值
		objX = manager.Value("i", 0)
	    objY = manager.Value("i", 0)

	    # panAngle和tiltAngle分别是两个舵机的PID控制输出量	    
      	panAngle = manager.Value("i", 0)
		tiltAngle = manager.Value("i", 0)

		# 设置一级舵机的PID参数
		panP = manager.Value("f", 0.09)
		panI = manager.Value("f", 0.08)
	    panD = manager.Value("f", 0.002)

		# 设置二级舵机的PID参数
		tiltP = manager.Value("f", 0.11)
		tiltI = manager.Value("f", 0.10)
		tiltD = manager.Value("f", 0.002)

    	# 创建4个独立进程
        # 1. objectCenter  - 探测人脸
		# 2. panning       - 对一级舵机进行PID控制，控制偏航角
		# 3. tilting       - 对二级舵机进行PID控制，控制俯仰角
		# 4. setServos     - 根据PID控制的输出驱动舵机
		#                    
		processObjectCenter = Process(target=obj_center,args=(args, objX, objY, centerX, centerY))
		processPanning = Process(target=pid_process,args=(panAngle, panP, panI, panD, objX, centerX))
		processTilting = Process(target=pid_process,args=(tiltAngle, tiltP, tiltI, tiltD, objY, centerY))
		processSetServos = Process(target=set_servos, args=(panAngle, tiltAngle))

		# 开启4个进程
		processObjectCenter.start()
		processPanning.start()
		processTilting.start()
		processSetServos.start()

		# 添加4个进程
		processObjectCenter.join()
		processPanning.join()
		processTilting.join()
		processSetServos.join()

		# 关闭舵机
		pan.detach()
		tilt.detach()
