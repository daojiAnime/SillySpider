# -*- coding: utf-8 -*-
from io import BytesIO

import requests
import hashlib
from PIL import Image

__author__ = 'Daoji'
__date__ = '2020/4/28 9:20'

# !/bin/env python
# -*- coding: UTF-8 -*-

from multiprocessing import Pool
import threading
import os
import sys
import pdb
import time
import pprint
import gevent
from gevent.queue import Queue

g_progress_num = 4 # 进程数 等于这个数*2
g_read_gevent_num = 10 # 页面解析的协程数
g_set__gevent_num = 5 # 图片下载的协程数

page_queue = Queue(100) # 页面队列数
img_queue = Queue(1000) # 图片队列数
page_size = 50 # 每页表情数
for page_num in range(1, 2):
    page_queue.put(f'http://www.dbbqb.com/api/search/json?round={page_num}&size={page_size}')


def gevent_set_job(n):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.122 Safari/537.36',
    }
    try:
        while True:
            print(f'page_queue:{page_queue.qsize()};img_queue:{img_queue.qsize()}\r')
            if page_queue.empty() and img_queue.empty():
                break
            resp = requests.get(img_queue.get(), headers=headers)
            img_type = resp.headers.get('Content-Type')
            bytes_io = BytesIO(resp.content)
            img = Image.open(bytes_io)
            # img.show()

            name = resp.headers.get('Content-MD5') if resp.headers.get('Content-MD5') else hashlib.md5(
                resp.content).hexdigest()
            path_name = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'image',
                                     f'{hashlib.md5(name.encode("utf8")).hexdigest()}')

            if img_type == 'image/jpg':
                if img.format == 'JPEG':
                    with open(f'{path_name}.jpg', mode='wb') as f:
                        f.write(resp.content)
            elif img_type == 'image/gif':
                with open(f'{path_name}.gif', mode='wb') as f:
                    f.write(resp.content)
            elif img_type == 'image/png':
                with open(f'{path_name}.png', mode='wb') as f:
                    f.write(resp.content)
            elif img_type == 'image/webp':
                if img.mode == 'RGBA':
                    img.load()  # required for png.split()
                    canvas = Image.new('RGB', img.size, (255, 255, 255))
                    canvas.paste(img, mask=img.split()[3])
                    # 保存图片为jpg
                    img.save(f'{path_name}.jpg', 'JPEG')
            else:
                print('未知格式')
    except Exception as e:
        print("[ERROR]:{0} {1}".format(time.ctime(), e), file=sys.stderr)
        sys.exit(1)


def gevent_read_job(n):
    try:
        if page_queue.empty():
            return
        response = requests.get(page_queue.get())
        for item in response.json():
            img_queue.put('http://image.dbbqb.com/' + item['path'])
        print(len(response.json()))
    except Exception as e:
        print("[ERROR]:{0} {1}".format(time.ctime(), e))


def work_page_progress():
    reads = [gevent.spawn(gevent_read_job, i) for i in range(100)]
    gevent.joinall(reads)


def work_img_progress():
    sets = [gevent.spawn(gevent_set_job, i) for i in range(2)]
    gevent.joinall(sets)


#####Start from here!###########
if __name__ == '__main__':
    print("Start time: {0} ".format(time.ctime()))
    p = Pool(g_progress_num)
    for i in range(g_progress_num):
        p.apply_async(work_page_progress)
        p.apply_async(work_img_progress)
    p.close()
    p.join()
    # work_progress()
    print("End time: {0} ".format(time.ctime()))
