import socket
import subprocess

# 启动套接字监听 0.0.0.0:8000 上的连接 (
# 0.0.0.0 表示所有接口)
server_socket = socket.socket()
server_socket.bind(('0.0.0.0', 8000))
server_socket.listen(0)

# 接受连接并建立类文件对象
connection = server_socket.accept()[0].makefile('rb')
try:
    #使用命令行运行视频播放器。 要用mplayer的话，取消注释mplayer这一行
    cmdline = ['vlc', '--demux', 'h264', '-']
    #cmdline = ['mplayer', '-fps', '25', '-cache', '1024', '-']
    player = subprocess.Popen(cmdline, stdin=subprocess.PIPE)
    while True:
        # 从连接中反复读取1k数据并将其写入媒体播放器的标准输入
        data = connection.read(1024)
        if not data:
            break
        player.stdin.write(data)
finally:
    connection.close()
    server_socket.close()
    player.terminate()