#-*- coding: UTF-8 -*-	
# 调用必需库
from imutils.object_detection import non_max_suppression
import numpy as np
import argparse
import time
import cv2

# 设置命令行参数
ap = argparse.ArgumentParser()
ap.add_argument("-i", "--image", type=str,
	help="path to input image")
ap.add_argument("-east", "--east", type=str,
	help="path to input EAST text detector")
ap.add_argument("-c", "--min-confidence", type=float, default=0.5,
	help="minimum probability required to inspect a region")
ap.add_argument("-w", "--width", type=int, default=320,
	help="resized image width (should be multiple of 32)")
ap.add_argument("-e", "--height", type=int, default=320,
	help="resized image height (should be multiple of 32)")
args = vars(ap.parse_args())

# 加载图像并获取图像尺寸
image = cv2.imread(args["image"])
orig = image.copy()
(H, W) = image.shape[:2]

# 读取命令行中设置的图像的高度与宽度 根据原图像大小计算缩放比例
(newW, newH) = (args["width"], args["height"])
rW = W / float(newW)
rH = H / float(newH)

# 缩放图像 并更新图像的尺寸
image = cv2.resize(image, (newW, newH))
(H, W) = image.shape[:2]

# 定义我们关注的EAST检测器2个输出层
# 第1层是结果的置信度 第2层可用于获取文字的外边框
layerNames = [
	"feature_fusion/Conv_7/Sigmoid",
	"feature_fusion/concat_3"]

# 加载训练好的EAST 文字检测器
print("[INFO] loading EAST text detector...")
net = cv2.dnn.readNet(args["east"])

# 创建一个blob 并在网络模型中前向传递 获得两个输出层score geometry
blob = cv2.dnn.blobFromImage(image, 1.0, (W, H),
	(123.68, 116.78, 103.94), swapRB=True, crop=False)
start = time.time()
net.setInput(blob)
(scores, geometry) = net.forward(layerNames)
end = time.time()

# 显示当前时间
print("[INFO] text detection took {:.6f} seconds".format(end - start))

# 获取score的行数和列数
# 初始化外边框列表和置信度列表
(numRows, numCols) = scores.shape[2:4]
rects = []
confidences = []

# 对行循环
for y in range(0, numRows):
	# 解析score和geometry中的内容
	scoresData = scores[0, 0, y]
	xData0 = geometry[0, 0, y]
	xData1 = geometry[0, 1, y]
	xData2 = geometry[0, 2, y]
	xData3 = geometry[0, 3, y]
	anglesData = geometry[0, 4, y]

	# 对列循环
	for x in range(0, numCols):
		# 如果置信度没有达到阈值 则跳过这个结果
		if scoresData[x] < args["min_confidence"]:
			continue

		# 最终输出的feature map与原图相比尺寸缩小了4倍 所以这里乘以4得到的是原图的位置
		(offsetX, offsetY) = (x * 4.0, y * 4.0)

		# angle是文字的方向
		angle = anglesData[x]
		cos = np.cos(angle)
		sin = np.sin(angle)

		# 获取外边框的高度和宽度
		h = xData0[x] + xData2[x]
		w = xData1[x] + xData3[x]

		# 计算外边框的两个角点
		endX = int(offsetX + (cos * xData1[x]) + (sin * xData2[x]))
		endY = int(offsetY - (sin * xData1[x]) + (cos * xData2[x]))
		startX = int(endX - w)
		startY = int(endY - h)
		
		# 将外边框和置信度信息存在之前的列表里
		rects.append((startX, startY, endX, endY))
		confidences.append(scoresData[x])

# 采用非极大值抑制法删除重复边框 选取最佳边框
boxes = non_max_suppression(np.array(rects), probs=confidences)

# 对所有筛选出来的边框循环
for (startX, startY, endX, endY) in boxes:
	# 根据缩放率对外边框进行缩放
	startX = int(startX * rW)
	startY = int(startY * rH)
	endX = int(endX * rW)
	endY = int(endY * rH)

	# 在图片上绘制外边框
	cv2.rectangle(orig, (startX, startY), (endX, endY), (0, 255, 0), 2)

# 显示识别结果
cv2.imshow("Text Detection", orig)
cv2.waitKey(0)