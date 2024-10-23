# import requests
# import certifi
# import urllib
import urllib.request

import socket


# v6不需要，如果连不上就是连不上了
# v4Server = ['https://getip.moonchan.xyz']

# 代码在家里，回家之后再改，现在临时用外面的API
def getIPv4():
    req = urllib.request.Request(
        'http://getip.moonchan.xyz/',
        headers={"User-Agent":"curl/7.55.1"},
    )
    try:
        with urllib.request.urlopen(req,timeout=10) as response:
            html = response.read()
            return html.decode()
    except:
        return None

def get_local_ip():
    # 创建一个 socket 对象
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # 连接到一个外部地址（不需要实际连接）
        s.connect(("8.8.8.8", 80))
        # 获取本机的 IP 地址
        ip = s.getsockname()[0]
    finally:
        s.close()
    
    return ip

def getIPv6():
    ipstr = None
    try:
        s = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        s.connect(('2001:da8:20d:22::2',80)) # edu.cn
        ipstr = s.getsockname()[0]
        s.close()
        return ipstr
    except:
        return None

def getroot(url):
    l = url.split('.')
    if len(l) <2 or url.startswith('http://') or url.startswith('https://'):
        raise Exception('请检查url是否符合规范：{} \n url应该形如 thisisan.example.com 或 example.com 或 another.example.com'.format(url))
    return '.'.join(l[-2:])


def getname(url):
    l = url.split('.')
    if len(l) <= 2:
        return "@"
    return '.'.join(l[:-2])