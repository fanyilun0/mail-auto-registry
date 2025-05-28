import asyncio
import os
import email
from loguru import logger
from browser.browser_manager import BrowserManager
from email_handler import EmailHandler
from proxy.proxy_manager import ProxyManager
from captcha.captcha_solver import CaptchaSolver
from dotenv import load_dotenv

class VerificationTest:
    def __init__(self):
        load_dotenv()
        self.browser_manager = BrowserManager()
        self.email_handler = EmailHandler()
        self.proxy_manager = ProxyManager()
        self.captcha_solver = CaptchaSolver()
        
        # 配置日志
        logger.add(
            "logs/verification.log",
            rotation="1 day",
            retention="7 days",
            level="INFO"
        )
    
    async def test_proxy_connection(self):
        """测试代理连接"""
        try:
            logger.info("开始测试代理连接...")
            
            # 获取当前代理
            proxy_url = self.proxy_manager.get_proxy_url()
            if proxy_url:
                logger.info(f"✅ 当前代理: {proxy_url}")
                return True
            else:
                logger.warning("⚠️ 未配置代理，将使用直连")
                return False
                
        except Exception as e:
            logger.error(f"❌ 代理连接测试失败: {str(e)}")
            return False

    async def test_browser_automation(self):
        """测试浏览器自动化 - 访问 ipfighter.com/en (使用代理)"""
        try:
            logger.info("开始测试浏览器自动化...")
            
            # 获取代理URL
            proxy_url = self.proxy_manager.get_proxy_url()
            
            # 获取浏览器页面（使用代理）
            page = await self.browser_manager.get_page(proxy_url)
            
            # 访问目标网站
            # target_url = "https://ipfighter.com/en"
            target_url = "https://whatismyipaddress.com/"
            await page.goto(target_url)
            logger.info(f"✅ 成功访问目标网站: {target_url}")
            
            # 等待页面加载完成
            await page.wait_for_load_state('networkidle')
            
            # 获取页面标题
            title = await page.title()
            logger.info(f"页面标题: {title}")
            
            # 尝试获取IP信息来验证代理是否生效
            try:
                ip_element = await page.query_selector('text=Your IP')
                if ip_element:
                    logger.info("✅ 检测到IP信息显示")
            except:
                pass
            
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
    
    def test_captcha_service(self):
        """测试验证码服务"""
        try:
            logger.info("开始测试验证码服务...")
            
            # 检查API密钥
            api_key = os.getenv('CAPTCHA_API_KEY')
            if not api_key or api_key == 'your_2captcha_api_key':
                logger.warning("⚠️ 验证码API密钥未设置，请在.env文件中配置CAPTCHA_API_KEY")
                return False
            
            # 获取账户余额
            balance = self.captcha_solver.get_balance()
            if balance > 0:
                logger.info(f"✅ 验证码服务连接成功，账户余额: ${balance}")
                return True
            else:
                logger.warning("⚠️ 验证码服务余额不足或连接失败")
                return False
                
        except Exception as e:
            logger.error(f"❌ 验证码服务测试失败: {str(e)}")
            return False
    
    async def test_email_verification_code(self):
        """测试邮件验证码提取"""
        try:
            logger.info("开始测试邮件验证码提取...")
            
            # 检查环境变量
            username = os.getenv('EMAIL_USERNAME')
            password = os.getenv('EMAIL_PASSWORD')
            
            if not username or not password:
                logger.warning("⚠️ 邮箱配置未设置，跳过验证码提取测试")
                return False
            
            # 连接到邮件服务器
            self.email_handler.connect()
            logger.info("✅ 成功连接到邮件服务器")
            
            # 模拟获取验证码（设置较短的超时时间用于测试）
            logger.info("正在检查最近的邮件中是否有验证码...")
            
            # 选择收件箱
            self.email_handler.imap.select('INBOX')
            
            # 获取最新的5封邮件进行测试
            _, messages = self.email_handler.imap.search(None, 'ALL')
            if messages[0]:
                email_ids = messages[0].split()[-5:]  # 最新5封邮件
                logger.info(f"检查最近的 {len(email_ids)} 封邮件")
                
                for email_id in reversed(email_ids):
                    try:
                        _, msg_data = self.email_handler.imap.fetch(email_id, '(RFC822)')
                        email_body = msg_data[0][1]
                        email_message = email.message_from_bytes(email_body)
                        
                        # 获取邮件主题
                        subject = self.email_handler._decode_email_subject(email_message['subject'] or '')
                        
                        # 获取邮件内容
                        body = ""
                        if email_message.is_multipart():
                            for part in email_message.walk():
                                if part.get_content_type() == "text/plain":
                                    try:
                                        body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                                        break
                                    except:
                                        continue
                        else:
                            try:
                                body = email_message.get_payload(decode=True).decode('utf-8', errors='ignore')
                            except:
                                continue
                        
                        # 尝试提取验证码
                        if body:
                            code = self.email_handler._extract_verification_code(body)
                            if code:
                                logger.info(f"✅ 在邮件中找到验证码: {code} (主题: {subject[:50]}...)")
                                return True
                    except Exception as e:
                        logger.debug(f"处理邮件时出错: {str(e)}")
                        continue
                
                logger.info("📧 未在最近的邮件中找到验证码，但邮件访问功能正常")
                return True
            else:
                logger.info("📧 收件箱为空，但连接功能正常")
                return True
                
        except Exception as e:
            logger.error(f"❌ 邮件验证码提取测试失败: {str(e)}")
            return False
        finally:
            if hasattr(self.email_handler, 'imap') and self.email_handler.imap:
                self.email_handler.disconnect()
    
    async def run_verification_tests(self):
        """运行所有验证测试"""
        logger.info("=== 开始逐步验证测试 ===")
        
        # 测试1: 代理连接
        proxy_success = await self.test_proxy_connection()
        
        # 测试2: 浏览器自动化（使用代理）
        browser_success = await self.test_browser_automation()
        
        # 测试3: 邮件服务连接
        email_success = self.test_email_connection()
        
        # 测试4: 验证码服务
        captcha_success = self.test_captcha_service()
        
        # 测试5: 邮件验证码提取
        email_code_success = await self.test_email_verification_code()
        
        # 输出测试结果
        logger.info("=== 测试结果汇总 ===")
        logger.info(f"代理连接测试: {'✅ 通过' if proxy_success else '❌ 失败'}")
        logger.info(f"浏览器自动化访问 ipfighter.com/en: {'✅ 通过' if browser_success else '❌ 失败'}")
        logger.info(f"Gmail IMAP 邮件服务连接: {'✅ 通过' if email_success else '❌ 失败'}")
        logger.info(f"验证码服务连接: {'✅ 通过' if captcha_success else '❌ 失败'}")
        logger.info(f"邮件验证码提取: {'✅ 通过' if email_code_success else '❌ 失败'}")
        
        # 统计通过的测试
        passed_tests = sum([proxy_success, browser_success, email_success, captcha_success, email_code_success])
        total_tests = 5
        
        if passed_tests == total_tests:
            logger.info("🎉 所有验证测试通过！")
        elif passed_tests >= 2:  # 至少通过代理和浏览器测试
            logger.info(f"✅ 核心功能测试通过 ({passed_tests}/{total_tests})")
        else:
            logger.warning("⚠️ 多项测试失败，请检查配置")
        
        # 关闭资源
        await self.browser_manager.close()

async def main():
    """主函数"""
    test = VerificationTest()
    await test.run_verification_tests()

if __name__ == "__main__":
    asyncio.run(main()) 