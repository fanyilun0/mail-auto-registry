import asyncio
import os
from loguru import logger
from playwright.async_api import Page
from typing import Optional, Dict
import json
from datetime import datetime
import time

class PolyflowRegistry:
    """Polyflow网站自动注册器"""
    
    def __init__(self, browser_manager, email_handler):
        self.browser_manager = browser_manager
        self.email_handler = email_handler
        self.base_url = "https://app.polyflow.tech/"
        
    @staticmethod
    def load_email_list(email_file_path: str = "sites/email.txt") -> list:
        """从email.txt文件加载邮箱地址列表"""
        emails = []
        try:
            with open(email_file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # 跳过空行和注释行
                    if line and not line.startswith('#'):
                        emails.append(line)
            logger.info(f"从 {email_file_path} 加载了 {len(emails)} 个邮箱地址")
        except FileNotFoundError:
            logger.error(f"邮箱配置文件 {email_file_path} 不存在")
        except Exception as e:
            logger.error(f"读取邮箱配置文件时发生错误: {str(e)}")
        
        return emails
    
    @staticmethod
    def save_token_to_batch_file(email: str, token: str, tokens_file_path: str = "data/tokens.txt"):
        """批量保存token到tokens.txt文件"""
        try:
            os.makedirs(os.path.dirname(tokens_file_path), exist_ok=True)
            
            # 以追加模式写入文件
            with open(tokens_file_path, 'a', encoding='utf-8') as f:
                f.write(f"{email}:{token}\n")
                
            logger.info(f"Token已保存到批量文件: {tokens_file_path}")
            
        except Exception as e:
            logger.error(f"保存token到批量文件时发生错误: {str(e)}")
        
    async def register_account(self, email: str) -> Dict[str, any]:
        """
        注册Polyflow账号
        
        Args:
            email: 注册邮箱
            
        Returns:
            Dict包含注册结果和token信息
        """
        result = {
            'success': False,
            'email': email,
            'token': None,
            'error': None,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # 获取浏览器页面
            page = await self.browser_manager.get_page()
            
            # 导航到目标网站
            logger.info(f"正在访问 {self.base_url}")
            await page.goto(self.base_url)
            
            # 等待页面加载完成
            await page.wait_for_load_state('networkidle')
            
            # 查找并点击Login/Sign up按钮
            login_button_selector = 'button:has-text("Login/Sign up")'
            await page.wait_for_selector(login_button_selector, timeout=10000)
            
            logger.info("找到Login/Sign up按钮，准备点击")
            await page.click(login_button_selector)
            
            # 等待登录模态框或新页面出现
            await page.wait_for_timeout(3000)
            
            # 检查是否出现了钱包连接选项或其他登录界面
            current_url = page.url
            logger.info(f"点击后的URL: {current_url}")
            
            # 查找可能的邮箱输入框（在模态框中）
            email_selectors = [
                'input[type="email"]',
                'input[placeholder*="email" i]',
                'input[placeholder*="Email" i]',
                'input[name="email"]',
                'input[id="email"]'
            ]
            
            email_input_found = False
            for selector in email_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=5000)
                    logger.info(f"找到邮箱输入框: {selector}")
                    await page.fill(selector, email)
                    email_input_found = True
                    break
                except:
                    continue
            
            if not email_input_found:
                # 如果没有找到邮箱输入框，可能是Web3钱包连接界面
                logger.info("未找到邮箱输入框，可能是Web3钱包连接界面")
                
                # 查找钱包连接选项
                wallet_selectors = [
                    'button:has-text("MetaMask")',
                    'button:has-text("WalletConnect")',
                    'button:has-text("Connect Wallet")',
                    '[data-testid="rk-wallet-option-metaMask"]',
                    '[data-testid="rk-wallet-option-walletConnect"]'
                ]
                
                wallet_found = False
                for selector in wallet_selectors:
                    try:
                        await page.wait_for_selector(selector, timeout=3000)
                        logger.info(f"找到钱包选项: {selector}")
                        wallet_found = True
                        break
                    except:
                        continue
                
                if wallet_found:
                    result['error'] = "这是一个Web3应用，需要连接钱包而不是邮箱注册"
                    result['success'] = False
                else:
                    result['error'] = "未找到预期的登录界面元素"
                
                # 保存当前页面状态用于调试
                await self._save_screenshot(page, email)
                return result
            
            # 如果找到了邮箱输入框，继续原有的流程
            logger.info(f"输入邮箱地址: {email}")
            
            # 查找发送按钮
            send_button_selectors = [
                'button:has-text("Send")',
                'button:has-text("Submit")',
                'button:has-text("Continue")',
                'button[type="submit"]'
            ]
            
            send_button_found = False
            for selector in send_button_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=3000)
                    await page.click(selector)
                    send_button_found = True
                    logger.info(f"点击了发送按钮: {selector}")
                    break
                except:
                    continue
            
            if not send_button_found:
                result['error'] = "未找到发送按钮"
                await self._save_screenshot(page, email)
                return result
            
            logger.info("已点击发送验证码按钮，等待验证码...")
            
            # 等待验证码输入框出现
            code_input_selectors = [
                'input[type="number"]',
                'input[placeholder*="code" i]',
                'input[placeholder*="Code" i]',
                'input[name="code"]',
                'input[id="code"]'
            ]
            
            code_input_found = False
            for selector in code_input_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=10000)
                    logger.info(f"找到验证码输入框: {selector}")
                    code_input_found = True
                    
                    # 连接邮件服务器获取验证码
                    if not self.email_handler.imap:
                        self.email_handler.connect()
                    
                    # 获取验证码
                    verification_code = await self._get_verification_code_async()
                    if not verification_code:
                        result['error'] = "未能获取到验证码"
                        return result
                    
                    logger.info(f"获取到验证码: {verification_code}")
                    
                    # 输入验证码
                    await page.fill(selector, verification_code)
                    break
                except:
                    continue
            
            if not code_input_found:
                result['error'] = "未找到验证码输入框"
                await self._save_screenshot(page, email)
                return result
            
            # 等待一下让验证码输入完成
            await page.wait_for_timeout(1000)
            
            # 查找并点击提交按钮
            submit_selectors = [
                'button:has-text("Submit")',
                'button:has-text("Verify")',
                'button:has-text("Continue")',
                'button[type="submit"]'
            ]
            
            submitted = False
            for selector in submit_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=2000)
                    await page.click(selector)
                    submitted = True
                    logger.info(f"点击了提交按钮: {selector}")
                    break
                except:
                    continue
            
            if not submitted:
                # 如果没有找到明确的提交按钮，尝试按回车键
                await page.keyboard.press('Enter')
                logger.info("按下回车键提交验证码")
            
            # 等待页面跳转或状态变化
            await page.wait_for_timeout(5000)  # 增加等待时间确保登录完成
            
            # 检查是否登录成功（通过URL变化或特定元素出现）
            current_url = page.url
            logger.info(f"当前URL: {current_url}")
            
            # 尝试获取localStorage中的token
            token = await self._extract_token(page)
            if token:
                result['token'] = token
                result['success'] = True
                logger.info("成功获取到token")
                
                # 保存token到批量文件
                self.save_token_to_batch_file(email, token)
                
                # 同时保存到单独的JSON文件（保持向后兼容）
                await self._save_token_to_file(email, token)
                
            else:
                # 检查是否有错误信息
                error_message = await self._check_for_errors(page)
                if error_message:
                    result['error'] = error_message
                else:
                    result['error'] = "登录成功但未能获取到token"
            
            # 保存页面截图用于调试
            await self._save_screenshot(page, email)
            
        except Exception as e:
            logger.error(f"注册过程发生错误: {str(e)}")
            result['error'] = str(e)
            
        return result
    
    async def _get_verification_code_async(self) -> Optional[str]:
        """异步获取验证码"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            self.email_handler.get_latest_verification_code
        )
    
    async def _extract_token(self, page: Page) -> Optional[str]:
        """从localStorage中提取token"""
        try:
            # 首先尝试获取'token'键 - 这是用户明确要求的
            token = await page.evaluate('() => localStorage.getItem("token")')
            if token:
                logger.info(f"找到token (键名: token): {token[:50]}...")
                return token
            
            logger.warning("localStorage中没有找到'token'键，这是正常的，因为Polyflow是Web3应用")
            
            # 如果没有找到'token'键，尝试其他可能的键名
            token_keys = [
                'authToken',
                'accessToken',
                'jwt',
                'auth_token',
                'user_token',
                'polyflow_token',
                'session_token'
            ]
            
            for key in token_keys:
                token = await page.evaluate(f'() => localStorage.getItem("{key}")')
                if token:
                    logger.info(f"找到token (键名: {key}): {token[:50]}...")
                    return token
            
            # 如果没有找到特定键名的token，获取所有localStorage内容进行分析
            all_storage = await page.evaluate('() => JSON.stringify(localStorage)')
            logger.info(f"localStorage内容: {all_storage}")
            
            # 检查是否有任何看起来像token的值
            storage_data = json.loads(all_storage)
            
            # 对于Polyflow这样的Web3应用，wagmi.store包含了用户的连接状态
            # 这实际上就是用户的"登录凭证"
            wagmi_store = storage_data.get('wagmi.store')
            if wagmi_store:
                logger.info("找到Web3钱包状态 (wagmi.store)，这是Polyflow的登录凭证")
                return wagmi_store
            
            # 首先查找JWT格式的token (必须包含两个点且长度大于20)
            for key, value in storage_data.items():
                if isinstance(value, str) and value.count('.') >= 2 and len(value) > 20:
                    logger.warning(f"找到可能的JWT token (键名: {key}): {value[:50]}...")
                    return value
            
            # 然后查找长字符串token (长度必须大于50)
            for key, value in storage_data.items():
                if isinstance(value, str) and len(value) > 50:
                    logger.warning(f"找到可能的长字符串token (键名: {key}): {value[:50]}...")
                    return value
            
            # 最后检查是否有JSON格式的复杂对象可能包含token信息
            for key, value in storage_data.items():
                if isinstance(value, str) and value.startswith('{') and len(value) > 30:
                    try:
                        parsed = json.loads(value)
                        if isinstance(parsed, dict):
                            logger.warning(f"找到可能的JSON token对象 (键名: {key}): {value[:50]}...")
                            return value
                    except:
                        continue
            
            logger.error("localStorage中没有找到任何看起来像token的值")
            return None
                        
        except Exception as e:
            logger.error(f"提取token时发生错误: {str(e)}")
            
        return None
    
    async def _save_token_to_file(self, email: str, token: str):
        """保存token到本地文件"""
        try:
            os.makedirs('data/tokens', exist_ok=True)
            
            token_data = {
                'email': email,
                'token': token,
                'timestamp': datetime.now().isoformat(),
                'site': 'polyflow.tech'
            }
            
            filename = f"data/tokens/{email.replace('@', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(token_data, f, indent=2, ensure_ascii=False)
                
            logger.info(f"Token已保存到: {filename}")
            
        except Exception as e:
            logger.error(f"保存token时发生错误: {str(e)}")
    
    async def _check_for_errors(self, page: Page) -> Optional[str]:
        """检查页面上的错误信息"""
        try:
            error_selectors = [
                '.error',
                '.alert-error',
                '.text-red',
                '[class*="error"]',
                '[class*="invalid"]'
            ]
            
            for selector in error_selectors:
                try:
                    error_element = await page.query_selector(selector)
                    if error_element:
                        error_text = await error_element.text_content()
                        if error_text and error_text.strip():
                            return error_text.strip()
                except:
                    continue
                    
        except Exception as e:
            logger.error(f"检查错误信息时发生异常: {str(e)}")
            
        return None
    
    async def _save_screenshot(self, page: Page, email: str):
        """保存页面截图用于调试"""
        try:
            os.makedirs('data/screenshots', exist_ok=True)
            
            filename = f"data/screenshots/{email.replace('@', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            await page.screenshot(path=filename, full_page=True)
            
            logger.info(f"页面截图已保存: {filename}")
            
        except Exception as e:
            logger.error(f"保存截图时发生错误: {str(e)}") 