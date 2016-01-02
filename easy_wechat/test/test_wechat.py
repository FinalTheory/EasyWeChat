#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Author: 黄龑(huangyan13@baidu.com)
# Created Time: 2015/12/11 19:21
# File Name: test_wechat.py
# Description: 
#
# Copyright (c) 2014 Baidu.com, Inc. All Rights Reserved
#

"""
微信接口单元测试
"""

import mock
import json
import unittest
import urllib

import flask
import werkzeug.exceptions as http_exceptions

import easy_wechat.utils as utils
import easy_wechat


class MockResponse(object):
    """
    模拟的Response对象
    """
    def __init__(self, json_data, status_code):
        """
        构造函数
        @param json_data: 返回的json数据
        @param status_code: 返回的状态码
        @return: 构造完成的Response对象
        """
        self.json_data = json_data
        self.status_code = status_code

    @property
    def content(self):
        """
        返回请求内容
        @return: 请求内容
        """
        return self.json_data


def mocked_requests_get(*args, **kwargs):
    """
    Mock Request库中的get操作
    @param args: 参数列表
    @param kwargs: 参数字典
    @return: 模拟的Response对象
    """
    return MockResponse(json.dumps({'access_token': 'fuck'}), 200)


def mocked_requests_post(*args, **kwargs):
    """
    Mock Request库中的post操作
    @param args: 参数列表
    @param kwargs: 参数字典
    @return: 模拟的Response对象
    """
    data = json.loads(args[1])
    if data['touser'] == 'FinalTheory':
        return MockResponse(json.dumps({'errcode': 0,
                                        'errmsg': 'ok'}), 200)
    else:
        return MockResponse(json.dumps({'errcode': 1,
                                        'errmsg': 'error'}), 400)


