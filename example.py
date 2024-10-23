import ddns
import json
import time
import re

import Tools


ddns.cf.ZONE_ID = 'your_zone_id'
ddns.cf.TOKEN   = 'your_token'

name = 'your.domain'
def getip(method: str = 'local'):
    f = {
        'ipv6': ddns.getIPv6,
        'ipv4': ddns.getIPv4,
        'local': ddns.get_local_ip,
    }
    return (f.get(method) or ddns.get_local_ip)()
method = 'local'

ddns.cf.ZONE_ID = Tools.parse_args(lambda x: re.findall(r'[0-9a-f]{32}', x) ) or ddns.cf.ZONE_ID
ddns.cf.TOKEN = Tools.parse_args(lambda x: len(x) > 32) or ddns.cf.TOKEN
name = Tools.parse_args(lambda x: (Tools.parse_endswith(x, ['.py', '.exe']) is None) and len(x.split('.')) > 1) or name
method = Tools.parse_args(lambda x: x.lower() in ['ipv4', 'v4', '4'], lambda x:'ipv4') or method
method = Tools.parse_args(lambda x: x.lower() in ['ipv6', 'v6', '6'], lambda x:'ipv6') or method

print("模式为：\t"+method)
print("ZONE_ID为：\t"+ ddns.cf.ZONE_ID)
print("TOKEN为：\t",ddns.cf.TOKEN)
print("域名为：\t",name)

recordID = ''
ip = None

i = 0
while ip is None:
    ip = getip(method)
    if ip is not None:
        print("得到本机IP为 " + ip)
    else: 
        i += 1
    if i > 5 :
        print("已经重试{}次，考虑网络是否正常".format(i))
    

html = None
while html is None:
    if html is None:
        print("尝试取得原有列表")
    html = ddns.cf.listRecords()
    # print(html)
j = json.loads(html)

id_list = []
for i in j['result']:
    if i['zone_name'] != ddns.getroot(name):
        print("请注意输入与zoneID相称的域名")
        print("输入的域名:" + name)
        print("Zone指示为:" + i['zone_name'])
        print("之后的行为未定义")
    if i['name'] == name:
        id_list.append(i['id'])

# 只留一条记录
for i in id_list[1:]:
    result = None
    while result is None:   
        print("尝试删除记录 " + i)
        result = ddns.cf.deleteRecorde(i)

# 如果没有记录，则创建
if len(id_list) == 0:
    result = None
    while result is None:
        print("尝试创建记录 " + name)
        result = ddns.cf.createRecord(ddns.getname(name),ip)
    j = json.loads(result)
    if j['success'] is not True:
        print('创建记录不成功，没写处理代码，请重新启动')
    recordID = j['result']['id']
else:
    # 否则取出id
    recordID = id_list[0]
    result = None
    while result is None:
        print('尝试修改记录', name, ip, recordID)
        result = ddns.cf.updateRecord(ddns.getname(name),ip,recordID)
    j = json.loads(result)
    if j['success'] is not True:
        print('更新记录不成功，没写处理代码，请重新启动')

while 1:    
    time.sleep(10)
    nextip = getip(method)
    if ip == nextip:
        print("ip未变动", ip)
        continue
    if nextip is None:
        print("也许是网断了")    
        continue
    ip = nextip
    print('修改记录', name, ip, recordID)
    result = ddns.cf.updateRecord(ddns.getname(name),ip,recordID)
    

print('祝您身体健康，再见')

exit(0)
