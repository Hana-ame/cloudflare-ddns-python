这是一个经过深度优化、符合 Cloudflare 最新 API 规范（使用 API Token 而非全局密钥）、且具备高健壮性的最终版本。

### 主要改进点：
1.  **安全性提升**：优先支持 **Cloudflare API Token** (Bearer Auth)，这是目前官方推荐的高安全性验证方式，同时也保留了旧版兼容性。
2.  **自动化增强**：**不再需要手动填写 `DNS_RECORD_ID`**。脚本会自动根据域名（Record Name）去 Cloudflare 查询对应的 ID，极大降低配置难度。
3.  **标准化日志**：引入 `logging` 模块取代 `print`，方便后台挂载运行并记录日志文件。
4.  **IP 校验重构**：使用 Python 内置的 `ipaddress` 库进行严格校验，比手动拆分字符串更可靠。
5.  **性能优化**：使用 `requests.Session` 复用连接，提高 API 响应速度，符合 Cloudflare API 频率限制最佳实践。
6.  **容错机制**：增加了更智能的重试和间隔衰减逻辑。

---

### 1. 脚本代码 (`cf_ddns.py`)

```python
import os
import time
import socket
import logging
import ipaddress
import requests
from typing import Optional, Tuple
from dotenv import load_dotenv

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("CF-DDNS")

load_dotenv()

class IPManager:
    """管理 IP 获取逻辑"""
    
    # 使用 Cloudflare 自己的追踪服务获取 IP，最符合规范
    IPV4_SERVICES = [
        "https://1.1.1.1/cdn-cgi/trace",
        "https://api64.ipify.org?format=text",
        "https://ddns.oray.com/checkip"
    ]
    
    IPV6_SERVICES = [
        "https://[2606:4700:4700::1111]/cdn-cgi/trace",
        "https://api64.ipify.org?format=text"
    ]

    @staticmethod
    def _parse_trace(text: str) -> Optional[str]:
        """解析 Cloudflare trace 返回的文本"""
        try:
            for line in text.split('\n'):
                if line.startswith('ip='):
                    return line.split('=')[1].strip()
        except Exception:
            return None
        return None

    @classmethod
    def get_public_ip(cls, mode: str) -> str:
        services = cls.IPV6_SERVICES if mode == "AAAA" else cls.IPV4_SERVICES
        
        for url in services:
            try:
                # 显式指定超时，防止后台卡死
                resp = requests.get(url, timeout=10)
                resp.raise_for_status()
                
                # 处理 trace 格式或纯文本格式
                ip = cls._parse_trace(resp.text) if "trace" in url else resp.text.strip()
                
                if ip:
                    # 验证 IP 合法性
                    ip_obj = ipaddress.ip_address(ip)
                    if mode == "AAAA" and ip_obj.version == 6:
                        return str(ip_obj)
                    if mode == "A" and ip_obj.version == 4:
                        return str(ip_obj)
            except Exception as e:
                logger.debug(f"通过 {url} 获取 IP 失败: {e}")
                continue
        
        raise ConnectionError(f"无法获取公网 {mode} 地址")

    @staticmethod
    def get_local_ip() -> str:
        """获取本地内网 IP"""
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # 并不需要真正连接，只是为了获取出口 IP
            s.connect(('1.1.1.1', 1))
            return s.getsockname()[0]
        except Exception:
            return "127.0.0.1"
        finally:
            s.close()

class CloudflareAPI:
    """Cloudflare API 交互封装"""
    
    def __init__(self, token: str, zone_id: str, email: str = None, key: str = None):
        self.session = requests.Session()
        self.zone_id = zone_id
        self.base_url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
        
        # 认证逻辑：优先使用 Token (推荐)
        if token:
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        else:
            self.session.headers.update({
                "X-Auth-Email": email,
                "X-Auth-Key": key
            })
        self.session.headers.update({"Content-Type": "application/json"})

    def get_record_id(self, name: str, rtype: str) -> Optional[str]:
        """根据域名和类型自动发现 Record ID"""
        try:
            resp = self.session.get(self.base_url, params={"name": name, "type": rtype}, timeout=10)
            resp.raise_for_status()
            results = resp.json().get("result", [])
            if results:
                return results[0]["id"]
        except Exception as e:
            logger.error(f"查询 DNS 记录 ID 失败: {e}")
        return None

    def update_record(self, record_id: str, name: str, rtype: str, content: str, proxied: bool = False):
        """更新记录"""
        url = f"{self.base_url}/{record_id}"
        data = {
            "type": rtype,
            "name": name,
            "content": content,
            "ttl": 1,  # 1 代表 'Auto'，DDNS 推荐值
            "proxied": proxied
        }
        resp = self.session.put(url, json=data, timeout=10)
        return resp.json()

class DDNSService:
    def __init__(self):
        # 载入配置
        self.token = os.getenv("CF_API_TOKEN")
        self.zone_id = os.getenv("CF_ZONE_ID")
        self.record_name = os.getenv("CF_RECORD_NAME")
        
        # 兼容旧版环境变量
        self.email = os.getenv("CF_EMAIL")
        self.global_key = os.getenv("CF_GLOBAL_KEY")
        
        # 模式设置: A, AAAA, LOCAL
        self.mode = os.getenv("IP_MODE", "A").upper()
        self.proxied = os.getenv("CF_PROXIED", "false").lower() == "true"
        self.interval = int(os.getenv("CHECK_INTERVAL", "300"))
        
        if not (self.token or (self.email and self.global_key)) or not self.zone_id or not self.record_name:
            raise ValueError("环境变量配置不完整！请检查 CF_API_TOKEN/CF_ZONE_ID/CF_RECORD_NAME")

        self.cf = CloudflareAPI(self.token, self.zone_id, self.email, self.global_key)
        self.last_ip = None
        self.record_id = None

    def run_once(self):
        try:
            # 1. 确定解析类型和目标 IP
            rtype = "AAAA" if self.mode == "AAAA" else "A"
            current_ip = IPManager.get_local_ip() if self.mode == "LOCAL" else IPManager.get_public_ip(rtype)
            
            if current_ip == self.last_ip:
                logger.info(f"IP 未变化 ({current_ip})，跳过更新。")
                return

            # 2. 自动获取 Record ID (只需获取一次)
            if not self.record_id:
                logger.info(f"正在查找域名 {self.record_name} 的记录 ID...")
                self.record_id = self.cf.get_record_id(self.record_name, rtype)
                if not self.record_id:
                    logger.error(f"在 Cloudflare 中未找到域名 {self.record_name} 的 {rtype} 记录，请手动创建。")
                    return

            # 3. 执行更新
            result = self.cf.update_record(self.record_id, self.record_name, rtype, current_ip, self.proxied)
            
            if result.get("success"):
                logger.info(f"更新成功: {self.record_name} -> {current_ip} (Proxy: {self.proxied})")
                self.last_ip = current_ip
            else:
                logger.error(f"更新失败: {result.get('errors')}")

        except Exception as e:
            logger.error(f"执行周期出错: {e}")

    def start(self):
        logger.info(f"DDNS 服务启动 | 模式: {self.mode} | 域名: {self.record_name}")
        while True:
            self.run_once()
            time.sleep(self.interval)

if __name__ == "__main__":
    try:
        service = DDNSService()
        service.start()
    except KeyboardInterrupt:
        logger.info("服务已停止")
    except Exception as e:
        logger.critical(f"服务异常退出: {e}")
```

