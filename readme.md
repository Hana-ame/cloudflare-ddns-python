# deepseek在上

看[deepseek.py](deepseek.py)
变量写到同文件夹`.env`里面，其实感觉不是很需要注释了，问AI吧。

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
|---|---|
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
先进入 https://dash.cloudflare.com/  \
点进任何一个域名的卡片之后，拉到底就能看到这个

![](https://p.sda1.dev/3/8982d2b3e67b1c85ad5184eaff682bb4/)

在1中，可以得到第一个需要得到的参数 \
然后点击2，根据步骤得到API TOKEN \
点击创建Token \

![](https://p.sda1.dev/3/d330ceaf4802758135a91b575d7ce387/)

使用 修改DNS 模板

![](https://p.sda1.dev/3/80b089fe203503ea078c8bc5aa8a55bc/)

默认权限为Edit不需要动 \
特定Zone可以使用Specific Zone然后在后面的选项中提供希望修改的域名，或者直接选择All Zones获得所有域名的修改权限

![](https://p.sda1.dev/3/8d9097e723e5b1fbf4a958409f2b6725/)

确认页面，直接点击创建Tokens

![](https://p.sda1.dev/3/27c23539ecf67360870168890d501b92/)

7中的圈是希望得到的第二个参数，也就是API Token的权限，如果丢失需要重复上述步骤

![](https://p.sda1.dev/3/2d6d04c66299c21ff01382eb49dc2424/)

像这样子得到了Zone ID和API Token之后，就可以运行了

    py .\example.py  example.com   f5a5e86ea16a1abd12f43a9624ed7060   72UYVeU3dgxGnXPjRxCwIckkwGcHUQQtIHkT06cN

这里的步骤不包括购买域名和把域名挂到cloudflare上的步骤，不过这些比较容易找到，不再赘述

[点击此处](readme.old.md)可以访问原有Readme，请注意不要参照旧版本的文件使用方法，是和重写的是不一样的
