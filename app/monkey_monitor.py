#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Author: 黄龑(huangyan13@baidu.com)
# Created Time: 2015/12/30 22:31
# File Name: monkey_monitor.py.py
# Description: 
#
# Copyright (c) 2015 Baidu.com, Inc. All Rights Reserved
#

import os
import sys
import time
import io

module_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(module_dir)
import Queue
import threading
import tempfile
import subprocess
import datetime

import gevent
import picamera
from flask import Response
from flask import request
from gevent.wsgi import WSGIServer

from easy_wechat.wechat import WeChatServer
from easy_wechat.wechat import WeChatClient


class Camera(object):
    thread = None  # background thread that reads frames from camera
    frame = None  # current frame is stored here by background thread
    last_access = 0  # time of last client access to the camera

    def initialize(self):
        if Camera.thread is None:
            # start background frame thread
            Camera.thread = threading.Thread(target=self._thread)
            Camera.thread.start()

            # wait until frames start to be available
            while self.frame is None:
                time.sleep(0)

    def get_frame(self):
        Camera.last_access = time.time()
        self.initialize()
        return self.frame

    @classmethod
    def _thread(cls):
        with picamera.PiCamera() as camera:
            # camera setup
            camera.resolution = (320, 240)
            camera.hflip = False
            camera.vflip = False

            # let camera warm up
            camera.start_preview()
            time.sleep(2)

            stream = io.BytesIO()
            for foo in camera.capture_continuous(stream, 'jpeg',
                                                 use_video_port=True):
                # store frame
                stream.seek(0)
                cls.frame = stream.read()

                # reset stream for next frame
                stream.seek(0)
                stream.truncate()

                # if there hasn't been any clients asking for frames in
                # the last 5 seconds stop the thread
                if time.time() - cls.last_access > 5:
                    break

                # sleep for a while to reduce CPU usage
                gevent.sleep(0.1)
        cls.thread = None


class MonkeyServer(WeChatServer):
    def __init__(self, appname, ini_name=None):
        super(MonkeyServer, self).__init__(appname, ini_name)
        self.app.add_url_rule('/', None, self.index,
                              methods=['POST', 'GET'])
        self.app.add_url_rule('/video_feed', None,
                              self.video_feed, methods=['GET'])

    def video_feed(self):
        def gen(camera):
            """Video streaming generator function."""
            while True:
                try:
                    gevent.sleep(0.1)
                    frame = camera.get_frame()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
                except GeneratorExit:
                    break

        return Response(gen(Camera()),
                        mimetype='multipart/x-mixed-replace; boundary=frame')

    def index(self):
        filename = '/tmp/hello.txt'
        index_str = """
        <html>
        <title>Code Monkey Monitor</title>
        <h1>Real Time Video Streaming</h1>
        <img src="/video_feed">
        <h1>Say Hello To Me</h1>
        <form name="input" action="/" method="post">
        Your name:
        <input type="text" name="name" />
        <input type="submit" value="Say Hello" />
        </form>
        <a href="http://www.yeelink.net/devices/341276/">
        See temperature data from Yeelink</a>
        </html>
        """

        def write_file(name):
            """
            这个函数没神马用, 只是为了好玩
            用来在树莓派LCD屏幕上显示一行字
            @param name:
            @return:
            """
            if not name:
                name = 'null'
            hello_str = 'Hi,I\'m ' + name
            if len(hello_str) > 13:
                hello_str = name[0:min(12, len(name))] + '~'
            with open(filename, 'w') as fid:
                fid.write(hello_str)
            return 'Nice to meet you, ' + name + '~'

        if request.method == 'GET':
            return index_str
        else:
            return write_file(request.form.get('name', ''))


class CameraError(Exception):
    pass


class MonkeyMonitor(object):
    class Worker(threading.Thread):
        def __init__(self, parent):
            super(MonkeyMonitor.Worker, self).__init__()
            self.parent = parent

        def run(self):
            client = self.parent.client
            while True:
                task = self.parent.queue.get()
                if task is None:
                    break
                try:
                    if task[0] == 'image':
                        img_path = self.parent.get_image()
                        res_dict = client.upload_media('image', img_path)
                        if 'media_id' in res_dict:
                            ret = client.send_media(
                                    'image', {'media_id': res_dict['media_id']}, task[1])
                            if ret['errcode'] != 0:
                                raise RuntimeError(ret['errmsg'])
                        os.remove(img_path)
                    else:
                        mp4_path = self.parent.get_video()
                        res_dict = client.upload_media('video', mp4_path)
                        if 'media_id' in res_dict:
                            ret = client.send_media(
                                    'video', {
                                        'media_id': res_dict['media_id'],
                                        "title": datetime.datetime.now().ctime(),
                                        "description": u"如果提示系统繁忙, 请等待一分钟后再试, "
                                                       u"微信服务器需要耗费时间对视频进行转码.",
                                    }, task[1])
                            if ret['errcode'] != 0:
                                raise RuntimeError(ret['errmsg'])
                        os.remove(mp4_path)
                except Exception as e:
                    try:
                        client.send_media(
                                'text', {
                                    "content": e.message
                                }, task[1])
                    except Exception as e:
                        sys.stderr.write('Exception occurred: %s\n' % e.message)

    def __init__(self):
        self.client = WeChatClient('monitor')
        self.queue = Queue.Queue(maxsize=100)
        self.worker = self.Worker(self)
        self.worker.start()

    def get_image(self):
        file_path = tempfile.mktemp('.jpg')
        ret_code = subprocess.call(['raspistill', '-t', '1500',
                                    '-w', '1280', '-h', '920', '-o', file_path])
        if ret_code != 0:
            raise CameraError(u"raspistill命令失败, 可能是由于摄像头被占用")

        return file_path

    def get_video(self):
        file_path = tempfile.mktemp('.h264')
        ret_code = subprocess.call(['raspivid', '-t', '10000',
                                    '-w', '640', '-h', '480', '-o', file_path])
        if ret_code != 0:
            raise CameraError(u"raspivid命令失败, 可能是由于摄像头被占用")

        mp4_path = tempfile.mktemp('.mp4')
        ret_code = subprocess.call(['MP4Box', '-add', file_path, mp4_path])
        if ret_code != 0:
            raise RuntimeError(u"MP4Box转码失败, 请检查环境配置")
        os.remove(file_path)
        return mp4_path

    def reply_func(self, param_dict):
        msg = param_dict['Content']
        if u'拍照' in msg:
            param_dict['Content'] = u'请耐心等待拍照'
            self.queue.put(['image', param_dict['FromUserName']])
        elif u'视频' in msg:
            param_dict['Content'] = u'请耐心等待视频录制, 若想查看实时视频流(可能较卡), ' \
                                    u'请访问: http://pi.finaltheory.me'
            self.queue.put(['video', param_dict['FromUserName']])
        else:
            param_dict['Content'] = u'无法理解您的要求'
        return param_dict


if __name__ == '__main__':
    monitor = MonkeyMonitor()
    # 实例化自动回复类
    server = MonkeyServer('monitor')
    # 注册回调函数
    server.register_callback('text', monitor.reply_func)
    # 使用gevent启动服务器实例
    http_server = WSGIServer(('', 8000), server.app)
    try:
        http_server.serve_forever()
    except KeyboardInterrupt as e:
        sys.stderr.write(e.message + '\n')
        monitor.queue.put(None)