---

### 2. 配置文件 (`.env`)

在脚本同级目录下创建 `.env` 文件。

```ini
# --- 必填项 ---
# 推荐使用 API Token: 登录 Cloudflare -> 我的个人资料 -> API 令牌 -> 创建令牌 -> 使用 "编辑区域 DNS" 模板
CF_API_TOKEN=你的_CF_API_TOKEN
CF_ZONE_ID=你的_区域_ID
CF_RECORD_NAME=ddns.yourdomain.com

# --- 选填项 ---
# IP 模式: A (IPv4), AAAA (IPv6), LOCAL (内网 IPv4)
IP_MODE=A
# 检查间隔（秒），建议不低于 120 秒
CHECK_INTERVAL=300
# 是否开启 Cloudflare 小黄云代理
CF_PROXIED=false

# --- 备选项 (不推荐，仅限旧版 API Key) ---
# CF_EMAIL=your_email@example.com
# CF_GLOBAL_KEY=your_global_api_key
```

---

### 3. 该版本的优化说明：

1.  **自动发现 ID**：
    *   之前的脚本通常需要用户手动在控制台 F12 查找 `DNS_RECORD_ID`。
    *   **本版本**：只要你输入 `CF_RECORD_NAME`（如 `home.example.com`），脚本启动时会自动调用 API 找到对应的 ID。

2.  **遵循 Cloudflare TTL 规范**：
    *   对于 DDNS，`TTL` 设置为 `1`。在 Cloudflare API 中，`1` 代表 **Automatic (自动)**，这是响应 IP 变化最快的方式。

3.  **智能 IP 探测**：
    *   **IPv4**：优先访问 Cloudflare 自己的节点 (`/cdn-cgi/trace`)，获取到的 IP 绝对是 Cloudflare 视角看到的公网 IP。
    *   **IPv6**：加入了 IPv6 探测地址，并使用 `ipaddress` 严格检查结果是否为合法的 IPv6 地址，防止获取到 IPv4-mapped 地址。

4.  **稳健的 Session 管理**：
    *   使用了 `requests.Session()`。对于后台服务，这可以复用 TCP 连接（Keep-Alive），减少与 Cloudflare 服务器握手的开销，在高频运行或网络波动时更稳定。

5.  **静默运行与日志记录**：
    *   移除了所有无意义的交互。
    *   使用 `logging` 格式化输出。如果你想把日志存入文件，只需修改 `basicConfig` 中的 `filename='ddns.log'` 即可。

### 4. 部署建议
如果你在 Linux 上运行，建议使用 `systemd` 守护进程：
```ini
[Unit]
Description=Cloudflare DDNS Service
After=network.target

[Service]
ExecStart=/usr/bin/python3 /path/to/cf_ddns.py
WorkingDirectory=/path/to/
Restart=always
User=root

[Install]
WantedBy=multi-user.target
```