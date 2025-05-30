# -*- coding: utf-8 -*-
"""
Gmail邮件处理模块

提供Gmail邮箱的IMAP连接和验证码提取功能
"""

from .email_handler import EmailHandler, RealEmailHandler

__version__ = "1.0.0"
__author__ = "Auto Registry Team"

__all__ = [
    "EmailHandler",
    "RealEmailHandler"
] 