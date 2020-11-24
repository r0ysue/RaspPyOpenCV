#-*- coding: UTF-8 -*-
# 调用所需库
from scipy.spatial import distance as dist
from collections import OrderedDict
import numpy as np

class CentroidTracker():
	def __init__(self, maxDisappeared=50):
		# 初始化下一个新出现人脸的ID
		# 初始化两个有序字典 
		# objects用来储存ID和形心坐标
		# disappeared用来储存ID和对应人脸已连续消失的帧数
		self.nextObjectID = 0
		self.objects = OrderedDict()
		self.disappeared = OrderedDict()

		# 设置最大连续消失帧数
		self.maxDisappeared = maxDisappeared

	def register(self, centroid):
		# 分别在两个字典中注册新人脸 并更新下一个新出现人脸的ID
		self.objects[self.nextObjectID] = centroid
		self.disappeared[self.nextObjectID] = 0
		self.nextObjectID += 1

	def deregister(self, objectID):
		# 分别在两个字典中注销已经消失的人脸
		del self.objects[objectID]
		del self.disappeared[objectID]

	def update(self, rects):
		# 检查输入的人脸外接矩形列表是否为空
		if len(rects) == 0:
			# 对每一个注册人脸 标记一次消失
			for objectID in self.disappeared.keys():
				self.disappeared[objectID] += 1

				# 当连续消失帧数超过最大值时 注销人脸
				if self.disappeared[objectID] > self.maxDisappeared:
					self.deregister(objectID)

			# 因为没有识别到人脸 本次更新结束
			return self.objects

		# 对于当前帧 初始化外接矩形形心的存储矩阵
		inputCentroids = np.zeros((len(rects), 2), dtype="int")

		# 对于每一个矩形执行操作
		for (i, (startX, startY, endX, endY)) in enumerate(rects):
			# 计算形心
			cX = int((startX + endX) / 2.0)
			cY = int((startY + endY) / 2.0)
			inputCentroids[i] = (cX, cY)

		# 如果当前追踪列表为空 则说明这些矩形都是新人脸 需要注册
		if len(self.objects) == 0:
			for i in range(0, len(inputCentroids)):
				self.register(inputCentroids[i])

		# 否则需要和旧人脸进行匹配
		else:
			# 从字典中获取ID和对应形心坐标
			objectIDs = list(self.objects.keys())
			objectCentroids = list(self.objects.values())

			# 计算全部已有人脸的形心与新图像中人脸的形心的距离 用于匹配
			# 每一行代表一个旧人脸形心与所有新人脸形心的距离
			# 元素的行代表旧人脸ID 列代表新人脸形心
			D = dist.cdist(np.array(objectCentroids), inputCentroids)

			# 接下来的两步用于匹配新物体和旧物体
			# min(axis=1)获得由每一行中的最小值组成的向量 代表了距离每一个旧人脸最近的新人脸的距离
			# argsort()将这些最小值进行排序 获得的是由相应索引值组成的向量
			# rows里存储的是旧人脸的ID 排列顺序是按照‘最小距离’从小到大排序
			rows = D.min(axis=1).argsort()

			# argmin(axis=1)获得每一行中的最小值的索引值，代表了距离每一个旧人脸最近的新人脸的ID
			# cols里存储的是新人脸的ID 按照rows排列
			cols = D.argmin(axis=1)[rows]

			# 为了防止重复更新、注册、注销 我们设置两个集合存储已经更新过的row和col
			usedRows = set()
			usedCols = set()

			# 对于所有(row,col)的组合执行操作
			for (row, col) in zip(rows, cols):
				# row和col二者之一被检验过 就跳过 
				if row in usedRows or col in usedCols:
					continue

				# 更新已经匹配的人脸 
				objectID = objectIDs[row]
				self.objects[objectID] = inputCentroids[col]
				self.disappeared[objectID] = 0

				# 更新以后将索引放入已更新的集合
				usedRows.add(row)
				usedCols.add(col)

			# 计算未参与更新的row和col
			unusedRows = set(range(0, D.shape[0])).difference(usedRows)
			unusedCols = set(range(0, D.shape[1])).difference(usedCols)

			# 如果距离矩阵行数大于列数 说明旧人脸数大于新人脸数
			# 有一些人脸在这帧图像中消失了
			if D.shape[0] >= D.shape[1]:
				# 对于没有用到的旧人脸索引
				for row in unusedRows:
					# 获取它的ID 连续消失帧数+1
					objectID = objectIDs[row]
					self.disappeared[objectID] += 1

					# 检查连续消失帧数是否大于最大允许值 若是则注销
					if self.disappeared[objectID] > self.maxDisappeared:
						self.deregister(objectID)

			# 如果距离矩阵列数大于行数 说明新人脸数大于旧人脸数
			# 有一些新人脸出现在了视频中 需要进行注册 
			else:
				for col in unusedCols:
					self.register(inputCentroids[col])

		# 返回追踪列表
		return self.objects