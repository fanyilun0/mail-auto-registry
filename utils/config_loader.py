#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置加载器模块

支持从YAML文件加载配置，并自动处理环境变量替换
支持.env文件和系统环境变量
"""

import os
import re
import yaml
from pathlib import Path
from typing import Dict, Any, Union
from loguru import logger

class ConfigLoader:
    """配置加载器类"""
    
    def __init__(self, config_path: Union[str, Path], env_file: Union[str, Path] = None):
        """
        初始化配置加载器
        
        Args:
            config_path: YAML配置文件路径
            env_file: .env文件路径，默认为项目根目录下的.env
        """
        self.config_path = Path(config_path)
        
        # 确定.env文件路径
        if env_file:
            self.env_file = Path(env_file)
        else:
            # 默认在配置文件同级目录或项目根目录查找.env
            project_root = self.config_path.parent
            self.env_file = project_root / ".env"
        
        # 加载.env文件
        self._load_env_file()
    
    def _load_env_file(self):
        """加载.env文件中的环境变量"""
        if not self.env_file.exists():
            logger.info(f".env文件不存在: {self.env_file}")
            return
        
        try:
            with open(self.env_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    
                    # 跳过空行和注释行
                    if not line or line.startswith('#'):
                        continue
                    
                    # 解析环境变量
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # 移除引号
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        elif value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]
                        
                        # 设置环境变量（如果尚未设置）
                        if key not in os.environ:
                            os.environ[key] = value
                            logger.debug(f"从.env加载环境变量: {key}")
                        else:
                            logger.debug(f"环境变量已存在，跳过: {key}")
                    else:
                        logger.warning(f".env文件第{line_num}行格式错误: {line}")
            
            logger.info(f"成功加载.env文件: {self.env_file}")
            
        except Exception as e:
            logger.error(f"加载.env文件失败: {str(e)}")
    
    def _replace_env_vars(self, obj: Any) -> Any:
        """
        递归替换配置中的环境变量
        
        支持格式:
        - ${VAR_NAME}
        - ${VAR_NAME:default_value}
        
        Args:
            obj: 要处理的对象
            
        Returns:
            处理后的对象
        """
        if isinstance(obj, dict):
            return {key: self._replace_env_vars(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._replace_env_vars(item) for item in obj]
        elif isinstance(obj, str):
            return self._replace_string_env_vars(obj)
        else:
            return obj
    
    def _replace_string_env_vars(self, text: str) -> str:
        """
        替换字符串中的环境变量
        
        Args:
            text: 包含环境变量的字符串
            
        Returns:
            替换后的字符串
        """
        # 匹配 ${VAR_NAME} 或 ${VAR_NAME:default_value} 格式
        pattern = r'\$\{([^}:]+)(?::([^}]*))?\}'
        
        def replace_match(match):
            var_name = match.group(1)
            default_value = match.group(2) if match.group(2) is not None else ""
            
            # 获取环境变量值
            env_value = os.getenv(var_name)
            
            if env_value is not None:
                logger.debug(f"替换环境变量: {var_name} = {env_value}")
                return env_value
            elif default_value:
                logger.debug(f"使用默认值: {var_name} = {default_value}")
                return default_value
            else:
                logger.warning(f"环境变量未设置且无默认值: {var_name}")
                return match.group(0)  # 返回原始字符串
        
        return re.sub(pattern, replace_match, text)
    
    def load_config(self) -> Dict[str, Any]:
        """
        加载配置文件并处理环境变量
        
        Returns:
            处理后的配置字典
        """
        try:
            # 读取YAML配置文件
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            if not config:
                logger.warning("配置文件为空")
                return {}
            
            # 替换环境变量
            config = self._replace_env_vars(config)
            
            logger.info(f"配置文件加载成功: {self.config_path}")
            return config
            
        except FileNotFoundError:
            logger.error(f"配置文件不存在: {self.config_path}")
            raise
        except yaml.YAMLError as e:
            logger.error(f"配置文件格式错误: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"加载配置文件失败: {str(e)}")
            raise
    
    def get_email_config(self) -> Dict[str, Any]:
        """
        获取邮件配置
        
        Returns:
            邮件配置字典
        """
        config = self.load_config()
        email_config = config.get('email', {})
        
        # 验证必要的配置项
        username = email_config.get('username')
        password = email_config.get('password')
        
        if not username:
            raise ValueError("邮箱用户名未配置，请设置环境变量 EMAIL_USERNAME")
        
        if not password:
            raise ValueError("邮箱密码未配置，请设置环境变量 EMAIL_PASSWORD")
        
        # 检查是否还包含未替换的环境变量
        if username.startswith('${') or password.startswith('${'):
            logger.error("环境变量未正确替换:")
            logger.error(f"  username: {username}")
            logger.error(f"  password: {password}")
            raise ValueError("环境变量配置错误，请检查.env文件或系统环境变量")
        
        logger.info(f"邮件配置加载成功: {username}")
        return email_config
    
    def get_timezone_config(self) -> Dict[str, Any]:
        """
        获取时区配置
        
        Returns:
            时区配置字典
        """
        config = self.load_config()
        timezone_config = config.get('timezone', {})
        
        # 设置默认值
        default_timezone_config = {
            'local_timezone': 'Asia/Shanghai',
            'utc_offset_hours': 8
        }
        
        # 合并默认配置
        for key, default_value in default_timezone_config.items():
            if key not in timezone_config:
                timezone_config[key] = default_value
        
        logger.info(f"时区配置加载成功: {timezone_config['local_timezone']} (UTC{timezone_config['utc_offset_hours']:+d})")
        return timezone_config

def load_config_with_env(config_path: Union[str, Path], env_file: Union[str, Path] = None) -> Dict[str, Any]:
    """
    便捷函数：加载配置文件并处理环境变量
    
    Args:
        config_path: YAML配置文件路径
        env_file: .env文件路径（可选）
        
    Returns:
        处理后的配置字典
    """
    loader = ConfigLoader(config_path, env_file)
    return loader.load_config()

def load_email_config(config_path: Union[str, Path], env_file: Union[str, Path] = None) -> Dict[str, Any]:
    """
    便捷函数：加载邮件配置
    
    Args:
        config_path: YAML配置文件路径
        env_file: .env文件路径（可选）
        
    Returns:
        邮件配置字典
    """
    loader = ConfigLoader(config_path, env_file)
    return loader.get_email_config() 