class TestWeChat(unittest.TestCase):
    """
    单测入口类
    """
    def test_send_test(self):
        """
        测试能否正常发送消息
        @return: None
        """
        with mock.patch('requests.get', side_effect=mocked_requests_get):
            with mock.patch('requests.post', side_effect=mocked_requests_post):
                client = easy_wechat.WeChatClient('demo', 'config_test.ini')
                res_dict = client.send_media('text', {'content': 'hello, world'}, 'FinalTheory')
                self.assertEqual(res_dict['errcode'], 0)
                self.assertNotEqual(
                        client.send_media('text', {'content': 'hello, world'},
                                          '645645')['errcode'], 0)

    def test_callback(self):
        """
        测试回调是否正常工作
        @return: None
        """
        with mock.patch('flask.request') as mock_request:
            type(mock_request).method = mock.PropertyMock(return_value='FUCK')
            server = easy_wechat.WeChatServer('demo', 'config_test.ini')
            self.assertRaises(http_exceptions.MethodNotAllowed,
                              server.callback)

    def test_receive_msg_err(self):
        """
        测试接收消息时参数错误是否抛出异常
        @return: None
        """
        param_dict = {
            'msg_signature': '',
            'timestamp': '',
            'nonce': '',
        }
        with mock.patch('flask.request') as mock_request:
            type(mock_request).method = mock.PropertyMock(return_value='POST')
            type(mock_request).args = mock.PropertyMock(return_value=param_dict)
            type(mock_request).data = mock.PropertyMock(return_value='')
            server = easy_wechat.WeChatServer('demo', 'config_test.ini')
            self.assertRaises(http_exceptions.BadRequest, server.callback)

    def test_receive_msg_OK(self):
        """
        测试接收正确消息时是否能够返回Response对象
        @return: None
        """
        recv_data = ('<xml><ToUserName><![CDATA[wx82ef843a5129db66]]>'
                     '</ToUserName><Encrypt><![CDATA[OoM+8tz/6B7iGq55'
                     'mU5PoP6u9w4iJW2BP/L8MWMRGMGll3kue5NRtkqPcOwUVdyFTW'
                     'saqUYvFXm0k7WVTt5d1ixBCb8FupfKP3eIar7ZPqwf7CYlXFT/'
                     'vxUkO/y12LNr7LOJzxe2hKDwBMyZ/SJEo0OYuit8BzfiyvlBv'
                     '300lnqDUnGvOumfp25i3WVxzV3FulKg/8VvAbqTBhiTUL3oRH'
                     'xbBCIth6HlrNlrT4ePVz0Azkh++hRL57IRHU+FTTFz9wLjnyhm'
                     'Agd8ka/j/SMrGtF0SiIGTjbzdWViKI8Jmpzox1N4ggBoABmbZTA'
                     'HqgZZIKsKwVFnmZg+4kGbqDff+BuHqGzyuIVzfORJNTHT8sS8G'
                     'meODAJeO+9HtR6lOO981tlsvfWgYAsfGyzMxRh1gxTEWBfqz6P'
                     'A1unAlfLUNjr54Q0aJOwP2ELqQnMYFgggSGqoe638SISc3bLle'
                     'rvxdw==]]></Encrypt><AgentID><![CDATA[2]]></AgentID></xml>')
        param_dict = {
            'msg_signature': '3483710b6ece7efff2dfcebb8aa258347eea6313',
            'timestamp': '1450092658',
            'nonce': '2095700682',
        }

        def reply_func(param):
            """
            自动回复函数
            @param param: 输入参数
            @return: 返回参数
            """
            param['Content'] = 'hello, world'
            return param
        with mock.patch('flask.request') as mock_request:
            # mock properties
            type(mock_request).method = mock.PropertyMock(return_value='POST')
            type(mock_request).args = mock.PropertyMock(return_value=param_dict)
            type(mock_request).data = mock.PropertyMock(return_value=recv_data)
            # load the server and do tests
            server = easy_wechat.WeChatServer('demo', 'config_test.ini')
            server.register_callback('text', reply_func)
            self.assertIsInstance(server.callback(), flask.Response)

    def test_verify_err(self):
        """
        测试微信接口验证功能是否能够正确报错
        @return: None
        """
        param_dict = {
            'msg_signature': '',
            'timestamp': 0,
            'nonce': '',
            'echostr': '123',
        }
        with mock.patch('flask.request') as mock_request:
            type(mock_request).method = mock.PropertyMock(return_value='GET')
            type(mock_request).args = mock.PropertyMock(return_value=param_dict)
            type(mock_request).data = mock.PropertyMock(return_value='')
            server = easy_wechat.WeChatServer('demo', 'config_test.ini')
            self.assertRaises(http_exceptions.Forbidden, server.callback)

    def test_verify_OK(self):
        """
        测试是否能够正确完成接口验证
        @return: None
        """
        echo_str = ('JJbZng5xDFUaE4UhtGVct3ksIzuIeh2Hik4Jf%2BHtuJPppSyv7'
                    'gaNY%2FplvblHZRe1JVMv3XGj9fST8ppx62lArQ%3D%3D')
        param_dict = {
            'msg_signature': 'fa5e779b1eeb709358f9742db4704ff932754a45',
            'timestamp': '1450093931',
            'nonce': '112775',
            'echostr': urllib.unquote(echo_str),
        }
        with mock.patch('flask.request') as mock_request:
            type(mock_request).method = mock.PropertyMock(return_value='GET')
            type(mock_request).args = mock.PropertyMock(return_value=param_dict)
            type(mock_request).data = mock.PropertyMock(return_value='')
            config = utils.get_config('config_test.ini')
            token = '8wdYqOgJWQlFRE13FaBAUOU2FxXVtGr'
            aes_key = config.get('demo', 'encoding_aes_key')
            corp_id = config.get('demo', 'corpid')

            server = easy_wechat.WeChatServer('demo', 'config_test.ini')
            server.wxcpt = utils.WXBizMsgCrypt(token, aes_key, corp_id)
            self.assertIsInstance(server.callback(), str)


if __name__ == '__main__':
    unittest.main()
