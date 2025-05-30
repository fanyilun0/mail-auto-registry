import aiohttp
import asyncio
from typing import Optional, Dict, List
from loguru import logger
import yaml
import os
from datetime import datetime, timedelta

class ProxyManager:
    def __init__(self, config_path: str = "config.yaml"):
        self.config = self._load_config(config_path)
        self.proxies: List[Dict] = []
        self.current_proxy: Optional[Dict] = None
        self.last_rotation: datetime = datetime.now()
        
        # 添加默认测试代理
        self.add_default_proxy()
        
    def _load_config(self, config_path: str) -> dict:
        """加载配置文件"""
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)['proxy']
    
    async def check_proxy(self, proxy: Dict) -> bool:
        """检查代理是否可用"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    'https://api.ipify.org?format=json',
                    proxy=f"{self.config['type']}://{proxy['host']}:{proxy['port']}",
                    timeout=self.config['check_timeout']
                ) as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"代理检测失败: {str(e)}")
            return False
    
    async def rotate_proxy(self) -> Optional[Dict]:
        """轮换代理"""
        if not self.proxies:
            logger.warning("没有可用的代理")
            return None
            
        current_time = datetime.now()
        if (current_time - self.last_rotation).seconds < self.config['rotation_interval']:
            return self.current_proxy
            
        for proxy in self.proxies:
            if await self.check_proxy(proxy):
                self.current_proxy = proxy
                self.last_rotation = current_time
                logger.info(f"切换到新代理: {proxy['host']}:{proxy['port']}")
                return proxy
                
        logger.error("所有代理均不可用")
        return None
    
    def get_current_proxy(self) -> Optional[Dict]:
        """获取当前代理"""
        return self.current_proxy
    
    def add_proxy(self, host: str, port: int, username: str = None, password: str = None):
        """添加新代理"""
        proxy = {
            'host': host,
            'port': port,
            'username': username,
            'password': password
        }
        self.proxies.append(proxy)
        logger.info(f"添加新代理: {host}:{port}")
    
    def remove_proxy(self, host: str, port: int):
        """移除代理"""
        self.proxies = [p for p in self.proxies if not (p['host'] == host and p['port'] == port)]
        logger.info(f"移除代理: {host}:{port}")
    
    def add_default_proxy(self):
        """添加默认测试代理"""
        # 根据step-by-step-verification.md的要求，默认使用http://127.0.0.1:7890
        default_proxy = {
            'host': '127.0.0.1',
            'port': 7890,
            'username': None,
            'password': None
        }
        self.proxies.append(default_proxy)
        self.current_proxy = default_proxy
        logger.info("已添加默认代理: http://127.0.0.1:7890")
    
    def get_proxy_url(self) -> Optional[str]:
        """获取当前代理的URL格式"""
        if not self.current_proxy:
            return None
            
        proxy = self.current_proxy
        auth = f"{proxy['username']}:{proxy['password']}@" if proxy.get('username') else ""
        return f"{self.config['type']}://{auth}{proxy['host']}:{proxy['port']}" 