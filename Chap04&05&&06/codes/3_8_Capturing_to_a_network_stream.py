import io
import socket
import struct
import time
import picamera

# 客户端套接字连接到 my_server:8000 
# (把my_server换成你服务器的主机名)
client_socket = socket.socket()
client_socket.connect(('192.168.1.103', 8000))

# 建立类文件对象
connection = client_socket.makefile('wb')
try:
    camera = picamera.PiCamera()
    camera.resolution = (640, 480)
    # 启动预览，并让相机预热2秒
    camera.start_preview()
    time.sleep(2)

    # 注意开始时间并构造一个暂时保存图像数据的流
    #（也可以直接将其写入连接，但为了是通信协议简单，需要确立每个捕获图像的大小）
    start = time.time()
    stream = io.BytesIO()
    for foo in camera.capture_continuous(stream, 'jpeg'):
        # 把捕获的长度写入流并刷新以确保真的有发送
        connection.write(struct.pack('<L', stream.tell()))
        connection.flush()
        # 回放流并通过网络发送图像数据
        stream.seek(0)
        connection.write(stream.read())
        # 如果超过 30 秒没有捕获, 则退出
        if time.time() - start > 30:
            break
        # 重置流以便下次捕获
        stream.seek(0)
        stream.truncate()
    # 在流中写入一个零长度，表示已经结束
    connection.write(struct.pack('<L', 0))
finally:
    connection.close()
    client_socket.close()