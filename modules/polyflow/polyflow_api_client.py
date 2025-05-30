import asyncio
import aiohttp
import os
import json
import random
import time
from datetime import datetime, timezone, timedelta
from loguru import logger
from typing import Optional, Dict, List, Any
import ssl
import pytz
from pathlib import Path

# 导入配置加载器
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from utils.config_loader import ConfigLoader

from gmail.email_handler import EmailHandler

class PolyflowAPIClient:
    """Polyflow API客户端，用于通过API进行自动注册"""
    
    def __init__(self, email_handler, proxy_list: List[str] = None, config_manager=None):
        self.email_handler = email_handler
        self.base_url = "https://api-v2.polyflow.tech"
        self.session = None
        self.proxy_list = proxy_list or []
        self.current_proxy = None
        self.config_manager = config_manager
        
        # 加载配置
        self._load_config()
        
        # 真实浏览器User-Agent列表
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
    def _load_config(self):
        """加载配置文件"""
        try:
            # 获取项目根目录的配置文件路径
            current_dir = Path(__file__).parent.parent.parent
            config_path = current_dir / "config.yaml"
            
            if config_path.exists():
                config_loader = ConfigLoader(config_path)
                self.timezone_config = config_loader.get_timezone_config()
                logger.info(f"配置加载成功: 时区 {self.timezone_config['local_timezone']}")
            else:
                # 使用默认配置
                self.timezone_config = {
                    'local_timezone': 'Asia/Shanghai',
                    'utc_offset_hours': 8
                }
                logger.warning(f"配置文件不存在，使用默认时区配置: {self.timezone_config['local_timezone']}")
        except Exception as e:
            # 使用默认配置
            self.timezone_config = {
                'local_timezone': 'Asia/Shanghai',
                'utc_offset_hours': 8
            }
            logger.warning(f"加载配置失败，使用默认时区配置: {str(e)}")
    
    def _get_local_timezone(self):
        """获取本地时区对象"""
        try:
            return pytz.timezone(self.timezone_config['local_timezone'])
        except Exception as e:
            logger.warning(f"获取时区失败，使用默认时区: {str(e)}")
            return pytz.timezone('Asia/Shanghai')
    
    def _get_random_headers(self) -> Dict[str, str]:
        """生成随机的真实浏览器请求头"""
        user_agent = random.choice(self.user_agents)
        
        headers = {
            'User-Agent': user_agent,
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Content-Type': 'application/json',
            'Origin': 'https://app.polyflow.tech',
            'Referer': 'https://app.polyflow.tech/',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Connection': 'keep-alive',
            'DNT': '1'
        }
        
        # 随机添加一些可选的请求头
        optional_headers = {
            'X-Requested-With': 'XMLHttpRequest',
            'Upgrade-Insecure-Requests': '1',
            'Sec-GPC': '1'
        }
        
        # 随机选择添加一些可选请求头
        for key, value in optional_headers.items():
            if random.random() > 0.5:
                headers[key] = value
                
        return headers
    
    def _get_random_proxy(self) -> Optional[str]:
        """获取随机代理"""
        if not self.proxy_list:
            return None
        return random.choice(self.proxy_list)
    
    @staticmethod
    def load_email_list(email_file_path: str = None) -> List[str]:
        """从email.txt文件加载邮箱地址列表"""
        # 自动检测执行路径并调整文件路径
        if email_file_path is None:
            # 检查当前工作目录
            current_dir = os.getcwd()
            if current_dir.endswith('/src'):
                # 在src目录下执行
                email_file_path = "polyflow/email.txt"
            else:
                # 在项目根目录执行
                email_file_path = "src/polyflow/email.txt"
        
        emails = []
        try:
            with open(email_file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # 跳过空行和注释行
                    if line and not line.startswith('#'):
                        emails.append(line)
            logger.info(f"从 {email_file_path} 加载了 {len(emails)} 个邮箱地址")
        except FileNotFoundError:
            logger.error(f"邮箱配置文件 {email_file_path} 不存在")
        except Exception as e:
            logger.error(f"读取邮箱配置文件时发生错误: {str(e)}")
        
        return emails
    
    @staticmethod
    def load_proxy_list(proxy_file_path: str = None) -> List[str]:
        """从文件加载代理列表"""
        # 自动检测执行路径并调整文件路径
        if proxy_file_path is None:
            current_dir = os.getcwd()
            if current_dir.endswith('/src'):
                proxy_file_path = "polyflow/proxies.txt"
            else:
                proxy_file_path = "src/polyflow/proxies.txt"
        
        proxies = []
        try:
            if os.path.exists(proxy_file_path):
                with open(proxy_file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            # 支持格式: http://ip:port 或 ip:port
                            if not line.startswith('http'):
                                line = f"http://{line}"
                            proxies.append(line)
                logger.info(f"从 {proxy_file_path} 加载了 {len(proxies)} 个代理")
            else:
                logger.info(f"代理文件 {proxy_file_path} 不存在，将不使用代理")
        except Exception as e:
            logger.error(f"读取代理文件时发生错误: {str(e)}")
        
        return proxies
        
    async def __aenter__(self):
        """异步上下文管理器入口"""
        # 加载代理列表
        if not self.proxy_list:
            self.proxy_list = self.load_proxy_list()
        
        # 选择代理
        self.current_proxy = self._get_random_proxy()
        if self.current_proxy:
            logger.info(f"使用代理: {self.current_proxy}")
        
        # 创建SSL上下文，允许不安全的连接
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        # 创建连接器
        connector = aiohttp.TCPConnector(
            ssl=ssl_context,
            limit=100,
            limit_per_host=30,
            ttl_dns_cache=300,
            use_dns_cache=True,
        )
        
        # 创建会话，代理在请求时设置
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=aiohttp.ClientTimeout(total=60, connect=30),
            headers=self._get_random_headers(),
            cookie_jar=aiohttp.CookieJar()
        )
        
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        if self.session:
            await self.session.close()
    
    async def _make_request_with_retry(self, method: str, url: str, **kwargs) -> Dict[str, any]:
        """带重试机制的请求方法"""
        max_retries = 3
        base_delay = 2
        
        for attempt in range(max_retries):
            try:
                # 随机延迟，模拟人类行为
                if attempt > 0:
                    delay = base_delay * (2 ** attempt) + random.uniform(1, 3)
                    logger.info(f"第 {attempt + 1} 次重试，等待 {delay:.1f} 秒...")
                    await asyncio.sleep(delay)
                    
                    # 更换代理和请求头
                    if self.proxy_list and len(self.proxy_list) > 1:
                        old_proxy = self.current_proxy
                        self.current_proxy = self._get_random_proxy()
                        if self.current_proxy != old_proxy:
                            logger.info(f"更换代理: {self.current_proxy}")
                    
                    # 更新请求头
                    new_headers = self._get_random_headers()
                    for key, value in new_headers.items():
                        self.session.headers[key] = value
                
                # 添加随机延迟模拟人类行为
                await asyncio.sleep(random.uniform(0.5, 2.0))
                
                logger.info(f"发送请求到: {url}")
                
                # 设置代理（如果有的话）
                request_kwargs = kwargs.copy()
                if self.current_proxy:
                    request_kwargs['proxy'] = self.current_proxy
                
                async with self.session.request(method, url, **request_kwargs) as response:
                    
                    # 记录响应信息
                    logger.info(f"响应状态码: {response.status}")
                    logger.info(f"响应头: {dict(response.headers)}")
                    
                    # 尝试解析响应
                    content_type = response.headers.get('content-type', '').lower()
                    
                    if 'application/json' in content_type:
                        response_data = await response.json()
                    elif 'text/' in content_type:
                        text_content = await response.text()
                        logger.warning(f"收到文本响应而非JSON: {text_content[:500]}...")
                        
                        # 尝试解析为JSON（有些API返回text/plain但内容是JSON）
                        try:
                            response_data = json.loads(text_content)
                            logger.info("成功将文本内容解析为JSON")
                        except json.JSONDecodeError:
                            # 如果不是JSON，进行错误分析
                            if response.status == 403:
                                if 'cloudflare' in text_content.lower():
                                    return {"success": False, "error": "Cloudflare防护拦截", "status_code": response.status}
                                elif 'access denied' in text_content.lower():
                                    return {"success": False, "error": "访问被拒绝", "status_code": response.status}
                                else:
                                    return {"success": False, "error": "403 Forbidden - 可能需要更多反爬虫措施", "status_code": response.status}
                            
                            response_data = {"error": "非JSON响应", "content": text_content[:1000]}
                    else:
                        response_data = {"error": "未知内容类型", "content_type": content_type}
                    
                    if response.status == 200:
                        return {"success": True, "data": response_data, "status_code": response.status}
                    else:
                        return {"success": False, "error": response_data, "status_code": response.status}
                        
            except aiohttp.ClientError as e:
                logger.error(f"请求异常 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
                if attempt == max_retries - 1:
                    return {"success": False, "error": f"网络请求失败: {str(e)}"}
            except Exception as e:
                logger.error(f"未知异常 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
                if attempt == max_retries - 1:
                    return {"success": False, "error": f"请求异常: {str(e)}"}
        
        return {"success": False, "error": "所有重试都失败了"}
    
    async def send_verification_code(self, email: str) -> Dict[str, any]:
        """发送验证码到邮箱"""
        url = f"{self.base_url}/api/account/email/send"
        payload = {
            "email": email,
            "type": "login"
        }
        
        logger.info(f"正在向 {email} 发送验证码...")
        result = await self._make_request_with_retry('POST', url, json=payload)
        
        if result["success"]:
            logger.info(f"验证码发送成功: {email}")
        else:
            logger.error(f"验证码发送失败: {email}, 错误: {result['error']}")
            
        return result
    
    async def login_with_code(self, email: str, code: str, referral_code: str = "") -> Dict[str, any]:
        """使用验证码登录"""
        url = f"{self.base_url}/api/account/email/login"
        payload = {
            "email": email,
            "code": code,
            "referral_code": referral_code
        }
        
        logger.info(f"正在使用验证码登录: {email}")
        result = await self._make_request_with_retry('POST', url, json=payload)
        
        if result["success"]:
            logger.info(f"登录成功: {email}")
        else:
            logger.error(f"登录失败: {email}, 错误: {result['error']}")
            
        return result
    
    async def get_verification_code_async(self, timeout: int = 120) -> Optional[str]:
        """异步获取验证码"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            self.email_handler.get_latest_verification_code,
            timeout
        )
    
    def save_token_data(self, email: str, token_data: Dict, tokens_file_path: str = None):
        """保存token数据到文件"""
        try:
            # 使用配置管理器获取保存路径
            if tokens_file_path is None:
                if self.config_manager:
                    tokens_file_path = self.config_manager.get_tokens_file_path()
                else:
                    # 兼容旧的路径检测方式
                    current_dir = os.getcwd()
                    if current_dir.endswith('/src'):
                        tokens_file_path = "../data/polyflow_tokens.txt"
                    else:
                        tokens_file_path = "data/polyflow_tokens.txt"
            
            # 确保目录存在
            os.makedirs(os.path.dirname(tokens_file_path), exist_ok=True)
            
            # 提取token信息
            msg = token_data.get("msg", {})
            token = msg.get("token", "")
            expiry_timestamp = msg.get("expiry", 0)
            
            # 转换时间戳为可读时间
            if expiry_timestamp:
                expiry_time = datetime.fromtimestamp(expiry_timestamp, tz=timezone.utc)
                expiry_str = expiry_time.strftime("%Y-%m-%d %H:%M:%S UTC")
            else:
                expiry_str = "Unknown"
            
            # 构建数据行：email|token|expire
            data_line = f"{email}|{token}|{expiry_str}\n"
            
            # 检查文件是否存在，如果不存在则添加表头
            file_exists = os.path.exists(tokens_file_path)
            
            # 以追加模式写入文件
            with open(tokens_file_path, 'a', encoding='utf-8') as f:
                if not file_exists:
                    # 添加表头
                    f.write("# Polyflow Token数据\n")
                    f.write("# 格式: email|token|expire\n")
                    f.write(f"# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("\n")
                f.write(data_line)
                
            logger.info(f"✅ Token数据已保存到: {tokens_file_path}")
            logger.info(f"📧 邮箱: {email}")
            logger.info(f"🔑 Token: {token[:50]}...")
            logger.info(f"⏰ 过期时间: {expiry_str}")
            
            # 同时保存详细的JSON格式数据用于备份
            self._save_detailed_token_data(email, token_data)
            
        except Exception as e:
            logger.error(f"保存token数据时发生错误: {str(e)}")
    
    def _save_detailed_token_data(self, email: str, token_data: Dict):
        """保存详细的token数据到JSON文件"""
        try:
            # 使用配置管理器获取保存路径
            if self.config_manager:
                detail_dir = self.config_manager.get_tokens_detail_dir_path()
            else:
                # 兼容旧的路径检测方式
                current_dir = os.getcwd()
                if current_dir.endswith('/src'):
                    detail_dir = "../data/polyflow_tokens_detailed"
                else:
                    detail_dir = "data/polyflow_tokens_detailed"
            
            os.makedirs(detail_dir, exist_ok=True)
            
            detailed_data = {
                'email': email,
                'token_data': token_data,
                'timestamp': datetime.now().isoformat(),
                'site': 'polyflow.tech',
                'registration_success': True
            }
            
            # 使用安全的文件名
            safe_email = email.replace('@', '_').replace('.', '_')
            filename = f"{detail_dir}/{safe_email}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(detailed_data, f, indent=2, ensure_ascii=False)
                
            logger.info(f"📄 详细token数据已保存到: {filename}")
            
        except Exception as e:
            logger.error(f"保存详细token数据时发生错误: {str(e)}")
    
    async def register_account(self, email: str, referral_code: str = "") -> Dict[str, any]:
        """
        注册单个账号的完整流程
        
        Args:
            email: 邮箱地址
            referral_code: 推荐码（可选）
            
        Returns:
            注册结果字典
        """
        result = {
            'success': False,
            'email': email,
            'token': None,
            'error': None,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # 确保邮件处理器已连接
            if not self.email_handler.imap:
                self.email_handler.connect()
            
            # 重要：完全清除之前的验证码记录和状态，避免获取到其他邮箱的验证码
            self.email_handler.clear_used_codes()
            logger.info(f"🔄 开始处理邮箱: {email}")
            logger.info(f"🧹 已清理验证码缓存，确保获取正确的验证码")
            
            # 记录发送验证码前的精确时间戳，用于严格过滤旧邮件
            send_time = datetime.now()
            logger.info(f"📅 记录发送时间: {send_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 步骤1: 发送验证码
            logger.info(f"📧 步骤1: 向 {email} 发送验证码...")
            send_result = await self.send_verification_code(email)
            if not send_result["success"]:
                result['error'] = f"发送验证码失败: {send_result['error']}"
                logger.error(f"❌ {email} - {result['error']}")
                return result
            
            # 检查API响应是否为预期的成功格式
            api_response = send_result.get("data", {})
            if not (api_response.get("success") == True and "msg" in api_response):
                result['error'] = f"API响应格式异常: {api_response}"
                logger.error(f"❌ {email} - {result['error']}")
                return result
            
            logger.info(f"✅ {email} - 验证码发送成功")
            
            # 步骤2: 等待邮件到达（增加等待时间，避免读取到旧邮件）
            logger.info(f"⏳ 步骤2: 等待验证码邮件到达...")
            logger.info(f"💤 等待15秒确保新邮件到达，避免读取旧验证码...")
            await asyncio.sleep(15)  # 增加等待时间到15秒
            
            # 步骤3: 获取验证码（使用发送时间过滤，确保获取最新验证码）
            logger.info(f"🔍 步骤3: 从邮箱读取验证码...")
            
            # 使用发送时间作为严格过滤条件，确保获取正确的验证码
            verification_code = await self.get_verification_code_for_email(email, timeout=180, send_time=send_time)
            if not verification_code:
                result['error'] = "未能获取到验证码，请检查邮箱设置或网络连接"
                logger.error(f"❌ {email} - {result['error']}")
                return result
            
            logger.info(f"✅ {email} - 成功获取验证码: {verification_code}")
            
            # 步骤4: 使用验证码登录
            logger.info(f"🔐 步骤4: 使用验证码登录...")
            login_result = await self.login_with_code(email, verification_code, referral_code)
            if not login_result["success"]:
                result['error'] = f"登录失败: {login_result['error']}"
                logger.error(f"❌ {email} - {result['error']}")
                return result
            
            # 步骤5: 处理登录响应
            response_data = login_result["data"]
            if response_data.get("success") and "msg" in response_data:
                msg = response_data["msg"]
                token = msg.get("token")
                
                if token:
                    result['success'] = True
                    result['token'] = token
                    
                    # 保存token数据
                    self.save_token_data(email, response_data)
                    
                    logger.info(f"🎉 {email} - 账号注册成功!")
                    logger.info(f"🔑 Token: {token[:50]}...")
                else:
                    result['error'] = "响应中未找到token"
                    logger.error(f"❌ {email} - {result['error']}")
            else:
                result['error'] = f"登录响应异常: {response_data}"
                logger.error(f"❌ {email} - {result['error']}")
                
        except Exception as e:
            logger.error(f"❌ {email} - 注册过程发生错误: {str(e)}")
            result['error'] = str(e)
            
        finally:
            # 确保每个邮箱处理完成后彻底清理状态
            if hasattr(self, 'email_handler') and self.email_handler:
                self.email_handler.clear_used_codes()
                logger.info(f"🧹 {email} - 处理完成，已清理验证码缓存")
            
        return result
    
    async def get_verification_code_for_email(self, email: str, timeout: int = 180, send_time: datetime = None) -> Optional[str]:
        """
        为特定邮箱获取验证码，避免验证码冲突
        
        Args:
            email: 目标邮箱地址
            timeout: 超时时间（秒）
            send_time: 发送验证码的时间，用于过滤旧邮件
            
        Returns:
            验证码字符串，如果获取失败返回None
        """
        logger.info(f"🔍 开始为 {email} 获取验证码，超时时间: {timeout}秒")
        if send_time:
            logger.info(f"📅 只获取 {send_time.strftime('%Y-%m-%d %H:%M:%S')} 之后的邮件")
        
        start_time = time.time()
        last_email_count = 0
        retry_count = 0
        max_retries = int(timeout / 5)  # 每5秒重试一次
        
        # 获取本地时区
        local_tz = self._get_local_timezone()
        
        while time.time() - start_time < timeout:
            try:
                retry_count += 1
                logger.info(f"🔄 第 {retry_count}/{max_retries} 次尝试获取验证码...")
                
                # 刷新邮箱连接，确保获取最新邮件
                if retry_count > 1:
                    try:
                        logger.info("🔄 刷新邮箱连接以获取最新邮件...")
                        self.email_handler.imap.select('INBOX')  # 重新选择收件箱
                    except Exception as e:
                        logger.warning(f"刷新邮箱连接失败: {str(e)}")
                
                # 动态调整搜索时间范围
                search_minutes = min(10, max(5, int((time.time() - start_time) / 60) + 5))
                logger.info(f"📧 搜索最近 {search_minutes} 分钟的邮件...")
                
                # 搜索来自polyflow的最近邮件
                email_ids = self.email_handler._search_recent_emails(
                    sender_filter="polyflow",
                    minutes=search_minutes
                )
                
                if len(email_ids) != last_email_count:
                    logger.info(f"📬 发现 {len(email_ids)} 封来自polyflow的邮件 (上次: {last_email_count})")
                    last_email_count = len(email_ids)
                else:
                    logger.info(f"📬 邮件数量无变化: {len(email_ids)} 封")
                
                # 处理最新的邮件（增加检查数量）
                found_new_email = False
                valid_codes_found = []  # 记录找到的有效验证码
                
                for email_id in email_ids[:10]:  # 检查最新的10封邮件
                    email_data = self.email_handler._get_email_content_with_timestamp(email_id)
                    if email_data and email_data['content']:
                        # 严格的时间过滤 - 必须有发送时间才进行处理
                        if send_time and email_data['timestamp']:
                            # 确保邮件时间在发送验证码之后
                            email_time = email_data['timestamp']
                            
                            # 处理时区问题，统一转换为本地时间
                            if email_time.tzinfo:
                                # 如果邮件时间有时区信息，转换为本地时间
                                email_time_local = email_time.astimezone(local_tz).replace(tzinfo=None)
                            else:
                                # 如果没有时区信息，假设是UTC时间，转换为本地时间
                                email_time_local = email_time + timedelta(hours=self.timezone_config['utc_offset_hours'])
                            
                            # 严格的时间过滤：邮件时间必须在发送时间之后（允许30秒容差）
                            time_diff = (email_time_local - send_time).total_seconds()
                            
                            if time_diff < -30:  # 邮件时间比发送时间早30秒以上，跳过
                                logger.debug(f"⏭️ 跳过旧邮件: {email_data['subject']} (时差: {time_diff:.1f}秒)")
                                continue
                            elif time_diff > 300:  # 邮件时间比发送时间晚5分钟以上，可能是其他请求的邮件
                                logger.debug(f"⏭️ 跳过过新邮件: {email_data['subject']} (时差: {time_diff:.1f}秒)")
                                continue
                            else:
                                logger.info(f"📧 检查符合时间条件的邮件: {email_data['subject']} (时差: {time_diff:.1f}秒)")
                                found_new_email = True
                        else:
                            # 如果没有发送时间，跳过处理（严格模式）
                            logger.debug(f"⏭️ 跳过无时间戳的邮件: {email_data['subject']}")
                            continue
                        
                        # 检查邮件内容是否与当前邮箱相关或是验证码邮件
                        if email.lower() in email_data['content'].lower() or self._is_recent_verification_email(email_data['content']):
                            code = self.email_handler._extract_verification_code(email_data['content'])
                            if code and code not in self.email_handler.used_codes:
                                valid_codes_found.append({
                                    'code': code,
                                    'subject': email_data['subject'],
                                    'time_diff': time_diff
                                })
                                logger.info(f"🔍 发现有效验证码: {code} (时差: {time_diff:.1f}秒)")
                            else:
                                if code:
                                    logger.warning(f"⚠️ 验证码 {code} 已被使用过，跳过")
                
                # 如果找到有效验证码，选择时间最接近的那个
                if valid_codes_found:
                    # 按时间差排序，选择最接近发送时间的验证码
                    valid_codes_found.sort(key=lambda x: abs(x['time_diff']))
                    best_code = valid_codes_found[0]
                    
                    # 标记验证码为已使用
                    self.email_handler.used_codes.add(best_code['code'])
                    logger.info(f"✅ 为 {email} 获取到验证码: {best_code['code']} (来自邮件: {best_code['subject']})")
                    return best_code['code']
                
                # 如果没有找到新邮件，给出更详细的信息
                if not found_new_email and send_time:
                    elapsed_time = time.time() - start_time
                    logger.info(f"⏳ 未找到 {email} 的新验证码 (已等待 {elapsed_time:.1f}秒)")
                    
                    # 如果等待时间超过60秒，记录详细信息但不降低标准
                    if elapsed_time > 60:
                        logger.warning(f"⚠️ 等待时间较长，但仍坚持严格的时间过滤标准")
                        logger.warning(f"   发送时间: {send_time.strftime('%Y-%m-%d %H:%M:%S')}")
                        logger.warning(f"   当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                # 等待一段时间后重试
                wait_time = 5 if retry_count <= 6 else 10  # 前30秒每5秒重试，之后每10秒重试
                logger.info(f"⏳ 等待 {wait_time} 秒后重试... (剩余时间: {timeout - (time.time() - start_time):.1f}秒)")
                await asyncio.sleep(wait_time)
                
            except Exception as e:
                logger.error(f"❌ 获取 {email} 验证码时发生错误: {str(e)}")
                await asyncio.sleep(5)
        
        logger.error(f"❌ 获取 {email} 验证码超时（{timeout}秒）")
        logger.error(f"💡 建议检查: 1) 邮件是否真的发送成功 2) 网络连接 3) Gmail设置")
        return None
    
    def _is_recent_verification_email(self, content: str) -> bool:
        """
        检查是否是最近的验证码邮件
        
        Args:
            content: 邮件内容
            
        Returns:
            是否是验证码邮件
        """
        verification_keywords = [
            'verification code',
            'login code',
            'polyflow',
            'verify',
            'code'
        ]
        
        content_lower = content.lower()
        return any(keyword in content_lower for keyword in verification_keywords)
    
    async def batch_register(self, emails: List[str], referral_code: str = "", delay_between_requests: int = 15) -> List[Dict]:
        """
        批量注册账号 - 确保每个邮箱完整流程完成后才处理下一个
        
        Args:
            emails: 邮箱地址列表
            referral_code: 推荐码（可选）
            delay_between_requests: 请求之间的延迟时间（秒）
            
        Returns:
            注册结果列表
        """
        results = []
        
        logger.info(f"🚀 开始批量注册，共 {len(emails)} 个邮箱")
        logger.info(f"⚙️ 每个邮箱间隔: {delay_between_requests}秒")
        
        for i, email in enumerate(emails, 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"📧 正在处理第 {i}/{len(emails)} 个邮箱: {email}")
            logger.info(f"{'='*60}")
            
            try:
                # 在处理每个邮箱前，彻底清理状态
                if hasattr(self, 'email_handler') and self.email_handler:
                    self.email_handler.clear_used_codes()
                    logger.info(f"🧹 预清理: 已清除验证码缓存")
                
                # 完整处理单个邮箱的注册流程
                result = await self.register_account(email, referral_code)
                results.append(result)
                
                if result['success']:
                    logger.info(f"✅ 第 {i}/{len(emails)} 个邮箱注册成功: {email}")
                else:
                    logger.error(f"❌ 第 {i}/{len(emails)} 个邮箱注册失败: {email}")
                    logger.error(f"   失败原因: {result['error']}")
                
                # 在处理下一个邮箱前等待并彻底清理状态
                if i < len(emails):
                    # 增加随机延迟，避免被检测
                    actual_delay = delay_between_requests + random.uniform(-3, 8)
                    logger.info(f"⏳ 等待 {actual_delay:.1f} 秒后处理下一个邮箱...")
                    await asyncio.sleep(actual_delay)
                    
                    # 彻底清理状态，为下一个邮箱做准备
                    if hasattr(self, 'email_handler') and self.email_handler:
                        self.email_handler.clear_used_codes()
                        logger.info(f"🧹 已清理验证码缓存，准备处理下一个邮箱")
                        
                        # 刷新邮箱连接，确保状态干净
                        try:
                            self.email_handler.imap.select('INBOX')
                            logger.info(f"🔄 已刷新邮箱连接")
                        except Exception as e:
                            logger.warning(f"刷新邮箱连接失败: {str(e)}")
                    
            except Exception as e:
                logger.error(f"❌ 处理邮箱 {email} 时发生异常: {str(e)}")
                results.append({
                    'success': False,
                    'email': email,
                    'token': None,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
                
                # 即使出现异常，也要清理状态
                if hasattr(self, 'email_handler') and self.email_handler:
                    self.email_handler.clear_used_codes()
                    logger.info(f"🧹 异常处理: 已清理验证码缓存")
        
        # 生成批量注册报告
        self._generate_batch_report(results)
        
        logger.info(f"\n🏁 批量注册完成!")
        return results
    
    def _generate_batch_report(self, results: List[Dict]):
        """生成批量注册报告"""
        try:
            os.makedirs('data/reports', exist_ok=True)
            
            successful = [r for r in results if r['success']]
            failed = [r for r in results if not r['success']]
            
            report = {
                'timestamp': datetime.now().isoformat(),
                'total_processed': len(results),
                'successful_count': len(successful),
                'failed_count': len(failed),
                'success_rate': f"{len(successful)/len(results)*100:.1f}%" if results else "0%",
                'successful_emails': [r['email'] for r in successful],
                'failed_emails': [{'email': r['email'], 'error': r['error']} for r in failed],
                'detailed_results': results
            }
            
            filename = f"data/reports/polyflow_batch_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            logger.info(f"批量注册报告已生成: {filename}")
            logger.info(f"注册统计: 总计 {len(results)}, 成功 {len(successful)}, 失败 {len(failed)}, 成功率 {report['success_rate']}")
            
        except Exception as e:
            logger.error(f"生成批量注册报告时发生错误: {str(e)}") 