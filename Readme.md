## EasyWeChat: 超轻量的微信企业号快速开发框架

### 简介

在某些不涉及传输敏感数据的情况下，为了监控自己的服务器（如VPS、NAS），或者实现一个自动应答的机器人，我们可能需要利用微信的消息服务来实现自动且及时的提醒。微信的“企业号”服务提供了每天最大30*200条的主动消息推送，以及不限次数的消息自动回复，因此十分适合这类需求。然而微信的接口设计非常繁琐，因此本框架使用了非常少的代码来对微信的接口进行封装，使得轻度用户可以只关注所需要实现的逻辑本身，而不用与微信的繁琐接口打交道。

本项目的目标，是希望用户在仅仅阅览该页面以及部分微信接口文档的情况下，能够**快速开发**出一个可用的微信企业号服务。


### 特性

- 支持文本、图片、视频、语音等消息类型的发送与接收
- 极简的开发流程，只需注册一个回复消息的回调函数
- 基于Flask框架，自身代码量非常少，方便按需定制


### 应用



### 依赖库

- `flask`
- `requests`
- `pycrypto`
- `dicttoxml/xmltodict`
- `gevent`（可选）


### 文件布局

    EasyWeChat
    ├── Readme.md                项目文档
    ├── app                      用于放置用户代码的目录
    │   ├── demo.py              示例应用：回显服务器(echo server)
    │   ├── monkey_monitor.py    示例应用：程序猿监控器
    │   └── ticket_watcher.py    示例应用：12306余票监控
    ├── config.ini               配置文件（私密）
    ├── config.ini.example       示例配置文件（公开）
    ├── config_test.ini          单元测试配置文件（可安全公开）
    └── easy_wechat              package目录
        ├── __init__.py          package初始化文件
        ├── ierror.py            加解密库错误码定义
        ├── test                 单元测试目录
        │   ├── __init__.py      初始化文件
        │   ├── test_utils.py    utils.py的单元测试
        │   └── test_wechat.py   wechat.py的单元测试
        ├── utils.py             辅助函数（官方加解密库等）
        └── wechat.py            主模块文件，包含与微信企业号接口的交互逻辑


### 示例

为了实现一个最简单的回显服务器（Echo Server，即返回你所发送的内容），仅仅需要以下几行代码：

    import easy_wechat
    
    def reply_func(param_dict):
        return param_dict
    
    if __name__ == '__main__':
        server = easy_wechat.WeChatServer('demo')
        server.register_callback('text', reply_func)
        server.run(host='0.0.0.0', port=6000, debug=False)

并按照格式填写`config.ini`即可。

为了获得持久化的存储，并同时避免使用全局变量，我们也可以直接实例化一个对象，然后将这个对象的成员函数作为回调函数注册给`EasyWeChat`：
    
    class TestClass(object):
        def reply_func(self, param_dict):
            param_dict['Content'] = 'hello, world'
            return param_dict
    
    if __name__ == '__main__':          
        server.register_callback('text', TestClass()

这样，在成员函数内部，我们就可以直接访问对象的成员变量，来实现我们所需要的操作了。

### 文档

#### 主动模式


#### 回调模式


### 已知限制：

- 由于Flask框架的内部使用了Python的signal等机制，因此`EasyWeChat`必须运行于主线程。


### 参考资料

[1] http://qydev.weixin.qq.com/wiki/index.php?title=消息类型及数据格式  
[2] http://qydev.weixin.qq.com/wiki/index.php?title=接收普通消息  
[3] http://qydev.weixin.qq.com/wiki/index.php?title=被动响应消息  