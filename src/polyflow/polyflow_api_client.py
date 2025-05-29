import asyncio
import aiohttp
import os
import json
from datetime import datetime, timezone
from loguru import logger
from typing import Optional, Dict, List
import time

class PolyflowAPIClient:
    """Polyflow API客户端，用于通过API进行自动注册"""
    
    def __init__(self, email_handler):
        self.email_handler = email_handler
        self.base_url = "https://api-v2.polyflow.tech"
        self.session = None
        
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        if self.session:
            await self.session.close()
    
    @staticmethod
    def load_email_list(email_file_path: str = "src/sites/email.txt") -> List[str]:
        """从email.txt文件加载邮箱地址列表"""
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
    
    async def send_verification_code(self, email: str) -> Dict[str, any]:
        """发送验证码到邮箱"""
        url = f"{self.base_url}/api/account/email/send"
        payload = {
            "email": email,
            "type": "login"
        }
        
        try:
            logger.info(f"正在向 {email} 发送验证码...")
            async with self.session.post(url, json=payload) as response:
                response_data = await response.json()
                
                if response.status == 200:
                    logger.info(f"验证码发送成功: {email}")
                    return {"success": True, "data": response_data}
                else:
                    logger.error(f"验证码发送失败: {email}, 状态码: {response.status}, 响应: {response_data}")
                    return {"success": False, "error": f"HTTP {response.status}: {response_data}"}
                    
        except Exception as e:
            logger.error(f"发送验证码时发生异常: {email}, 错误: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def login_with_code(self, email: str, code: str, referral_code: str = "") -> Dict[str, any]:
        """使用验证码登录"""
        url = f"{self.base_url}/api/account/email/login"
        payload = {
            "email": email,
            "code": code,
            "referral_code": referral_code
        }
        
        try:
            logger.info(f"正在使用验证码登录: {email}")
            async with self.session.post(url, json=payload) as response:
                response_data = await response.json()
                
                if response.status == 200 and response_data.get("success"):
                    logger.info(f"登录成功: {email}")
                    return {"success": True, "data": response_data}
                else:
                    logger.error(f"登录失败: {email}, 状态码: {response.status}, 响应: {response_data}")
                    return {"success": False, "error": f"HTTP {response.status}: {response_data}"}
                    
        except Exception as e:
            logger.error(f"登录时发生异常: {email}, 错误: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_verification_code_async(self, timeout: int = 120) -> Optional[str]:
        """异步获取验证码"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            self.email_handler.get_latest_verification_code,
            timeout
        )
    
    def save_token_data(self, email: str, token_data: Dict, tokens_file_path: str = "data/polyflow_tokens.txt"):
        """保存token数据到文件"""
        try:
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
            
            # 以追加模式写入文件
            with open(tokens_file_path, 'a', encoding='utf-8') as f:
                f.write(data_line)
                
            logger.info(f"Token数据已保存到: {tokens_file_path}")
            
            # 同时保存详细的JSON格式数据用于备份
            self._save_detailed_token_data(email, token_data)
            
        except Exception as e:
            logger.error(f"保存token数据时发生错误: {str(e)}")
    
    def _save_detailed_token_data(self, email: str, token_data: Dict):
        """保存详细的token数据到JSON文件"""
        try:
            os.makedirs('data/polyflow_tokens_detailed', exist_ok=True)
            
            detailed_data = {
                'email': email,
                'token_data': token_data,
                'timestamp': datetime.now().isoformat(),
                'site': 'polyflow.tech'
            }
            
            filename = f"data/polyflow_tokens_detailed/{email.replace('@', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(detailed_data, f, indent=2, ensure_ascii=False)
                
            logger.info(f"详细token数据已保存到: {filename}")
            
        except Exception as e:
            logger.error(f"保存详细token数据时发生错误: {str(e)}")
    
    async def register_account(self, email: str, referral_code: str = "", max_retries: int = 3) -> Dict[str, any]:
        """
        注册Polyflow账号的完整流程
        
        Args:
            email: 注册邮箱
            referral_code: 推荐码（可选）
            max_retries: 最大重试次数
            
        Returns:
            Dict包含注册结果和token信息
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
            
            # 清除之前的验证码记录
            self.email_handler.clear_used_codes()
            
            # 步骤1: 发送验证码
            send_result = await self.send_verification_code(email)
            if not send_result["success"]:
                result['error'] = f"发送验证码失败: {send_result['error']}"
                return result
            
            # 步骤2: 等待并获取验证码
            logger.info(f"等待验证码到达邮箱: {email}")
            await asyncio.sleep(5)  # 等待邮件到达
            
            verification_code = await self.get_verification_code_async(timeout=120)
            if not verification_code:
                result['error'] = "未能获取到验证码"
                return result
            
            logger.info(f"获取到验证码: {verification_code}")
            
            # 步骤3: 使用验证码登录
            login_result = await self.login_with_code(email, verification_code, referral_code)
            if not login_result["success"]:
                result['error'] = f"登录失败: {login_result['error']}"
                return result
            
            # 步骤4: 处理登录响应
            response_data = login_result["data"]
            if response_data.get("success") and "msg" in response_data:
                msg = response_data["msg"]
                token = msg.get("token")
                
                if token:
                    result['success'] = True
                    result['token'] = token
                    
                    # 保存token数据
                    self.save_token_data(email, response_data)
                    
                    logger.info(f"账号注册成功: {email}")
                else:
                    result['error'] = "响应中未找到token"
            else:
                result['error'] = f"登录响应异常: {response_data}"
                
        except Exception as e:
            logger.error(f"注册过程发生错误: {email}, 错误: {str(e)}")
            result['error'] = str(e)
            
        return result
    
    async def batch_register(self, emails: List[str], referral_code: str = "", delay_between_requests: int = 10) -> List[Dict]:
        """
        批量注册账号
        
        Args:
            emails: 邮箱地址列表
            referral_code: 推荐码（可选）
            delay_between_requests: 请求之间的延迟时间（秒）
            
        Returns:
            注册结果列表
        """
        results = []
        
        logger.info(f"开始批量注册，共 {len(emails)} 个邮箱")
        
        for i, email in enumerate(emails, 1):
            logger.info(f"正在处理第 {i}/{len(emails)} 个邮箱: {email}")
            
            try:
                result = await self.register_account(email, referral_code)
                results.append(result)
                
                if result['success']:
                    logger.info(f"✅ {email} 注册成功")
                else:
                    logger.error(f"❌ {email} 注册失败: {result['error']}")
                
                # 在处理下一个邮箱前等待
                if i < len(emails):
                    logger.info(f"等待 {delay_between_requests} 秒后处理下一个邮箱...")
                    await asyncio.sleep(delay_between_requests)
                    
            except Exception as e:
                logger.error(f"处理邮箱 {email} 时发生异常: {str(e)}")
                results.append({
                    'success': False,
                    'email': email,
                    'token': None,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
        
        # 生成批量注册报告
        self._generate_batch_report(results)
        
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