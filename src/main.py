import asyncio
import os
from loguru import logger
from proxy.proxy_manager import ProxyManager
from browser.browser_manager import BrowserManager
from email_handler import EmailHandler
from captcha.captcha_solver import CaptchaSolver
from polyflow.polyflow_registry import PolyflowRegistry
from dotenv import load_dotenv
import yaml
import json
from datetime import datetime

class AutoRegistry:
    def __init__(self, config_path: str = "../config.yaml"):
        self.config = self._load_config(config_path)
        load_dotenv()
        
        # 初始化各个模块
        self.proxy_manager = ProxyManager(config_path)
        self.browser_manager = BrowserManager(config_path)
        self.email_handler = EmailHandler(config_path)
        self.captcha_solver = CaptchaSolver(config_path)
        
        # 初始化网站特定的注册器
        self.polyflow_registry = PolyflowRegistry(
            self.browser_manager, 
            self.email_handler
        )
        
        # 创建必要的目录
        os.makedirs('data/cookies', exist_ok=True)
        os.makedirs('data/tokens', exist_ok=True)
        os.makedirs('data/screenshots', exist_ok=True)
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
    
    async def register_polyflow_account(self, email: str) -> dict:
        """注册Polyflow账号"""
        logger.info(f"开始注册Polyflow账号: {email}")
        
        try:
            # 获取代理（如果启用）
            if self.config.get('proxy', {}).get('enabled', False):
                proxy = await self.proxy_manager.rotate_proxy()
                if proxy:
                    proxy_url = self.proxy_manager.get_proxy_url()
                    logger.info(f"使用代理: {proxy_url}")
                    # 使用代理初始化浏览器
                    await self.browser_manager.initialize(proxy_url)
            
            # 执行注册流程
            result = await self.polyflow_registry.register_account(email)
            
            if result['success']:
                logger.info(f"Polyflow账号注册成功: {email}")
                logger.info(f"Token: {result['token'][:50] if result['token'] else 'None'}...")
            else:
                logger.error(f"Polyflow账号注册失败: {result['error']}")
            
            return result
            
        except Exception as e:
            logger.error(f"注册Polyflow账号时发生错误: {str(e)}")
            return {
                'success': False,
                'email': email,
                'token': None,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    async def batch_register_polyflow_accounts(self, email_file_path: str = "sites/email.txt") -> dict:
        """批量注册Polyflow账号"""
        logger.info("开始批量注册Polyflow账号")
        
        # 加载邮箱列表
        emails = PolyflowRegistry.load_email_list(email_file_path)
        if not emails:
            logger.error("没有找到可用的邮箱地址")
            return {
                'total': 0,
                'success': 0,
                'failed': 0,
                'results': []
            }
        
        results = {
            'total': len(emails),
            'success': 0,
            'failed': 0,
            'results': []
        }
        
        logger.info(f"准备注册 {len(emails)} 个账号")
        
        # 清空之前的tokens.txt文件
        tokens_file = "data/tokens.txt"
        if os.path.exists(tokens_file):
            os.remove(tokens_file)
            logger.info("已清空之前的tokens.txt文件")
        
        for i, email in enumerate(emails, 1):
            logger.info(f"正在处理第 {i}/{len(emails)} 个邮箱: {email}")
            
            try:
                result = await self.register_polyflow_account(email)
                results['results'].append(result)
                
                if result['success']:
                    results['success'] += 1
                    logger.info(f"✅ {email} 注册成功")
                else:
                    results['failed'] += 1
                    logger.error(f"❌ {email} 注册失败: {result['error']}")
                
                # 在每次注册之间添加延迟，避免过于频繁的请求
                if i < len(emails):  # 不是最后一个
                    delay = self.config.get('security', {}).get('request_delay', 2)
                    logger.info(f"等待 {delay} 秒后继续下一个注册...")
                    await asyncio.sleep(delay)
                    
            except Exception as e:
                logger.error(f"处理邮箱 {email} 时发生异常: {str(e)}")
                results['failed'] += 1
                results['results'].append({
                    'success': False,
                    'email': email,
                    'token': None,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
        
        # 输出批量注册结果
        logger.info("=" * 60)
        logger.info("📊 批量注册结果统计")
        logger.info("=" * 60)
        logger.info(f"总计邮箱: {results['total']}")
        logger.info(f"成功注册: {results['success']}")
        logger.info(f"注册失败: {results['failed']}")
        logger.info(f"成功率: {(results['success']/results['total']*100):.1f}%")
        
        # 检查tokens.txt文件
        if os.path.exists(tokens_file):
            with open(tokens_file, 'r', encoding='utf-8') as f:
                token_lines = f.readlines()
            logger.info(f"📁 tokens.txt文件包含 {len(token_lines)} 个token")
        
        return results

    async def register_account(self, target_url: str, email: str, password: str):
        """注册新账号（通用方法，保持向后兼容）"""
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
    # 检查环境变量配置
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    email_username = os.getenv('EMAIL_USERNAME')
    email_password = os.getenv('EMAIL_PASSWORD')
    
    if not email_username or not email_password or email_username == 'your_email@gmail.com':
        logger.warning("⚠️  邮箱配置未设置或使用默认值")
        logger.info("📝 请按照以下步骤配置邮箱:")
        logger.info("1. 在项目根目录创建 .env 文件")
        logger.info("2. 设置以下环境变量:")
        logger.info("   EMAIL_USERNAME=your_email@gmail.com")
        logger.info("   EMAIL_PASSWORD=your_app_password")
        logger.info("   TEST_EMAIL=your_test_email@gmail.com")
        logger.info("3. 如果使用Gmail，需要生成应用密码")
        logger.info("4. 配置邮箱列表: 编辑 src/sites/email.txt")
        logger.info("5. 运行批量注册: python main.py")
        logger.info("")
        logger.info("💡 当前可以运行基本功能验证: python test_basic.py")
        return
    
    # 创建自动注册实例
    registry = AutoRegistry()
    
    # 检查是否存在邮箱配置文件
    email_file = "sites/email.txt"
    if os.path.exists(email_file):
        logger.info("🚀 开始批量注册Polyflow账号")
        results = await registry.batch_register_polyflow_accounts(email_file)
        
        if results['success'] > 0:
            logger.info("✅ 批量注册完成")
            logger.info(f"📧 成功注册: {results['success']} 个账号")
            logger.info(f"❌ 注册失败: {results['failed']} 个账号")
            logger.info("📁 Token已保存到: data/tokens.txt")
        else:
            logger.error("❌ 批量注册失败，没有成功注册任何账号")
    else:
        # 单个账号注册（向后兼容）
        test_email = os.getenv('TEST_EMAIL', email_username)
        
        logger.info("开始单个Polyflow账号注册测试")
        result = await registry.register_polyflow_account(test_email)
        
        if result['success']:
            logger.info("✅ Polyflow注册流程完成")
            logger.info(f"📧 邮箱: {result['email']}")
            logger.info(f"🔑 Token: {result['token'][:50] if result['token'] else 'None'}...")
        else:
            logger.error("❌ Polyflow注册流程失败")
            logger.error(f"错误信息: {result['error']}")
    
    # 关闭资源
    await registry.close()

if __name__ == "__main__":
    asyncio.run(main()) 