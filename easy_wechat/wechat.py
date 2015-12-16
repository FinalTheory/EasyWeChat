#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Author: 黄龑(huangyan13@baidu.com)
# Created Time: 2015/12/11 12:44
# Description:
#
# Copyright (c) 2014 Baidu.com, Inc. All Rights Reserved
#

"""
微信企业号消息接口封装模块
由于该模块直接与微信服务端进行交互, 因此无需单测
只要能够正确返回结果即可
"""

import os
import sys
import time
import copy
import json
import logging
import tempfile

import flask
import requests

import easy_wechat.utils as utils

WEIXIN_URL = 'https://qyapi.weixin.qq.com'


class WeChatClient(object):
    """
    消息发送类
    """

    def __init__(self, appname, ini_name=None):
        """
        构造函数
        @param appname: 应用名称, 需要与配置文件中section对应
        @return: WeChatClient对象实例
        """
        self.appname = appname
        if ini_name:
            self.config = utils.get_config(ini_name)
        else:
            self.config = utils.get_config()
        self.CorpID = self.config.get(self.appname, 'corpid')
        self.Secret = self.config.get(self.appname, 'secret')
        self.AppID = self.config.get(self.appname, 'appid')

    @staticmethod
    def url_request(url, get=True, data=''):
        """
        请求指定的URL
        @param url: 字符串
        @param get: 是否使用GET方法
        @param data: 附加数据(POST)
        @return: 转换为dict的请求结果
        """
        if get:
            req = requests.get(url)
            res = json.loads(req.content)
        else:
            req = requests.post(url, data)
            res = json.loads(req.content)
        return res

    def get_token(self):
        """
        获取发送消息时的验证token
        @return: token字符串
        """
        token_url = '%s/cgi-bin/gettoken?corpid=%s&corpsecret=%s' \
                    % (WEIXIN_URL, self.CorpID, self.Secret)
        res = self.url_request(token_url)
        return res['access_token']

    def send_text(self, message, touser, toparty='', totag=''):
        """
        发送消息给指定的用户
        @param message: 消息体
        @param touser: 用户名, '|'分割
        @param toparty: 分组名, '|'分割
        @param totag: 标签名, '|'分割
        @return: 服务器返回值
        """
        send_url = '%s/cgi-bin/message/send?access_token=%s' \
                   % (WEIXIN_URL, self.get_token())
        message_data = {
            "touser": touser,
            "toparty": toparty,
            "totag": totag,
            "msgtype": "text",
            "agentid": self.AppID,
            "text": {
                "content": message
            },
            "safe": "0"
        }
        raw_data = json.dumps(message_data, ensure_ascii=False)
        res = self.url_request(send_url, False, raw_data)
        logger = logging.getLogger('easy_wechat')
        if int(res['errcode']) == 0:
            logger.info('send message successful')
        else:
            logger.error('send message failed with error: %s' % res['errmsg'])
        return res

    def upload_media(self):
        pass


