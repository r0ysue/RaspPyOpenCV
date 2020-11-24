#-*- coding: UTF-8 -*-
# 调用必需库
import imutils
import cv2

class ObjCenter:
	def __init__(self, haarPath):
		# 加载人脸探测器
		self.detector = cv2.CascadeClassifier(haarPath)

	def update(self, frame, frameCenter):
		# 将图像转为灰度图
		gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

		# 探测图像中的所有人脸
		rects = self.detector.detectMultiScale(gray, scaleFactor=1.05,
			minNeighbors=9, minSize=(30, 30),
			flags=cv2.CASCADE_SCALE_IMAGE)

		# 是否检测到人脸
		if len(rects) > 0:
			# 获取矩形的参数
			# x,y为左上角点坐标，w,h为宽度和高度
	        # 计算图像中心
			(x, y, w, h) = rects[0]
			faceX = int(x + (w / 2.0))
			faceY = int(y + (h / 2.0))

			# 返回人脸中心
			return ((faceX, faceY), rects[0])

		# 如果没有识别到人脸，返回图像中心
		return (frameCenter, None)