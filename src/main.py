import asyncio
import os
from loguru import logger
from proxy.proxy_manager import ProxyManager
from browser.browser_manager import BrowserManager
from email_handler import EmailHandler
from captcha.captcha_solver import CaptchaSolver
from dotenv import load_dotenv
import yaml
import json
from datetime import datetime

class AutoRegistry:
    def __init__(self, config_path: str = "config.yaml"):
        self.config = self._load_config(config_path)
        load_dotenv()
        
        # 初始化各个模块
        self.proxy_manager = ProxyManager(config_path)
        self.browser_manager = BrowserManager(config_path)
        self.email_handler = EmailHandler(config_path)
        self.captcha_solver = CaptchaSolver(config_path)
        
        # 创建必要的目录
        os.makedirs('data/cookies', exist_ok=True)
        os.makedirs('logs', exist_ok=True)
        
        # 配置日志
        logger.add(
            "logs/app.log",
            rotation="1 day",
            retention="7 days",
            level="INFO"
        )
    
    def _load_config(self, config_path: str) -> dict:
        """加载配置文件"""
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    async def register_account(self, target_url: str, email: str, password: str):
        """注册新账号"""
        try:
            # 获取代理
            proxy = await self.proxy_manager.rotate_proxy()
            if not proxy:
                logger.error("无法获取可用代理")
                return False
            
            # 获取浏览器页面
            page = await self.browser_manager.get_page()
            
            # 设置代理
            await page.route("**/*", lambda route: route.continue_(
                proxy=self.proxy_manager.get_proxy_url()
            ))
            
            # 访问目标网站
            await page.goto(target_url)
            logger.info(f"已访问目标网站: {target_url}")
            
            # 等待注册表单加载
            await self.browser_manager.wait_for_element(page, "form")
            
            # 填写注册表单
            await page.fill('input[type="email"]', email)
            await page.fill('input[type="password"]', password)
            
            # 处理验证码
            if await page.query_selector('iframe[src*="recaptcha"]'):
                site_key = await page.evaluate('() => document.querySelector("iframe[src*=\'recaptcha\']").getAttribute("data-sitekey")')
                recaptcha_response = await self.captcha_solver.solve_recaptcha(site_key, target_url)
                if recaptcha_response:
                    await page.evaluate(f'() => document.getElementById("g-recaptcha-response").innerHTML = "{recaptcha_response}"')
            
            # 提交表单
            await page.click('button[type="submit"]')
            
            # 等待验证邮件
            verification_code = await self.email_handler.get_latest_verification_code()
            if not verification_code:
                logger.error("未收到验证码")
                return False
            
            # 输入验证码
            await page.fill('input[type="text"]', verification_code)
            await page.click('button[type="submit"]')
            
            # 保存Cookie
            await self.browser_manager.save_cookies(page, f"{email}_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            
            logger.info(f"账号注册成功: {email}")
            return True
            
        except Exception as e:
            logger.error(f"注册过程发生错误: {str(e)}")
            return False
    
    async def close(self):
        """关闭所有资源"""
        await self.browser_manager.close()
        self.email_handler.disconnect()
        logger.info("所有资源已关闭")

async def main():
    # 创建自动注册实例
    registry = AutoRegistry()
    
    # 示例：注册账号
    success = await registry.register_account(
        target_url="https://ipfighter.com/en",
        email="test@example.com",
        password="YourPassword123"
    )
    
    if success:
        logger.info("注册流程完成")
    else:
        logger.error("注册流程失败")
    
    # 关闭资源
    await registry.close()

if __name__ == "__main__":
    asyncio.run(main()) 