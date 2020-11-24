from __future__ import (
    unicode_literals,
    absolute_import,
    print_function,
    division,
    )


import io
import time
import picamera
import numpy as np
from numpy.lib.stride_tricks import as_strided

stream = io.BytesIO()
with picamera.PiCamera() as camera:
    # 相机预热2s
    time.sleep(2)
    # 捕获图像，包括Bayer数据
    camera.capture(stream, format='jpeg', bayer=True)
    ver = {
        'RP_ov5647': 1,
        'RP_imx219': 2,
        }[camera.exif_tags['IFD0.Model']]

# 从流末尾提取原始Bayer数据，把数据转换为numpy数组之前，检查header并关闭如果是off状态

offset = {
    1: 6404096,
    2: 10270208,
    }[ver]
data = stream.getvalue()[-offset:]
#assert data[:4] == 'BRCM'
data = data[32768:]
data = np.fromstring(data, dtype=np.uint8)


# V1型号，数据有1952行,每行3264个字节。
# 最后8行数据未使用（因为1944行的最大值分辨率向上取整到最接近的16的倍数）
# V2型号，数据有2480行，每行4128字节。
# 实际上有2464行数据，但传感器的原始大小为2466行，向上取整到最接近的16的倍数即是2480。
# 同样，每行的最后几个字节都没有使用（为什么？）。调整数据大小并去除未使用的字节。

reshape, crop = {
    1: ((1952, 3264), (1944, 3240)),
    2: ((2480, 4128), (2464, 4100)),
    }[ver]
data = data.reshape(reshape)[:crop[0], :crop[1]]

# 水平方向上，每行都由10-字节值构成：首先是4行8-字节值，然后第5行是4个2-字节值。ABCD的排列如下:
#
#  byte 1   byte 2   byte 3   byte 4   byte 5
# AAAAAAAA BBBBBBBB CCCCCCCC DDDDDDDD AABBCCDD
#
# 将数据转换为16-字节的数组，把所有字节左移2位，
# 然后解压每行的第5个byte的字节，去掉包含压缩字节的列


data = data.astype(np.uint16) << 2
for byte in range(4):
    data[:, byte::5] |= ((data[:, 4::5] >> ((4 - byte) * 2)) & 0b11)
data = np.delete(data, np.s_[4::5], 1)

# 把数据拆分为红绿蓝模式，OV5647传感器的Bayer模式是BGGR。
# 第一行是交替的绿、蓝色值，第二行是交替的红、绿色值:
#
# GBGBGBGBGBGBGB
# RGRGRGRGRGRGRG
# GBGBGBGBGBGBGB
# RGRGRGRGRGRGRG
#
# 注意，如果使用vflip或hflip更改捕获的方向，就要相应地调换一下Bayer模式

rgb = np.zeros(data.shape + (3,), dtype=data.dtype)
rgb[1::2, 0::2, 0] = data[1::2, 0::2] # 红色
rgb[0::2, 0::2, 1] = data[0::2, 0::2] # 绿色
rgb[1::2, 1::2, 1] = data[1::2, 1::2] # 绿色
rgb[0::2, 1::2, 2] = data[0::2, 1::2] # 蓝色

# 现在，原始拜耳数据的值和颜色都正确了，但数据仍然需要色彩插值以及后续处理。
#
# 下面展示一种简单的色彩插值法：扫描周围像素的加权平均值
# 得到的值就代表中间像素的Bayer过滤值:

bayer = np.zeros(rgb.shape, dtype=np.uint8)
bayer[1::2, 0::2, 0] = 1 # Red
bayer[0::2, 0::2, 1] = 1 # Green
bayer[1::2, 1::2, 1] = 1 # Green
bayer[0::2, 1::2, 2] = 1 # Blue

# 分配一个数组和输入数据的形状相同输出数组。 然后，定义计算加权平均值（3x3）的window。
# 然后，填充rgb和bayer数组，在数组边缘，通过添加空白像素来计算边缘像素的平均值。

output = np.empty(rgb.shape, dtype=rgb.dtype)
window = (3, 3)
borders = (window[0] - 1, window[1] - 1)
border = (borders[0] // 2, borders[1] // 2)

rgb = np.pad(rgb, [
    (border[0], border[0]),
    (border[1], border[1]),
    (0, 0),
    ], 'constant')
bayer = np.pad(bayer, [
    (border[0], border[0]),
    (border[1], border[1]),
    (0, 0),
    ], 'constant')

# RGB数据中的每个平面，用numpy的（as_strided）来构建3x3矩阵。
# 对拜耳数组做同样的事情，然后爱因斯坦求和（np.sum更简单，但复制数据更慢），并除以结果得到加权平均值：

for plane in range(3):
    p = rgb[..., plane]
    b = bayer[..., plane]
    pview = as_strided(p, shape=(
        p.shape[0] - borders[0],
        p.shape[1] - borders[1]) + window, strides=p.strides * 2)
    bview = as_strided(b, shape=(
        b.shape[0] - borders[0],
        b.shape[1] - borders[1]) + window, strides=b.strides * 2)
    psum = np.einsum('ijkl->ij', pview)
    bsum = np.einsum('ijkl->ij', bview)
    output[..., plane] = psum // bsum


# 这时，输出应该就是一个比较“正常”的图片，但是还是不像相机的正常输出（因为缺少晕影补偿，AWB等）。
# 如果想在图像软件（如GIMP）中查看，需要将数据转换为8位RGB。 最简单的方法是将所有数据右移2位

output = (output >> 2).astype(np.uint8)
with open('image4_16.data', 'wb') as f:
    output.tofile(f)