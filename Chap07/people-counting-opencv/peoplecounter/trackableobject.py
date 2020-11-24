#-*- coding: UTF-8 -*-
class TrackableObject:
	def __init__(self, objectID, centroid):
		# 存储目标ID
		self.objectID = objectID

		# 形心列表 存储在整个过程中该目标所有的形心位置
		self.centroids = [centroid]
		
		# 是否被计数器统计过的布尔量
		self.counted = False