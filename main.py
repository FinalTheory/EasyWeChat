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


def reply_func(param_dict):
    param_dict['Content'] = u'hello, world'
    return param_dict


if __name__ == '__main__':
    server = easy_wechat.WeChatServer('demo')
    server.register_callback('text', reply_func)
    server.run(host='0.0.0.0', port=6000, debug=False)
