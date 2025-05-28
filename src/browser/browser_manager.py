from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from typing import Optional, List, Dict
import asyncio
from loguru import logger
import yaml
import random
import json
import os

class BrowserManager:
    def __init__(self, config_path: str = "config.yaml"):
        self.config = self._load_config(config_path)
        self.browsers: List[Browser] = []
        self.contexts: List[BrowserContext] = []
        self.pages: List[Page] = []
        self.playwright = None
        
    def _load_config(self, config_path: str) -> dict:
        """加载配置文件"""
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)['browser']
    
    async def initialize(self, proxy_url: str = None):
        """初始化浏览器实例池"""
        if not self.playwright:
            self.playwright = await async_playwright().start()
        
        # 只创建一个浏览器实例用于测试
        if not self.browsers:
            launch_options = {
                'headless': self.config['headless']
            }
            
            # 如果提供了代理，添加代理配置
            if proxy_url:
                launch_options['proxy'] = {'server': proxy_url}
                logger.info(f"使用代理: {proxy_url}")
            
            browser = await self.playwright.chromium.launch(**launch_options)
            self.browsers.append(browser)
            logger.info("浏览器实例已创建")
    
    async def get_page(self, proxy_url: str = None) -> Optional[Page]:
        """获取可用的页面实例"""
        if not self.pages:
            if not self.browsers:
                await self.initialize(proxy_url)
            
            browser = self.browsers[0]  # 使用第一个浏览器实例
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            )
            self.contexts.append(context)
            
            page = await context.new_page()
            self.pages.append(page)
            
            # 设置页面超时
            page.set_default_timeout(self.config['timeout'])
            
            # 注入反检测脚本
            await self._inject_anti_detection(page)
            
        return self.pages[0]
    
    async def _inject_anti_detection(self, page: Page):
        """注入反检测脚本"""
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
    
    async def save_cookies(self, page: Page, filename: str):
        """保存Cookie"""
        cookies = await page.context.cookies()
        os.makedirs('data/cookies', exist_ok=True)
        with open(f'data/cookies/{filename}.json', 'w') as f:
            json.dump(cookies, f)
        logger.info(f"Cookie已保存到: {filename}")
    
    async def load_cookies(self, page: Page, filename: str):
        """加载Cookie"""
        try:
            with open(f'data/cookies/{filename}.json', 'r') as f:
                cookies = json.load(f)
            await page.context.add_cookies(cookies)
            logger.info(f"Cookie已加载: {filename}")
        except FileNotFoundError:
            logger.warning(f"Cookie文件不存在: {filename}")
    
    async def close(self):
        """关闭所有浏览器实例"""
        for page in self.pages:
            await page.close()
        for context in self.contexts:
            await context.close()
        for browser in self.browsers:
            await browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("所有浏览器实例已关闭")
    
    async def wait_for_element(self, page: Page, selector: str, timeout: int = None):
        """等待元素出现并可交互"""
        try:
            await page.wait_for_selector(selector, state='visible', timeout=timeout or self.config['timeout'])
            await page.wait_for_selector(selector, state='enabled', timeout=timeout or self.config['timeout'])
        except Exception as e:
            logger.error(f"等待元素超时: {selector}")
            raise e 