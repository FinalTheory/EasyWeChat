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


# test entry
if __name__ == '__main__':
    unittest.main()
