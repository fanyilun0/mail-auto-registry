#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gmail邮件处理器模块

提供Gmail邮箱的IMAP连接和验证码提取功能
"""

import imaplib
import email
import re
import time
import asyncio
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from loguru import logger
import ssl

class EmailHandler:
    """Gmail邮件处理器类"""
    
    def __init__(self, config: dict = None):
        """
        初始化Gmail邮件处理器
        
        Args:
            config: 邮件配置字典，包含IMAP服务器信息
        """
        self.config = config or {}
        self.imap = None
        self.used_codes = set()  # 已使用的验证码缓存
        
        # 从配置中获取IMAP设置
        self.imap_server = self.config.get('imap_server', 'imap.gmail.com')
        self.imap_port = self.config.get('imap_port', 993)
        self.username = self.config.get('username')
        self.password = self.config.get('password')
        self.timeout = self.config.get('timeout', 120)
        
        # 验证码匹配模式
        self.code_patterns = [
            r'verification code[:\s]*(\d{6})',
            r'verify code[:\s]*(\d{6})',
            r'code[:\s]*(\d{6})',
            r'(\d{6})',  # 简单的6位数字
            r'verification code[:\s]*(\d{4,8})',  # 4-8位验证码
        ]
        
    def connect(self):
        """连接到Gmail IMAP服务器"""
        try:
            if not self.username or not self.password:
                raise ValueError("邮箱用户名或密码未配置")
            
            logger.info(f"正在连接到 {self.imap_server}:{self.imap_port}")
            
            # 创建SSL上下文
            ssl_context = ssl.create_default_context()
            
            # 连接到IMAP服务器
            self.imap = imaplib.IMAP4_SSL(
                self.imap_server, 
                self.imap_port,
                ssl_context=ssl_context
            )
            
            # 登录
            logger.info(f"正在登录邮箱: {self.username}")
            self.imap.login(self.username, self.password)
            
            # 选择收件箱
            self.imap.select('INBOX')
            
            logger.info("Gmail IMAP连接成功")
            
        except Exception as e:
            logger.error(f"连接Gmail IMAP服务器失败: {str(e)}")
            if self.imap:
                try:
                    self.imap.close()
                    self.imap.logout()
                except:
                    pass
                self.imap = None
            raise
    
    def disconnect(self):
        """断开Gmail IMAP连接"""
        if self.imap:
            try:
                logger.info("正在断开Gmail IMAP连接")
                self.imap.close()
                self.imap.logout()
                logger.info("Gmail IMAP连接已断开")
            except Exception as e:
                logger.warning(f"断开Gmail IMAP连接时出现警告: {str(e)}")
            finally:
                self.imap = None
    
    def clear_used_codes(self):
        """清除已使用的验证码缓存"""
        self.used_codes.clear()
        logger.info("已清除验证码缓存")
    
    def _search_recent_emails(self, sender_filter: str = None, subject_filter: str = None, minutes: int = 10) -> List[int]:
        """
        搜索最近的邮件
        
        Args:
            sender_filter: 发件人过滤条件
            subject_filter: 主题过滤条件
            minutes: 搜索最近多少分钟的邮件
            
        Returns:
            邮件ID列表（按时间倒序）
        """
        try:
            # 刷新邮箱状态，确保获取最新邮件
            try:
                self.imap.check()  # 检查邮箱更新
            except Exception as e:
                logger.debug(f"邮箱检查失败: {str(e)}")
            
            # 计算搜索时间范围
            since_date = (datetime.now() - timedelta(minutes=minutes)).strftime('%d-%b-%Y')
            
            # 构建搜索条件
            search_criteria = [f'SINCE {since_date}']
            
            if sender_filter:
                search_criteria.append(f'FROM "{sender_filter}"')
            
            if subject_filter:
                search_criteria.append(f'SUBJECT "{subject_filter}"')
            
            # 搜索邮件
            search_query = ' '.join(search_criteria)
            logger.debug(f"搜索邮件条件: {search_query}")
            
            typ, data = self.imap.search(None, search_query)
            
            if typ != 'OK':
                logger.warning(f"邮件搜索失败: {typ}")
                return []
            
            # 获取邮件ID列表
            email_ids = data[0].split()
            logger.debug(f"找到 {len(email_ids)} 封符合条件的邮件")
            
            # 按时间倒序排列（最新的在前）
            return [int(eid) for eid in reversed(email_ids)]
            
        except Exception as e:
            logger.error(f"搜索邮件时发生错误: {str(e)}")
            return []
    
    def _extract_verification_code(self, email_content: str) -> Optional[str]:
        """
        从邮件内容中提取验证码
        
        Args:
            email_content: 邮件内容
            
        Returns:
            验证码字符串，如果未找到返回None
        """
        try:
            # 尝试不同的验证码匹配模式
            for pattern in self.code_patterns:
                matches = re.findall(pattern, email_content, re.IGNORECASE)
                if matches:
                    code = matches[0]
                    # 验证码长度检查
                    if 4 <= len(code) <= 8 and code.isdigit():
                        if code not in self.used_codes:
                            logger.info(f"提取到验证码: {code}")
                            return code
                        else:
                            logger.warning(f"验证码 {code} 已被使用过")
            
            logger.warning("未能从邮件中提取到有效的验证码")
            return None
            
        except Exception as e:
            logger.error(f"提取验证码时发生错误: {str(e)}")
            return None
    
    def _get_email_content_with_timestamp(self, email_id: int) -> Optional[Dict]:
        """
        获取邮件内容和时间戳信息
        
        Args:
            email_id: 邮件ID
            
        Returns:
            包含内容和时间戳的字典
        """
        try:
            # 获取邮件
            typ, data = self.imap.fetch(str(email_id), '(RFC822)')
            
            if typ != 'OK':
                logger.warning(f"获取邮件失败: {email_id}")
                return None
            
            # 解析邮件
            raw_email = data[0][1]
            email_message = email.message_from_bytes(raw_email)
            
            # 获取邮件基本信息
            subject = email_message.get('Subject', '')
            sender = email_message.get('From', '')
            date_str = email_message.get('Date', '')
            
            # 解析邮件时间
            email_time = None
            if date_str:
                try:
                    from email.utils import parsedate_to_datetime
                    email_time = parsedate_to_datetime(date_str)
                    # 保留原始时区信息，不要移除
                    logger.debug(f"解析邮件时间: {email_time} (原始: {date_str})")
                except Exception as e:
                    logger.warning(f"解析邮件时间失败: {str(e)}")
                    # 尝试其他时间解析方法
                    try:
                        import dateutil.parser
                        email_time = dateutil.parser.parse(date_str)
                        logger.debug(f"备用解析邮件时间: {email_time}")
                    except Exception as e2:
                        logger.warning(f"备用时间解析也失败: {str(e2)}")
            
            logger.debug(f"处理邮件 - 发件人: {sender}, 主题: {subject}, 日期: {date_str}")
            
            # 提取邮件内容
            content = ""
            
            if email_message.is_multipart():
                # 多部分邮件
                for part in email_message.walk():
                    content_type = part.get_content_type()
                    if content_type in ['text/plain', 'text/html']:
                        try:
                            payload = part.get_payload(decode=True)
                            if payload:
                                content += payload.decode('utf-8', errors='ignore')
                        except Exception as e:
                            logger.warning(f"解码邮件部分失败: {str(e)}")
            else:
                # 单部分邮件
                try:
                    payload = email_message.get_payload(decode=True)
                    if payload:
                        content = payload.decode('utf-8', errors='ignore')
                except Exception as e:
                    logger.warning(f"解码邮件失败: {str(e)}")
            
            return {
                'content': content,
                'subject': subject,
                'sender': sender,
                'date': date_str,
                'timestamp': email_time,
                'email_id': email_id
            }
            
        except Exception as e:
            logger.error(f"获取邮件内容时发生错误: {str(e)}")
            return None
    
    def _get_email_content(self, email_id: int) -> Optional[str]:
        """
        获取邮件内容（兼容方法）
        
        Args:
            email_id: 邮件ID
            
        Returns:
            邮件内容字符串
        """
        email_data = self._get_email_content_with_timestamp(email_id)
        return email_data['content'] if email_data else None
    
    def get_latest_verification_code(self, timeout: int = 120, sender_filter: str = None, max_age_minutes: int = 10) -> Optional[str]:
        """
        获取最新的验证码
        
        Args:
            timeout: 超时时间（秒）
            sender_filter: 发件人过滤条件（可选）
            max_age_minutes: 验证码最大有效时间（分钟）
            
        Returns:
            验证码字符串，如果获取失败返回None
        """
        if not self.imap:
            logger.error("IMAP连接未建立，请先调用connect()方法")
            return None
        
        logger.info(f"开始获取验证码，超时时间: {timeout}秒，最大有效时间: {max_age_minutes}分钟")
        
        start_time = time.time()
        
        # 常见的验证码发件人
        common_senders = [
            'polyflow',
            'noreply',
            'no-reply',
            'verification',
            'security'
        ]
        
        while time.time() - start_time < timeout:
            try:
                # 搜索最近的邮件
                email_ids = self._search_recent_emails(
                    sender_filter=sender_filter,
                    subject_filter='verification' if not sender_filter else None,
                    minutes=max_age_minutes
                )
                
                # 如果没有指定发件人过滤，尝试常见的发件人
                if not email_ids and not sender_filter:
                    for sender in common_senders:
                        email_ids = self._search_recent_emails(
                            sender_filter=sender,
                            minutes=max_age_minutes
                        )
                        if email_ids:
                            break
                
                # 处理找到的邮件（按时间倒序，最新的在前）
                for email_id in email_ids:
                    email_data = self._get_email_content_with_timestamp(email_id)
                    if email_data and email_data['content']:
                        # 检查邮件时间是否在有效范围内
                        if email_data['timestamp']:
                            email_age = datetime.now(email_data['timestamp'].tzinfo) - email_data['timestamp']
                            if email_age.total_seconds() > max_age_minutes * 60:
                                logger.info(f"跳过过期邮件: {email_data['subject']} (发送时间: {email_data['date']})")
                                continue
                        
                        code = self._extract_verification_code(email_data['content'])
                        if code:
                            # 检查验证码是否已被使用
                            if code not in self.used_codes:
                                # 标记验证码为已使用
                                self.used_codes.add(code)
                                logger.info(f"成功获取验证码: {code} (来自邮件: {email_data['subject']})")
                                return code
                            else:
                                logger.warning(f"验证码 {code} 已被使用过，跳过")
                
                # 等待一段时间后重试
                logger.info("未找到有效验证码，等待5秒后重试...")
                time.sleep(5)
                
            except Exception as e:
                logger.error(f"获取验证码时发生错误: {str(e)}")
                time.sleep(5)
        
        logger.error(f"获取验证码超时（{timeout}秒）")
        return None
    
    async def get_latest_verification_code_async(self, timeout: int = 120, sender_filter: str = None) -> Optional[str]:
        """
        异步获取最新的验证码
        
        Args:
            timeout: 超时时间（秒）
            sender_filter: 发件人过滤条件（可选）
            
        Returns:
            验证码字符串，如果获取失败返回None
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            self.get_latest_verification_code,
            timeout,
            sender_filter
        )
    
    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.disconnect()

# 为了向后兼容，保留RealEmailHandler别名
RealEmailHandler = EmailHandler 