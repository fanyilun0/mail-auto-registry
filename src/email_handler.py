import imaplib
import email
import re
import time
from email.header import decode_header
from typing import Optional, List, Dict
import asyncio
from datetime import datetime, timedelta
from loguru import logger
import yaml
import os
from dotenv import load_dotenv

class EmailHandler:
    def __init__(self, config_path: str = "config.yaml"):
        self.config = self._load_config(config_path)
        load_dotenv()
        self.imap = None
        self.used_codes = set()
        
    def _load_config(self, config_path: str) -> dict:
        """加载配置文件"""
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)['email']
    
    def connect(self):
        """连接到IMAP服务器"""
        try:
            username = os.getenv('EMAIL_USERNAME')
            password = os.getenv('EMAIL_PASSWORD')
            
            if not username or not password:
                raise ValueError("邮箱用户名或密码未设置，请检查.env文件中的EMAIL_USERNAME和EMAIL_PASSWORD")
            
            self.imap = imaplib.IMAP4_SSL(
                self.config['imap_server'],
                self.config['imap_port']
            )
            self.imap.login(username, password)
            logger.info("已连接到邮件服务器")
        except Exception as e:
            logger.error(f"邮件服务器连接失败: {str(e)}")
            raise
    
    def disconnect(self):
        """断开IMAP连接"""
        if self.imap:
            try:
                self.imap.close()
                self.imap.logout()
                logger.info("已断开邮件服务器连接")
            except Exception as e:
                logger.error(f"断开连接时发生错误: {str(e)}")
    
    def _decode_email_subject(self, subject: str) -> str:
        """解码邮件主题"""
        decoded_parts = []
        for part, encoding in decode_header(subject):
            if isinstance(part, bytes):
                decoded_parts.append(part.decode(encoding or 'utf-8'))
            else:
                decoded_parts.append(part)
        return ''.join(decoded_parts)
    
    def _extract_verification_code(self, email_body: str) -> Optional[str]:
        """从邮件内容中提取验证码"""
        # 常见的验证码模式
        patterns = [
            r'验证码[：:]\s*(\d{4,6})',
            r'verification code[：:]\s*(\d{4,6})',
            r'code[：:]\s*(\d{4,6})',
            r'[\s\S]*?(\d{4,6})[\s\S]*?'  # 通用模式
        ]
        
        for pattern in patterns:
            match = re.search(pattern, email_body, re.IGNORECASE)
            if match:
                code = match.group(1)
                if code not in self.used_codes:
                    self.used_codes.add(code)
                    return code
        return None
    
    def get_latest_verification_code(self, timeout: int = None) -> Optional[str]:
        """获取最新的验证码"""
        timeout = timeout or self.config.get('timeout', 120)
        start_time = datetime.now()
        
        while (datetime.now() - start_time).seconds < timeout:
            try:
                self.imap.select('INBOX')
                _, messages = self.imap.search(None, 'ALL')
                
                # 获取最新的10封邮件
                email_ids = messages[0].split()[-10:]
                
                for email_id in reversed(email_ids):
                    _, msg_data = self.imap.fetch(email_id, '(RFC822)')
                    email_body = msg_data[0][1]
                    email_message = email.message_from_bytes(email_body)
                    
                    # 获取邮件主题
                    subject = self._decode_email_subject(email_message['subject'])
                    
                    # 获取邮件内容
                    body = ""
                    if email_message.is_multipart():
                        for part in email_message.walk():
                            if part.get_content_type() == "text/plain":
                                body = part.get_payload(decode=True).decode()
                                break
                    else:
                        body = email_message.get_payload(decode=True).decode()
                    
                    # 提取验证码
                    code = self._extract_verification_code(body)
                    if code:
                        logger.info(f"找到验证码: {code}")
                        return code
                
                # 等待5秒后重试
                time.sleep(5)
                
            except Exception as e:
                logger.error(f"获取验证码时发生错误: {str(e)}")
                time.sleep(5)
        
        logger.error("获取验证码超时")
        return None
    
    def clear_used_codes(self):
        """清除已使用的验证码记录"""
        self.used_codes.clear()
        logger.info("已清除验证码使用记录") 