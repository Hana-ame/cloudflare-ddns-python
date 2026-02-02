# Author: Gemini 3 flash

import os
import time
import socket
import logging
import ipaddress
import requests
from dotenv import load_dotenv

# 配置日志：生产环境建议级别为 INFO
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("CF-DDNS-Smart")

load_dotenv()

class IPManager:
    """智能 IP 获取器"""
    IPV4_SERVICES = ["https://1.1.1.1/cdn-cgi/trace", "https://api64.ipify.org?format=text"]
    IPV6_SERVICES = ["https://[2606:4700:4700::1111]/cdn-cgi/trace", "https://api64.ipify.org?format=text"]

    @classmethod
    def get_ip(cls, mode: str) -> str:
        if mode == "LOCAL":
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                s.connect(('1.1.1.1', 1))
                return s.getsockname()[0]
            except Exception: return "127.0.0.1"
            finally: s.close()

        rtype = "AAAA" if mode == "AAAA" else "A"
        services = cls.IPV6_SERVICES if rtype == "AAAA" else cls.IPV4_SERVICES
        
        for url in services:
            try:
                resp = requests.get(url, timeout=10)
                resp.raise_for_status()
                # 解析 trace 或纯文本
                content = resp.text
                ip = next((line.split('=')[1] for line in content.split('\n') if line.startswith('ip=')), content.strip())
                # 校验格式
                ip_obj = ipaddress.ip_address(ip)
                if (rtype == "A" and ip_obj.version == 4) or (rtype == "AAAA" and ip_obj.version == 6):
                    return str(ip_obj)
            except Exception: continue
        raise ConnectionError(f"无法获取公网 {rtype} 地址")

class CloudflareSmartAPI:
    """具备自愈功能的 Cloudflare API 封装"""
    def __init__(self, token: str | None, zone_id: str, email: str | None = None, key: str | None = None):
        self.session = requests.Session()
        self.zone_id = zone_id
        self.base_url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
        
        # 直接通过赋值来设置 header，避免 update() 的多重载类型歧义
        self.session.headers["Content-Type"] = "application/json"

        if token:
            self.session.headers["Authorization"] = f"Bearer {token}"
        elif email and key:
            self.session.headers["X-Auth-Email"] = email
            self.session.headers["X-Auth-Key"] = key
        else:
            raise ValueError("必须提供 CF_API_TOKEN 或 (CF_EMAIL 和 CF_GLOBAL_KEY)")

    def sync_dns(self, name, rtype, content, proxied):
        """核心逻辑：确保 Cloudflare 中有且仅有一条匹配的记录"""
        try:
            # 1. 查询现有记录
            resp = self.session.get(self.base_url, params={"name": name, "type": rtype}, timeout=10)
            resp.raise_for_status()
            records = resp.json().get("result", [])

            if not records:
                # 场景：记录不存在 -> 创建
                logger.info(f"未发现记录，正在自动创建: {name} ({rtype}) -> {content}")
                self._create_record(name, rtype, content, proxied)
                return True

            # 场景：存在记录
            target_record = records[0]
            record_id = target_record["id"]
            existing_ip = target_record["content"]
            existing_proxied = target_record["proxied"]

            # 2. 如果存在多个记录，清理冗余记录（去重）
            if len(records) > 1:
                logger.warning(f"检测到 {len(records)} 条冗余记录，正在自动清理...")
                for extra in records[1:]:
                    self._delete_record(extra["id"])

            # 3. 检查是否需要更新内容或代理状态
            if existing_ip != content or existing_proxied != proxied:
                logger.info(f"记录需要更新: {existing_ip} -> {content} (Proxy: {proxied})")
                self._update_record(record_id, name, rtype, content, proxied)
            else:
                logger.info(f"配置未变化，保持现状: {content}")
            
            return True
        except Exception as e:
            logger.error(f"同步过程中发生异常: {e}")
            return False

    def _create_record(self, name, rtype, content, proxied):
        data = {"type": rtype, "name": name, "content": content, "ttl": 1, "proxied": proxied}
        r = self.session.post(self.base_url, json=data, timeout=10)
        r.raise_for_status()
        logger.info("记录创建成功")

    def _update_record(self, record_id, name, rtype, content, proxied):
        url = f"{self.base_url}/{record_id}"
        data = {"type": rtype, "name": name, "content": content, "ttl": 1, "proxied": proxied}
        r = self.session.put(url, json=data, timeout=10)
        r.raise_for_status()
        logger.info("记录更新成功")

    def _delete_record(self, record_id):
        url = f"{self.base_url}/{record_id}"
        self.session.delete(url, timeout=10)
        logger.debug(f"已删除冗余记录 ID: {record_id}")

class DDNSService:
    def __init__(self):
        self.token = os.getenv("CF_API_TOKEN")
        self.zone_id = os.getenv("CF_ZONE_ID")
        self.record_name = os.getenv("CF_RECORD_NAME")
        self.mode = os.getenv("IP_MODE", "A").upper()
        self.proxied = os.getenv("CF_PROXIED", "false").lower() == "true"
        self.interval = int(os.getenv("CHECK_INTERVAL", "300"))
        
        # 兼容旧 API Key 模式
        self.email = os.getenv("CF_EMAIL")
        self.global_key = os.getenv("CF_GLOBAL_KEY")

        if not (self.token or (self.email and self.global_key)) or not self.zone_id:
            raise ValueError("配置不足，请检查环境变量。")

        self.api = CloudflareSmartAPI(self.token, self.zone_id, self.email, self.global_key)
        self.last_sync_ip = None

    def tick(self):
        try:
            current_ip = IPManager.get_ip(self.mode)
            rtype = "AAAA" if self.mode == "AAAA" else "A"
            
            # 为了处理代理状态变化或被手动误删的情况，这里不完全依赖 last_sync_ip
            # 但为了减少 API 调用，如果 IP 没变，可以延长检查
            success = self.api.sync_dns(self.record_name, rtype, current_ip, self.proxied)
            if success:
                self.last_sync_ip = current_ip
        except Exception as e:
            logger.error(f"执行失败: {e}")

    def start(self):
        logger.info(f"DDNS 服务启动: {self.record_name} (模式: {self.mode})")
        while True:
            self.tick()
            time.sleep(self.interval)

if __name__ == "__main__":
    try:
        DDNSService().start()
    except KeyboardInterrupt:
        logger.info("退出服务")