class WeChatServer(object):
    """
    消息接收类(server)
    """
    app = flask.Flask(__name__)
    config = utils.get_config()
    wxcpt = None
    callback_funcs = {
        'text': None,
        'image': None,
        'voice': None,
        'video': None,
        'shortvideo': None,
        'location': None,
    }

    def __new__(cls, *args, **kwargs):
        """
        重载__new__函数, 实现单例模式
        @param args:
        @param kwargs:
        @return:
        """
        if not hasattr(cls, '_instance'):
            orig = super(WeChatServer, cls)
            cls._instance = orig.__new__(cls, *args)
        return cls._instance

    def __init__(self, appname, ini_name=None):
        """
        构造函数
        @param appname: APP名称, 与配置文件中section对应
        @return: 构造的对象
        """
        if ini_name:
            self.config = utils.get_config(ini_name)
        self.init_logger()
        token = self.config.get(appname, 'token')
        aes_key = self.config.get(appname, 'encoding_aes_key')
        corp_id = self.config.get(appname, 'corpid')
        WeChatServer.wxcpt = utils.WXBizMsgCrypt(token, aes_key, corp_id)
        self.appname = appname

    def init_logger(self):
        """
        初始化日志模块相关参数
        @return: None
        """
        logger = logging.getLogger('easy_wechat')
        logger.setLevel(logging.INFO)
        log_path = self.config.get('system', 'log_path')
        log_name = self.config.get('system', 'log_name')

        if not (os.path.exists(log_path) and os.path.isdir(log_path)):
            log_path = tempfile.gettempdir()

        if not log_name:
            log_name = 'easy_wechat.log'

        log_handler = logging.FileHandler(os.path.join(log_path, log_name))
        logger.addHandler(log_handler)

    def register_callback(self, msg_type, func):
        """
        注册收到某种类型消息后的回调函数
        @param msg_type: 消息类型
        @param func: 回调函数
        @return: None
        """
        if msg_type in self.callback_funcs:
            self.callback_funcs[msg_type] = func
        else:
            raise KeyError('Invalid media type.')

    @staticmethod
    @app.route('/weixin', methods=['GET', 'POST'])
    def callback():
        """
        响应对/weixin请求的函数
        @return: 返回响应内容
        """
        method = flask.request.method
        if method == 'GET':
            return WeChatServer.verify()
        elif method == 'POST':
            return WeChatServer.do_reply()
        else:
            logger = logging.getLogger('easy_wechat')
            logger.error('unsupported method, return 405 method not allowed')
            # unknown method, return 405 method not allowed
            flask.abort(405)

    @staticmethod
    def verify():
        """
        验证接口可用性
        @return: 回显字符串
        """
        verify_msg_sig = flask.request.args.get('msg_signature', '')
        timestamp = flask.request.args.get('timestamp', '')
        nonce = flask.request.args.get('nonce', '')
        echo_str = flask.request.args.get('echostr', '')
        # do decoding and return
        ret, echo_str_res = WeChatServer.wxcpt.VerifyURL(verify_msg_sig, timestamp, nonce, echo_str)
        if ret != 0:
            logger = logging.getLogger('easy_wechat')
            logger.error('verification failed with return value %d' % ret)
            # if verification failed, return 403 forbidden
            flask.abort(403)
        else:
            return echo_str_res

    @staticmethod
    def do_reply():
        """
        根据消息类型调用对应的回调函数进行回复
        @return: 回复的消息, 按照微信接口加密
        """
        req_msg_sig = flask.request.args.get('msg_signature', '')
        timestamp = flask.request.args.get('timestamp', '')
        nonce = flask.request.args.get('nonce', '')
        req_data = flask.request.data
        ret, xml_str = WeChatServer.wxcpt.DecryptMsg(req_data, req_msg_sig, timestamp, nonce)
        if ret == 0:
            param_dict = utils.xml_to_dict(xml_str)
            msg_type = param_dict.get("MsgType", '')
            if msg_type in WeChatServer.callback_funcs:
                callback_func = WeChatServer.callback_funcs[msg_type]
                if callback_func:
                    # call the callback function and get return message (dict)
                    res_dict = callback_func(copy.deepcopy(param_dict))
                    default_params = {
                        'ToUserName': param_dict['FromUserName'],
                        'FromUserName': param_dict['ToUserName'],
                        'MsgType': param_dict['MsgType'],
                        'CreateTime': int(time.time())
                    }
                    for key, val in default_params.items():
                        if not res_dict.get(key, None):
                            res_dict[key] = val
                    xml_data = utils.dict_to_xml(res_dict)
                    ret_val, encrypted_data =\
                        WeChatServer.wxcpt.EncryptMsg(xml_data, nonce, timestamp)
                    if ret_val == 0:
                        return flask.Response(encrypted_data, mimetype='text/xml')

        logger = logging.getLogger('easy_wechat')
        logger.error('request failed with request data: %r' % req_data)
        # if decryption failed or all other reasons, return 400 bad request code
        flask.abort(400)

    def run(self, *args, **kwargs):
        """
        启动server线程
        @param args: 参数列表
        @param kwargs: 参数字典
        @return: None
        """
        self.app.run(*args, **kwargs)
