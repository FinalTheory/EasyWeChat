## EasyWeChat: 超轻量的微信企业号快速开发框架

### 简介

在某些不涉及传输敏感数据的情况下，为了监控自己的服务器（如VPS、NAS），或者实现一个自动应答的机器人，我们可能需要利用微信的消息服务来实现自动且及时的提醒。微信的“企业号”服务提供了每天最大30*200条的主动消息推送，以及不限次数的消息自动回复，因此十分适合这类需求。然而微信的接口设计非常繁琐，因此本框架使用了非常少的代码来对微信的接口进行封装，使得轻度用户可以只关注所需要实现的逻辑本身，而不用与微信的繁琐接口打交道。

本项目的目标，是希望用户在仅仅阅览该页面以及部分微信接口文档的情况下，能够**快速开发**出一个可用的微信企业号服务。


### 特性

- 支持文本、图片、视频、语音等消息类型的发送与接收
- 极简的开发流程，只需注册一个回复消息的回调函数
- 基于Flask框架，自身代码量非常少，方便按需定制


### 应用

#### 程序猿搬砖监控器

为了方便家人以及妹子查看码农是否在公司搬砖，还是已经回家打PS4，并且避免打扰到程序猿写代码时的思路，故开发这个监控器，其硬件如下：

<img src="https://raw.githubusercontent.com/FinalTheory/EasyWeChat/master/images/monkey_monitor.jpg" width="400">

实现的效果是，通过发送消息给对应的企业号，可以让摄像头自动拍照并回复该照片，或者录一段视频并回复。

<img src="https://raw.githubusercontent.com/FinalTheory/EasyWeChat/master/images/wechat.png" width="250">

也可以直接访问某域名（如pi.xxx.com）实时查看摄像头所拍摄到的视频流，但这样由于经过VPS中转，速度可能略卡。

<img src="https://raw.githubusercontent.com/FinalTheory/EasyWeChat/master/images/stream.png" width="250">

至此，家人和妹子就不用发消息询问程序猿是否还在加班了。

配置方法：

- 在树莓派上运行EasyWeChat，监听8000端口；
- 使用`ngrok`将树莓派的8000端口映射到远程VPS上的某端口，例如同样为8000端口；
- 增加`nginx`转发规则，将对80端口的特定域名的请求（如pi.xxx.com）转发到8000端口。

其中`nginx`转发规则示意如下：

    server {
        listen 80;
        server_name pi.xxx.com;
        location / {
            proxy_pass http://pi.xxx.com:8000;
        }
    }


#### 12306余票监控

Loading……


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

此外，如果需要获得更好的并发处理能力，建议不要使用Flask自带的Server，因为它主要用来调试的，只是简单的多线程实现。可以直接采用`gevent`并发框架来获得更好的并发性能。示例代码如下：

    from gevent.wsgi import WSGIServer
    
    http_server = WSGIServer(('', 8000), server.app)
    http_server.serve_forever()


### 文档

#### 主动发送消息

首先实例化一个`client`对象：

    client = WeChatClient('demo')

其中`demo`是`config.ini`中对应section的名称。

然后调用`client`对象的`send_media`方法以发送消息。示例代码如下：

    client.send_media(
        'text', {"content": 'message'}, 'user_name')

`send_media`函数的各个参数含义请直接参考代码注释。总而言之，这些参数遵循参考链接[1]中的微信企业号接口约定，并去除了冗余部分。


#### 回调式响应消息

首先实例化一个`server`对象：

    server = MonkeyServer('demo')

然后为需要自动回复的消息类型注册回调函数，如下所示表示注册一个回复`text`文本类型消息的回调函数：

    server.register_callback('text', reply_func)

EasyWeChat会以一个字典作为传入参数来调用回调函数，**字典的内容符合参考链接[2]中的企业号消息回调约定**。开发者所注册的回调函数需要返回一个**字典**，其中内容应该“大致”符合参考链接[3]中的消息返回值约定。

最后启动Server接受请求即可，可以选择使用gevent框架或者Flask自带Server。

其他细节请参阅源代码以及示例应用。


### 已知限制：

- 由于Flask框架的内部使用了Python的signal等机制，因此`EasyWeChat`必须运行于主线程。


### 参考资料

[1] http://qydev.weixin.qq.com/wiki/index.php?title=消息类型及数据格式  
[2] http://qydev.weixin.qq.com/wiki/index.php?title=接收普通消息  
[3] http://qydev.weixin.qq.com/wiki/index.php?title=被动响应消息  
