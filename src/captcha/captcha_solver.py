from twocaptcha import TwoCaptcha
from typing import Optional, Dict
import os
from loguru import logger
import yaml
from dotenv import load_dotenv
import base64
import time

class CaptchaSolver:
    def __init__(self, config_path: str = "config.yaml"):
        self.config = self._load_config(config_path)
        load_dotenv()
        self.solver = TwoCaptcha(os.getenv('CAPTCHA_API_KEY'))
        
    def _load_config(self, config_path: str) -> dict:
        """加载配置文件"""
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)['captcha']
    
    async def solve_recaptcha(self, site_key: str, url: str) -> Optional[str]:
        """解决reCAPTCHA"""
        try:
            result = self.solver.recaptcha(
                sitekey=site_key,
                url=url
            )
            logger.info("reCAPTCHA解决成功")
            return result['code']
        except Exception as e:
            logger.error(f"reCAPTCHA解决失败: {str(e)}")
            return None
    
    async def solve_image_captcha(self, image_path: str) -> Optional[str]:
        """解决图片验证码"""
        try:
            with open(image_path, 'rb') as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
            
            result = self.solver.normal(
                image_data,
                case_sensitive=True
            )
            logger.info("图片验证码解决成功")
            return result['code']
        except Exception as e:
            logger.error(f"图片验证码解决失败: {str(e)}")
            return None
    
    async def solve_hcaptcha(self, site_key: str, url: str) -> Optional[str]:
        """解决hCaptcha"""
        try:
            result = self.solver.hcaptcha(
                sitekey=site_key,
                url=url
            )
            logger.info("hCaptcha解决成功")
            return result['code']
        except Exception as e:
            logger.error(f"hCaptcha解决失败: {str(e)}")
            return None
    
    def get_balance(self) -> float:
        """获取账户余额"""
        try:
            balance = self.solver.balance()
            logger.info(f"账户余额: {balance}")
            return float(balance)
        except Exception as e:
            logger.error(f"获取余额失败: {str(e)}")
            return 0.0 