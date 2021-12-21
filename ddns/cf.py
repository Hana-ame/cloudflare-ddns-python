import urllib
import urllib.request
import urllib.parse
import json

ZONE_ID    = 'f5a5e86ea16a1ab312f43a9624ed7060'  # 这个标识了域名
TOKEN      = '72UYxeU3dgxGnXPjRxCwIckkwGcHUQQtIHkT06cN' # api授权，请按照指示生成
# 请不要给任何人看你的TOKEN，这里的示范已经经过了修改

def gen_headers(token=TOKEN,mode=None):
    if mode == 'GET':
        return {
            "User-Agent"     :  "curl/7.55.1", # 更改以防被ban
            "Authorization"  :  "Bearer "+TOKEN,
            # "Content-Type"   :  "application/json",
        }
    return {
        "User-Agent"     :  "curl/7.55.1", # 更改以防被ban
        "Authorization"  :  "Bearer "+TOKEN,
        "Content-Type"   :  "application/json",
    }
def gen_A(name="@",ip="127.0.0.1"):
    return {
        "type":"A",
        "name": name,
        "content": ip,
        "ttl":1,
        "proxied":False
    }
def gen_AAAA(name="@",ip="::1"):
    return {
        "type":"AAAA",
        "name": name,
        "content": ip,
        "ttl":1,
        "proxied":False
    }

def listRecords(token=TOKEN):
    req = urllib.request.Request(
        'https://api.cloudflare.com/client/v4/zones/' + ZONE_ID + '/dns_records',
        headers=gen_headers(TOKEN, 'GET'),
    )
    try:
        with urllib.request.urlopen(req,timeout=5) as response:
            html = response.read()
            return html.decode()
    except:
        return None

def createRecord(name,ip,token=TOKEN):
    data = gen_A(name,ip)
    if len(ip.split(':'))>1: # IPv6
        data = gen_AAAA(name,ip)
    pl = json.dumps(data)
    pl = pl.encode()
    req = urllib.request.Request(
        'https://api.cloudflare.com/client/v4/zones/' + ZONE_ID + '/dns_records',
        headers=gen_headers(TOKEN),
        data=pl,
        method='POST'
    )
    try:
        with urllib.request.urlopen(req,timeout=10) as response:
            html = response.read()
            return html.decode()
    except:
        return None

def updateRecord(name,ip,id,token=TOKEN):
    data = gen_A(name,ip)
    if len(ip.split(':'))>1: # IPv6
        data = gen_AAAA(name,ip)
    pl = json.dumps(data)
    pl = pl.encode()
    req = urllib.request.Request(
        'https://api.cloudflare.com/client/v4/zones/' + ZONE_ID + '/dns_records/' + id,
        headers=gen_headers(TOKEN),
        data=pl,
        method='PUT'
    )
    try:
        with urllib.request.urlopen(req,timeout=10) as response:
            html = response.read()
            return html.decode()
    except:
        return None

def deleteRecorde(id,token=TOKEN):
    req = urllib.request.Request(
        'https://api.cloudflare.com/client/v4/zones/' + ZONE_ID + '/dns_records/' + id,
        headers=gen_headers(TOKEN),
        method='DELETE'
    )
    try:
        with urllib.request.urlopen(req,timeout=10) as response:
            html = response.read()
            return html.decode()
    except:
        return None