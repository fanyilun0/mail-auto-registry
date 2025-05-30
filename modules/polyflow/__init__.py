# -*- coding: utf-8 -*-
"""
Polyflow自动注册模块

提供Polyflow网站的自动注册功能，包括API客户端和浏览器自动化两种方式。
"""

from .polyflow_api_client import PolyflowAPIClient

__version__ = "1.0.0"
__author__ = "Auto Registry Team"

__all__ = [
    "PolyflowAPIClient",
] 