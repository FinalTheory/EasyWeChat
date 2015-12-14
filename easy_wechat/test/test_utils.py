#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Author: 黄龑(huangyan13@baidu.com)
# Created Time: 2015/12/11 15:11
# File Name: test_xml.py
# Description: 
#
# Copyright (c) 2014 Baidu.com, Inc. All Rights Reserved
#

"""
XML模块单元测试
"""

import sys
import unittest
import collections

import easy_wechat.utils as utils


class XMLTestCase(unittest.TestCase):
    """
    XML模块单元测试类
    """
    xml_string = '''<xml>
    <ToUserName><![CDATA[mycreate]]></ToUserName>
    <FromUserName><![CDATA[wx5823bf96d3bd56c7]]></FromUserName>
    <CreateTime>1348831860</CreateTime>
    <MsgType><![CDATA[text]]></MsgType>
    <Content><![CDATA[thisisatest]]></Content>
    <MsgId>1234567890123456</MsgId>
    <AgentID>128</AgentID>
    </xml>'''

    def test_xml2dict(self):
        """
        测试XML转Dict
        @return: None
        """
        dict_data = utils.xml_to_dict(self.xml_string)
        self.assertIsInstance(dict_data, collections.OrderedDict)
        self.assertIn('ToUserName', dict_data)
        self.assertIn('FromUserName', dict_data)
        self.assertIn('CreateTime', dict_data)
        self.assertIn('MsgType', dict_data)
        self.assertIn('Content', dict_data)
        self.assertIn('MsgId', dict_data)
        self.assertIn('AgentID', dict_data)

    def test_dict2xml(self):
        """
        测试Dict转XML
        @return: None
        """
        dict_data = utils.xml_to_dict(self.xml_string)
        xml_data = utils.dict_to_xml(dict_data)
        self.assertEqual(xml_data, self.xml_string.replace('\n', '').replace(' ', ''))

    def test_wrap_cdata(self):
        """
        测试将Dict中字符串全部包裹上<![CDATA[]]>标签的函数
        该函数是为了符合微信接口的调用约定
        @return: None
        """
        dict_data = {
            'a': 'test',
            'b': 'test1',
            'c': {
                'test': '123'
            },
            'd': {
                'e': {
                    'f': {
                        'g': {
                            'h': 'test2'
                        }
                    }
                }
            }
        }
        res_data = utils.wrap_cdata(dict_data)
        self.assertEqual(res_data['a'], '<![CDATA[test]]>')
        self.assertEqual(res_data['c']['test'], 123)
        self.assertEqual(res_data['d']['e']['f']['g']['h'], '<![CDATA[test2]]>')

    def test_dict_trans(self):
        """
        测试用于将OrderedDict转换为普通Dict的函数
        @return: None
        """
        ordered = collections.OrderedDict()
        ordered['a'] = 'test'
        ordered['b'] = 'test1'
        ordered['c'] = collections.OrderedDict()
        ordered['c']['d'] = 'test2'
        ordered['c']['e'] = collections.OrderedDict()
        ordered['c']['e']['f'] = 'test3'
        dict_data = utils.ordered_to_dict(ordered)
        self.assertIsInstance(dict_data, dict)
        self.assertIsInstance(dict_data['c'], dict)
        self.assertIsInstance(dict_data['c']['e'], dict)


# test entry
if __name__ == '__main__':
    unittest.main()
