#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Polyflow自动注册工具主程序

提供完整的邮箱自动注册功能，包括验证码处理、代理管理等。
"""

import asyncio
import sys
import os
from pathlib import Path
from typing import List, Dict, Optional
import yaml
from loguru import logger

# 添加项目根目录到Python路径
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from modules.polyflow.polyflow_api_client import PolyflowAPIClient
    from gmail.email_handler import EmailHandler
    from proxy.proxy_manager import ProxyManager
    from utils.config_loader import ConfigLoader
except ImportError as e:
    logger.error(f"导入模块失败: {e}")
    logger.error("请确保在项目根目录下运行此脚本")
    sys.exit(1)

class PolyflowMain:
    """Polyflow主程序类"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化主程序
        
        Args:
            config_path: 配置文件路径，默认为项目根目录下的config.yaml
        """
        self.project_root = project_root
        self.config_path = config_path or (self.project_root / "config.yaml")
        self.config = self._load_config()
        
        # 设置日志
        self._setup_logging()
        
        # 初始化组件
        self.proxy_manager = None
        self.api_client = None
        
    def _load_config(self) -> Dict:
        """加载配置文件"""
        try:
            # 使用新的配置加载器，支持环境变量和.env文件
            config_loader = ConfigLoader(self.config_path)
            config = config_loader.load_config()
            logger.info(f"配置文件加载成功: {self.config_path}")
            return config
        except FileNotFoundError:
            logger.error(f"配置文件不存在: {self.config_path}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"配置文件加载失败: {e}")
            sys.exit(1)
    
    def _setup_logging(self):
        """设置日志配置"""
        log_config = self.config.get('logging', {})
        
        # 创建日志目录
        log_dir = self.project_root / "logs"
        log_dir.mkdir(exist_ok=True)
        
        # 配置loguru
        logger.remove()  # 移除默认处理器
        
        # 添加控制台输出
        logger.add(
            sys.stdout,
            level=log_config.get('level', 'INFO'),
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            colorize=True
        )
        
        # 添加文件输出
        log_file = log_dir / f"polyflow_{Path(__file__).stem}.log"
        logger.add(
            str(log_file),
            level=log_config.get('level', 'INFO'),
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            rotation=log_config.get('rotation', '1 day'),
            retention=log_config.get('retention', '7 days'),
            encoding='utf-8'
        )
        
        logger.info("日志系统初始化完成")
    
    def _load_emails(self) -> List[str]:
        """加载邮箱列表"""
        email_file = self.project_root / "modules" / "polyflow" / "email.txt"
        emails = []
        
        try:
            if email_file.exists():
                with open(email_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            emails.append(line)
                logger.info(f"从 {email_file} 加载了 {len(emails)} 个邮箱地址")
            else:
                logger.error(f"邮箱配置文件不存在: {email_file}")
                logger.info("请创建该文件并添加要注册的邮箱地址（每行一个）")
        except Exception as e:
            logger.error(f"读取邮箱配置文件时发生错误: {str(e)}")
        
        return emails
    
    def _create_directories(self):
        """创建必要的目录"""
        directories = [
            "data/tokens",
            "data/screenshots", 
            "data/reports",
            "logs"
        ]
        
        for dir_path in directories:
            full_path = self.project_root / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
        
        logger.info("必要目录创建完成")
    
    async def _initialize_components(self):
        """初始化组件"""
        try:
            # 初始化代理管理器
            proxy_file = self.project_root / "modules" / "polyflow" / "proxies.txt"
            proxy_config = self.config.get('proxy', {})
            self.proxy_manager = ProxyManager(
                proxy_file=str(proxy_file) if proxy_file.exists() else None,
                proxy_type=proxy_config.get('type', 'http'),
                check_timeout=proxy_config.get('check_timeout', 10)
            )
            
            # 初始化邮件处理器
            email_config = self.config.get('email', {})
            self.email_handler = EmailHandler(config=email_config)
            
            # 初始化API客户端
            proxy_list = self.proxy_manager.get_proxy_list() if self.proxy_manager else []
            self.api_client = PolyflowAPIClient(
                email_handler=self.email_handler,
                proxy_list=proxy_list,
                config_manager=None  # 可以后续实现配置管理器
            )
            
            logger.info("组件初始化完成")
            logger.info(f"代理管理器状态: {self.proxy_manager.get_stats()}")
            
        except Exception as e:
            logger.error(f"组件初始化失败: {str(e)}")
            raise
    
    async def run_batch_registration(self, emails: List[str], referral_code: str = "") -> List[Dict]:
        """
        运行批量注册
        
        Args:
            emails: 邮箱地址列表
            referral_code: 推荐码（可选）
            
        Returns:
            注册结果列表
        """
        if not emails:
            logger.error("没有要注册的邮箱地址")
            return []
        
        logger.info(f"开始批量注册，共 {len(emails)} 个邮箱")
        
        # 初始化组件
        await self._initialize_components()
        
        results = []
        
        try:
            async with self.api_client:
                # 使用API客户端进行批量注册
                results = await self.api_client.batch_register(
                    emails=emails,
                    referral_code=referral_code,
                    delay_between_requests=self.config.get('security', {}).get('request_delay', 2)
                )
                
        except Exception as e:
            logger.error(f"批量注册过程中发生错误: {str(e)}")
            
        return results
    
    async def run_single_registration(self, email: str, referral_code: str = "") -> Dict:
        """
        运行单个邮箱注册
        
        Args:
            email: 邮箱地址
            referral_code: 推荐码（可选）
            
        Returns:
            注册结果
        """
        logger.info(f"开始注册单个邮箱: {email}")
        
        # 初始化组件
        await self._initialize_components()
        
        try:
            async with self.api_client:
                result = await self.api_client.register_account(
                    email=email,
                    referral_code=referral_code,
                    max_retries=self.config.get('security', {}).get('max_retries', 3)
                )
                return result
                
        except Exception as e:
            logger.error(f"单个邮箱注册过程中发生错误: {str(e)}")
            return {
                'success': False,
                'email': email,
                'token': None,
                'error': str(e),
                'timestamp': None
            }
    
    def print_results_summary(self, results: List[Dict]):
        """打印结果摘要"""
        if not results:
            logger.warning("没有注册结果")
            return
        
        successful = [r for r in results if r.get('success', False)]
        failed = [r for r in results if not r.get('success', False)]
        
        logger.info("=" * 50)
        logger.info("注册结果摘要:")
        logger.info(f"总计: {len(results)}")
        logger.info(f"成功: {len(successful)}")
        logger.info(f"失败: {len(failed)}")
        logger.info(f"成功率: {len(successful)/len(results)*100:.1f}%")
        
        if successful:
            logger.info("\n成功的邮箱:")
            for result in successful:
                logger.info(f"  ✅ {result['email']}")
        
        if failed:
            logger.warning("\n失败的邮箱:")
            for result in failed:
                logger.warning(f"  ❌ {result['email']}: {result.get('error', '未知错误')}")
        
        logger.info("=" * 50)

async def main():
    """主函数"""
    try:
        # 创建主程序实例
        app = PolyflowMain()
        
        # 创建必要目录
        app._create_directories()
        
        # 加载邮箱列表
        emails = app._load_emails()
        
        if not emails:
            logger.error("没有找到有效的邮箱地址，程序退出")
            return
        
        # 运行批量注册
        results = await app.run_batch_registration(emails)
        
        # 打印结果摘要
        app.print_results_summary(results)
        
    except KeyboardInterrupt:
        logger.info("用户中断程序执行")
    except Exception as e:
        logger.error(f"程序执行出错: {str(e)}")
        raise

if __name__ == "__main__":
    # 设置事件循环策略（Windows兼容性）
    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    # 运行主程序
    asyncio.run(main()) 