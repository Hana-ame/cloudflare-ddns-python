import socket
import json, urllib3, certifi, time

class ApiConn:
    def __init__(self, name, Authorization, Zone, recordID):
        self.nowIP = '::1'   
        self.lastIP = '::1'
        self.http = urllib3.PoolManager(
            cert_reqs='CERT_REQUIRED',
            ca_certs=certifi.where()
        )
        self.myHeaders = {
            "Authorization"  :  Authorization,
            "Content-Type"   :  "application/json"
        }
        self.url = 'https://api.cloudflare.com/client/v4/zones/{0}/dns_records/{1}'.format(Zone,recordID)
        self.data = {
            "type":"AAAA",
            "name": name,
            "content": self.nowIP,
            "ttl":1,
            "proxied":False
            }
        self.renew()
    def get_v6addr(self):
        try:
            s = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
            s.connect(('2001:da8:20d:22::2',80)) # edu.cn
            self.lastIP = s.getsockname()[0]
        except:
            print("获取地址ERROR")
        finally:
            s.close()
        print("获取地址为", self.lastIP)
        return self.lastIP
    def renew(self):
        self.get_v6addr()
        # print(self.lastIP, self.nowIP)
        if self.lastIP != self.nowIP:
            try:        
                self.data["content"] = self.lastIP
                r = self.http.request(
                    'PUT',
                    self.url,
                    body = json.dumps(self.data).encode('utf-8'),
                    headers = self.myHeaders
                )
                if json.loads(r.data.decode())['success']: # 应为True
                    # 处理结束，等待下一次
                    print("成功将记录更新为{}".format(self.lastIP))  
                self.nowIP = self.lastIP
            except:
                print("更新记录ERROR")

# def main():
print("准备初始化")
api = ApiConn("www", "Bearer 8CP**********************************qUV", "7b8**************************c57", "0d7**************************218")
while 1:
    api.renew()
    time.sleep(10)
