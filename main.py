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
入口文件, 用于启动服务端接口
"""

import easy_wechat


class TestClass(object):
    """
    测试类, 无实际含义
    """
    def reply_func(self, param_dict):
        """
        一个简答的自动回复函数, 自动给每条消息回复'hello, world'
        @param param_dict: 用户消息的参数
        @return: 向字典中填充对应回复内容后返回
        """
        param_dict['Content'] = 'hello, world'
        return param_dict


if __name__ == '__main__':
    server = easy_wechat.WeChatServer('demo')
    server.register_callback('text', TestClass().reply_func)
    server.run(host='0.0.0.0', port=6000, debug=False)
