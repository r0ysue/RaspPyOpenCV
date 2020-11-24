import socket
import time
import picamera

# 客户端套接字连接到 my_server:8000 
# (把my_server换成你服务器的主机名)
client_socket = socket.socket()
client_socket.connect(('192.168.1.103', 8000))

# 从连接中建立类文件对象
connection = client_socket.makefile('wb')
try:
    camera = picamera.PiCamera()
    camera.resolution = (640, 480)
    camera.framerate = 24
    # 开启预览并额昂相机预热2秒
    camera.start_preview()
    time.sleep(2)
    # 开始录制，将输出发送到连接60秒，然后停止
    camera.start_recording(connection, format='h264')
    camera.wait_recording(60)
    camera.stop_recording()
finally:
    #connection.close()
    client_socket.close()