# 2021更新
重写了一遍，修改了使用方式
重做了cloudflare的教程

目录结构和仓库一样
    /src/
    │   example.py
    │   readme.md
    │
    └───ddns
            cf.py
            tools.py
            __init__.py
## 使用方法
命令行中输入
py .\example.py [domain] [Zone_ID] [token] [4/6]
顺序应该是可以随便换，但是记得两个变量之间插入空格
|变量名|含义|
|domain|使用的domain名称，形如example.com或a.example.com|
|Zone ID|从Cloudflare中得到，代表这个域名|
|token|从Cloudflare中得到，需要在页面中创建|
|4/6|代表ddns使用的是ipv4/ipv6，输入6或者4即可|
例如
    py .\example.py example.com f5a5e86ea16a1abd22f43a9624ed7060 72UYVeU3dgxGnXPjRxCwIckkwGcHUQQtIHkT09cN     
    py .\example.py ipv6.example.com f5a5e86ea16a1abd22f43a9624ed7060 72UYVeU3dgxGnXPjRxCwIckkwGcHUQQtIHkT09cN  6
或者release的exe
    ddns.exe  example.com f5a5e86ea16a1abd22f43a9624ed7060 72UYVeU3dgxGnXPjRxCwIckkwGcHUQQtIHkT09cN     
    ddns.exe  ipv6.example.com f5a5e86ea16a1abd22f43a9624ed7060 72UYVeU3dgxGnXPjRxCwIckkwGcHUQQtIHkT09cN  6

## cloudflare中的流程，可结合原readme看
先进入 https://dash.cloudflare.com/ 
点进任何一个域名的卡片之后，拉到底就能看到这个
![](https://p.sda1.dev/3/8982d2b3e67b1c85ad5184eaff682bb4/)
在1中，可以得到第一个需要得到的参数
然后点击2，根据步骤得到API TOKEN
点击创建Token
![](https://p.sda1.dev/3/d330ceaf4802758135a91b575d7ce387/)
使用 修改DNS 模板
![](https://p.sda1.dev/3/80b089fe203503ea078c8bc5aa8a55bc/)
默认权限为Edit不需要动
特定Zone可以使用Specific Zone然后在后面的选项中提供希望修改的域名，或者直接选择All Zones获得所有域名的修改权限
![](https://p.sda1.dev/3/8d9097e723e5b1fbf4a958409f2b6725/)
确认页面，直接点击创建Tokens
![](https://p.sda1.dev/3/27c23539ecf67360870168890d501b92/)
7中的圈是希望得到的第二个参数，也就是API Token的权限，如果丢失需要重复上述步骤
![](https://p.sda1.dev/3/2d6d04c66299c21ff01382eb49dc2424/)

像这样子得到了Zone ID和API Token之后，就可以运行了
    py .\example.py a.nmb.buzz   f5a5e86ea16a1abd12f43a9624ed7060   72UYVeU3dgxGnXPjRxCwIckkwGcHUQQtIHkT06cN

这里的步骤不包括购买域名和把域名挂到cloudflare上的步骤，不过这些比较容易找到，不再赘述

以下为原有Readme

----

使用python与cloudflare的api进行通讯以时时更新记录内容，从而实现ddns的功能

# 0. 在开始之前
  * 这一节是从得到域名开始直到能够使用cf进行ddns的设置过程的例子
  * 这里的内容大致如下
    * 文件（虽然只有两个）的基本概述
    * 从域名服务商手中购买域名（如果你会请跳过）
    * 从Cloudflare的页面找到需要的内容（如果你会请跳过）
## 0.0 基本信息

|文件名|概述|
|---|---|
|ddns.py|脚本本体，python3.6.4|
|ddns.json|配置文件，放在同一目录下，不能缺失，文件名不能修改（特别是对使用exe来说）|
|ddns.exe|使用pyinstaller生成的可执行文件，pyinstaller3.3.1，Windows-10-10.0.17763-SP0（兼容性大概会很糟糕）|

exe在[release](https://github.com/Hana-ame/cloudflare-ddns-python/releases)的压缩包里

## 0.1 域名服务商的设置
  * 这一节的具体操作会根据你购买域名时选择的商家不同而不同
  * 这一节的目的是将域名交给cloudflare进行解析

注 ：直接根据cloudflare给出的向导进行设置即可

在购买域名的服务商的管理页面中找到类似NameServer Manager的管理页面中填入cf给出的服务器网址即可

（需要先开出cf的向导）

## 0.2 cloudflare的设置
  * 这一节的目的是从cloudflare的管理页面中得到需要的参数

|参数名|概述|
|---|---|
|name|自由设定，解析的名称，单纯的字符串对应二级域名，直接输入域名（例：example.com）以更新主域名|
|Zone|cf给出，对应每一个域名的id|
|Authorization|cf给出，授权|
|recordID|cf给出，若新记录则无需设定，每一条记录对应的id|
|isSetedID|本地变量（True，False），对应是否是第一次执行|
|sleeptime|本地变量，对应每次查询本机IP的相隔时间（秒）|

第一次使用时，name、Zone、Authorization是必填选项，isSetedID为false，sleeptime挑选一个喜欢的数字即可
### 0.2.1 name的设置
name是由用户自决的，填入一个字串
>例:
>
>"name":"abc"会更新到abc.example.com 也就是二级域名
>
>而"name":"example.com"则会直接更新到example.com 也就是一级域名
  * example.com是自己购入的域名
### 0.2.2 Zone的设置
Zone可以cf中，域名的overview的右边栏靠下的位置，在API中的Zone ID找到，
### 0.2.3 Authorization
这一脚本使用了cf提供的API Token作为授权，对于第一次使用来说，授权需要手动从cf的控制页面中产生

接下来会说明Token的生成过程

1. 在0.2.1节中的API栏目的下方点入Get your API key
2. 在上方的选项卡中选择API Tokens
    * 这个界面的网址形如  https://dash.cloudflare.com/[一串随机数，代表账户]/profile/api-tokens
3. 点击Create Tokens
4. 选择 Start with a template，使用Edit zone DNS模板
5. 改变Zone Resources中的Select..选择需要操作的域名
6. 将token填入json文件中的Authorization栏目（需要保留Bearer）
# 1. 使用方式
完成必要信息的录入后（见0.2节），直接运行即可

重新运行时，若未有更改，可直接运行

# 2. 其他
自己虽然能用，但没有经过细致的debug和兼容性测试，如果有反馈的话我大概会试着解决的

能够ddns并不代表能够解决内网的端口映射[1]、防火墙或公网IP[2]的问题
  1. 大体上是需要UPnP（需要网关/路由支持）或者端口映射（需要网关/路由支持）
     * 其实自购的路由器应该都有的，但如果是运营商的路由可能有限制，一般能破解
  2. 比如打电话投诉之类（类似城通长宽这种运营商就别想了）
     * 虽然我没用过
   * 这些问题的解决方案可参见其他教程
  * 如果用的是虚拟拨号上网（ADSL）那么恭喜你大概很有可能直接拥有公网IP，关闭防火墙应该就能连上了吧

域名的购买，可以选择xyz或top这些首年收费很低的域名（大约10元左右）

  * 此外，如果对隐私有洁癖的话，可以尝试选择国外的一些域名商
  
 最后  

 说到底大概没人会看吧，那么，总之如有需要请随意联系吧



