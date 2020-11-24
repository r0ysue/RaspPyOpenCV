#-*- coding: UTF-8 -*-	
# 调用必需库
from imutils.video import VideoStream
from imutils.video import FPS
from imutils.object_detection import non_max_suppression
import numpy as np
import argparse
import imutils
import time
import cv2

def decode_predictions(scores, geometry):
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

	# 返回一个外接矩形及其对应置信度的tuple
	return (rects, confidences)

# 设置命令行参数
ap = argparse.ArgumentParser()
ap.add_argument("-east", "--east", type=str, required=True,
	help="path to input EAST text detector")
ap.add_argument("-v", "--video", type=str,
	help="path to optinal input video file")
ap.add_argument("-c", "--min-confidence", type=float, default=0.5,
	help="minimum probability required to inspect a region")
ap.add_argument("-w", "--width", type=int, default=320,
	help="resized image width (should be multiple of 32)")
ap.add_argument("-e", "--height", type=int, default=320,
	help="resized image height (should be multiple of 32)")
args = vars(ap.parse_args())

# 初始化原图像和处理后图像的高度与宽度，并初始化缩放率
(W, H) = (None, None)
(newW, newH) = (args["width"], args["height"])
(rW, rH) = (None, None)

# 定义我们关注的EAST检测器2个输出层
# 第1层是结果的置信度 第2层可用于获取文字的外边框
layerNames = [
	"feature_fusion/Conv_7/Sigmoid",
	"feature_fusion/concat_3"]

# 加载训练好的EAST 文字检测器
print("[INFO] loading EAST text detector...")
net = cv2.dnn.readNet(args["east"])

# 如果没有提供视频文件的路径 则从摄像头中抓取图像
if not args.get("video", False):
	print("[INFO] starting video stream...")
	vs = VideoStream(src=0).start()
	time.sleep(1.0)

# 如果提供了视频文件路径 则从文件中抓取图像
else:
	vs = cv2.VideoCapture(args["video"])

# 启动帧率估计
fps = FPS().start()

# 对视频流中的图像循环
while True:
	# 抓取下一帧 并根据视频流的来源作调
	frame = vs.read()
	frame = frame[1] if args.get("video", False) else frame

	# 检查视频流是否结束
	if frame is None:
		break

	# 缩放图像帧 并保持长宽比
	frame = imutils.resize(frame, width=1000)
	orig = frame.copy()

	# 如果高或宽为空，我们需要获取当前图像的高度和宽度并计算缩放率
	if W is None or H is None:
		(H, W) = frame.shape[:2]
		rW = W / float(newW)
		rH = H / float(newH)

	# 缩放图像 这次忽略长宽比 
	frame = cv2.resize(frame, (newW, newH))

	# 创建一个blob 并在网络模型中前向传递 获得两个输出层score geometry
	blob = cv2.dnn.blobFromImage(frame, 1.0, (newW, newH),
		(123.68, 116.78, 103.94), swapRB=True, crop=False)
	net.setInput(blob)
	(scores, geometry) = net.forward(layerNames)

	# 调用decode_predictions函数获取外边框及相应置信度 
	# 应用非极大值抑制法删除重复或不可靠的结果
	(rects, confidences) = decode_predictions(scores, geometry)
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

	# 更新帧率估算
	fps.update()

	# 显示输出帧
	cv2.imshow("Text Detection", orig)
	key = cv2.waitKey(1) & 0xFF

	# 如果按下'q'键 则跳出循环
	if key == ord("q"):
		break

# 停止计数器 并显示帧数
fps.stop()
print("[INFO] elasped time: {:.2f}".format(fps.elapsed()))
print("[INFO] approx. FPS: {:.2f}".format(fps.fps()))

# 如果我们使用的是摄像头 则释放调用
if not args.get("video", False):
	vs.stop()

# 如果使用的是视频文件 则释放调用
else:
	vs.release()

# 关闭所有窗口
cv2.destroyAllWindows()