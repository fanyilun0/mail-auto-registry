import asyncio
import os
from loguru import logger
from browser.browser_manager import BrowserManager
from email_handler import EmailHandler
from dotenv import load_dotenv

class VerificationTest:
    def __init__(self):
        load_dotenv()
        self.browser_manager = BrowserManager()
        self.email_handler = EmailHandler()
        
        # 配置日志
        logger.add(
            "logs/verification.log",
            rotation="1 day",
            retention="7 days",
            level="INFO"
        )
    
    async def test_browser_automation(self):
        """测试浏览器自动化 - 访问 ipfighter.com/en"""
        try:
            logger.info("开始测试浏览器自动化...")
            
            # 获取浏览器页面
            page = await self.browser_manager.get_page()
            
            # 访问目标网站
            target_url = "https://ipfighter.com/en"
            await page.goto(target_url)
            logger.info(f"✅ 成功访问目标网站: {target_url}")
            
            # 等待页面加载完成
            await page.wait_for_load_state('networkidle')
            
            # 获取页面标题
            title = await page.title()
            logger.info(f"页面标题: {title}")
            
            # 截图保存
            os.makedirs('data/screenshots', exist_ok=True)
            await page.screenshot(path='data/screenshots/ipfighter_test.png')
            logger.info("✅ 页面截图已保存")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 浏览器自动化测试失败: {str(e)}")
            return False
    
    def test_email_connection(self):
        """测试邮件服务连接 - Gmail IMAP"""
        try:
            logger.info("开始测试邮件服务连接...")
            
            # 检查环境变量
            username = os.getenv('EMAIL_USERNAME')
            password = os.getenv('EMAIL_PASSWORD')
            
            if not username or not password:
                logger.warning("⚠️ 邮箱配置未设置，请复制 .env.example 为 .env 并配置邮箱信息")
                logger.info("💡 提示：需要配置 EMAIL_USERNAME 和 EMAIL_PASSWORD 环境变量")
                return False
            
            # 连接到邮件服务器
            self.email_handler.connect()
            logger.info("✅ 成功连接到 Gmail IMAP 服务器")
            
            # 测试邮箱选择
            self.email_handler.imap.select('INBOX')
            logger.info("✅ 成功选择收件箱")
            
            # 获取邮件数量
            _, messages = self.email_handler.imap.search(None, 'ALL')
            email_count = len(messages[0].split()) if messages[0] else 0
            logger.info(f"收件箱中共有 {email_count} 封邮件")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 邮件服务连接测试失败: {str(e)}")
            return False
        finally:
            if hasattr(self.email_handler, 'imap') and self.email_handler.imap:
                self.email_handler.disconnect()
    
    async def run_verification_tests(self):
        """运行所有验证测试"""
        logger.info("=== 开始逐步验证测试 ===")
        
        # 测试1: 浏览器自动化
        browser_success = await self.test_browser_automation()
        
        # 测试2: 邮件服务连接
        email_success = self.test_email_connection()
        
        # 输出测试结果
        logger.info("=== 测试结果汇总 ===")
        logger.info(f"浏览器自动化访问 ipfighter.com/en: {'✅ 通过' if browser_success else '❌ 失败'}")
        logger.info(f"Gmail IMAP 邮件服务连接: {'✅ 通过' if email_success else '❌ 失败'}")
        
        if browser_success and email_success:
            logger.info("🎉 所有验证测试通过！")
        else:
            logger.warning("⚠️ 部分测试失败，请检查配置")
        
        # 关闭资源
        await self.browser_manager.close()

async def main():
    """主函数"""
    test = VerificationTest()
    await test.run_verification_tests()

if __name__ == "__main__":
    asyncio.run(main()) 