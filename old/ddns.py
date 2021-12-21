# ddns.py
# ddns with cloudflare api and remote_ip

import json, urllib3, certifi, time

filepath = "./ddns.json"

fp = open(filepath)
config = json.load(fp)
fp.close()

name  = config['name']
Authorization = config['Authorization'] 
Zone  = config['Zone']
recordID = config['recordID'] 
isSetedID = config['isSetedID']
sleeptime = config['sleeptime']

class Log:
    def d(s):
        print(s)
    def i(s):
        print(s)
    def w(s):
        print(s)
    def e(s):
        print(s)

# 制作访问http访问物件
http = urllib3.PoolManager(
    cert_reqs='CERT_REQUIRED',
    ca_certs=certifi.where()
    )
# 指定文件头
myHeaders = {
    "Authorization"  :  Authorization,
    "Content-Type"   :  "application/json"
    }
# 获取自家ip
myIp = http.request("GET","http://ip.3322.net/")
myIp = myIp.data.strip().decode()
myData = {
    "type":"A",
    "name":name,
    "content": myIp,
    "ttl":1,
    "proxied":False
    }
# 初始处理
if isSetedID : # 在未有值的时候设置为false
    Log.i("记录ID似乎已经存在，直接进入更新部分")
    myIp = "newIP"
else:
    r = http.request(
        'POST',
        'https://api.cloudflare.com/client/v4/zones/{0}/dns_records'.format(Zone),
        body = json.dumps(myData).encode('utf-8'),
        headers = myHeaders
        )
    # 接受返回值
    r = json.loads(r.data)
    if r['success']: # 应为True
        # 处理结束，等待下一次
        Log.i("成功创建记录{0}".format(name))
        Log.i("接下来请不要关闭以保持更新")
        recordID = r['result']['id']
        # 更新json
        config['recordID'] = recordID
        config['isSetedID'] = True
        fp = open(filepath,'w')
        json.dump(config,fp)
        fp.close()
        Log.i("json文件已保存")
        # 删掉（有必要吗）
        del(config)
        time.sleep(sleeptime)
    else:
        if r['errors'][0]['code'] == 81057:
            print("记录已存在，请设置id以更新或更换name")
            print(r.data)
            time.sleep(sleeptime*1000)
        else:
            print(r.data)
# 实时更新
while 1:
    try:
        # 刷新自家ip
        newIp = http.request("GET","http://ip.3322.net/")
        newIp = newIp.data.strip().decode()
        # 仅当自家ip改变时
        if newIp != myIp: 
            Log.d('myIp = {}'.format(myIp))
            Log.d('newIp = {}'.format(newIp))
            myIp = newIp
            # 更新内容物
            myData['content'] = newIp
            # 发送数据
            r = http.request(
                'PUT',
                'https://api.cloudflare.com/client/v4/zones/{0}/dns_records/{1}'.format(Zone,recordID),
                body = json.dumps(myData).encode('utf-8'),
                headers = myHeaders
                )
            # 接受返回值
            if json.loads(r.data.decode())['success']: # 应为True
                # 处理结束，等待下一次
                Log.i("成功将记录更新为{}".format(myIp))
                time.sleep(sleeptime)
            else:
                print(r.data)
                myIp = "error!"
        else:
            Log.d("IP未改变 {}".format(myIp))
            time.sleep(sleeptime)
    except Exception:
        Log.e("靠腰")
        myIp = "error!"
        Log.e(r.data)
        pass
    finally:
        pass