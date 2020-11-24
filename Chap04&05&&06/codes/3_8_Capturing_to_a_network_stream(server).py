import io
import socket
import struct
from PIL import Image

# 启动套接字监听 0.0.0.0:8000 上的连接 (
# 0.0.0.0 表示所有接口)
server_socket = socket.socket()
server_socket.bind(('0.0.0.0', 8000))
server_socket.listen(0)

# 接受连接并建立类文件对象
connection = server_socket.accept()[0].makefile('rb')
try:
    while True:
        # 以32位unsigned int的形式读取图像的长度。 
        # 如果length为零，退出循环
        image_len = struct.unpack('<L', connection.read(struct.calcsize('<L')))[0]
        if not image_len:
            break
        # 构造流保存图像数据并从连接中读取图像数据
        image_stream = io.BytesIO()
        image_stream.write(connection.read(image_len))
        # 回放流，使用PIL将其作为图像打开并处理
        image_stream.seek(0)
        image = Image.open(image_stream)
        print('Image is %dx%d' % image.size)
        image.verify()
        print('Image is verified')
finally:
    connection.close()
    server_socket.close()