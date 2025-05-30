import aiohttp
import asyncio
from typing import Optional, Dict, List
from loguru import logger
import os
from datetime import datetime, timedelta

class ProxyManager:
    def __init__(self, proxy_file: str = None, proxy_type: str = "http", check_timeout: int = 10):
        """
        初始化代理管理器
        
        Args:
            proxy_file: 代理文件路径（可选）
            proxy_type: 代理类型，默认为http
            check_timeout: 代理检测超时时间，默认10秒
        """
        self.proxy_type = proxy_type
        self.check_timeout = check_timeout
        self.proxies: List[Dict] = []
        self.current_proxy: Optional[Dict] = None
        self.last_rotation: datetime = datetime.now()
        self.proxy_file = proxy_file
        
        # 从代理文件加载代理列表
        if proxy_file and os.path.exists(proxy_file):
            self._load_proxies_from_file(proxy_file)
        
        # 如果没有代理，添加默认测试代理
        if not self.proxies:
            self.add_default_proxy()
        
    def _load_proxies_from_file(self, proxy_file: str):
        """从文件加载代理列表"""
        try:
            with open(proxy_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        self._parse_and_add_proxy(line)
            logger.info(f"从 {proxy_file} 加载了 {len(self.proxies)} 个代理")
        except Exception as e:
            logger.error(f"加载代理文件失败: {str(e)}")
    
    def _parse_and_add_proxy(self, proxy_line: str):
        """解析代理字符串并添加到列表"""
        try:
            # 支持格式: http://ip:port, http://user:pass@ip:port, ip:port
            if '://' in proxy_line:
                # 完整URL格式
                if '@' in proxy_line:
                    # 带认证的代理
                    protocol, rest = proxy_line.split('://', 1)
                    auth_part, host_port = rest.split('@', 1)
                    username, password = auth_part.split(':', 1)
                    host, port = host_port.split(':', 1)
                else:
                    # 不带认证的代理
                    protocol, host_port = proxy_line.split('://', 1)
                    host, port = host_port.split(':', 1)
                    username, password = None, None
            else:
                # 简单格式 ip:port
                host, port = proxy_line.split(':', 1)
                username, password = None, None
            
            self.add_proxy(host, int(port), username, password)
            
        except Exception as e:
            logger.error(f"解析代理字符串失败: {proxy_line}, 错误: {str(e)}")
    
    async def check_proxy(self, proxy: Dict) -> bool:
        """检查代理是否可用"""
        try:
            proxy_url = self._build_proxy_url(proxy)
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    'https://api.ipify.org?format=json',
                    proxy=proxy_url,
                    timeout=aiohttp.ClientTimeout(total=self.check_timeout)
                ) as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"代理检测失败: {str(e)}")
            return False
    
    def _build_proxy_url(self, proxy: Dict) -> str:
        """构建代理URL"""
        auth = f"{proxy['username']}:{proxy['password']}@" if proxy.get('username') else ""
        return f"{self.proxy_type}://{auth}{proxy['host']}:{proxy['port']}"
    
    async def rotate_proxy(self, rotation_interval: int = 300) -> Optional[Dict]:
        """
        轮换代理
        
        Args:
            rotation_interval: 轮换间隔时间（秒），默认300秒
        """
        if not self.proxies:
            logger.warning("没有可用的代理")
            return None
            
        current_time = datetime.now()
        
        if (current_time - self.last_rotation).seconds < rotation_interval:
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
            
        return self._build_proxy_url(self.current_proxy)
    
    def get_proxy_list(self) -> List[str]:
        """获取代理URL列表，用于兼容其他组件"""
        proxy_urls = []
        for proxy in self.proxies:
            proxy_urls.append(self._build_proxy_url(proxy))
        return proxy_urls
    
    def get_stats(self) -> Dict:
        """获取代理统计信息"""
        return {
            'total_proxies': len(self.proxies),
            'current_proxy': self.current_proxy,
            'proxy_type': self.proxy_type,
            'last_rotation': self.last_rotation.isoformat() if self.last_rotation else None
        } 