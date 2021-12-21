import ddns
import json
import time

import sys
import re


ddns.cf.ZONE_ID = 'f5a5e86ea16a1abd12f43a9624ed7060'
ddns.cf.TOKEN   = '72UYVeU3dgxGnXPjRxCwIckkwGcHUQQtIHkT06cN'

name = 'tes2t.nmb.buzz'
getip = ddns.getIPv4

for arg in sys.argv:
    if arg[-3:] == '.py':
        continue
    if arg == 'ipv6' or arg == 'IPv6' or arg == 'v6' or arg == '6':
        getip = ddns.getIPv6
        continue
    if arg == 'ipv4' or arg == 'IPv4' or arg == 'v4' or arg == '4':
        getip = ddns.getIPv4
        continue
    if re.findall(r'[0-9a-f]{32}', arg) != []:
        ddns.cf.ZONE_ID = re.findall(r'[0-9a-f]{32}', arg)[0]
        continue
    if len(arg.split('.')) > 1:
        name = arg
    elif len(arg)>32:
        ddns.cf.TOKEN = arg

if getip == ddns.getIPv4:
    print("模式为：\tipv4")
elif getip == ddns.getIPv6:
    print("模式为：\tipv6")
print("ZONE_ID为：\t"+ ddns.cf.ZONE_ID)
print("TOKEN为：\t",ddns.cf.TOKEN)
print("域名为：\t",name)

recordID = ''
ip = None

while ip is None:
    ip = getip()
    print("得到本机IP为 " + ip)

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
    if ip == getip():
        print("ip未变动", ip)
        continue
    ip = getip()
    print('修改记录', name, ip, recordID)
    result = ddns.cf.updateRecord(ddns.getname(name),ip,recordID)
    

print('祝您身体健康，再见')

exit(0)
