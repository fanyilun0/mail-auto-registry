#!/usr/bin/env python3
"""
基本功能验证脚本 - 不需要真实的邮箱配置
"""

import asyncio
import os
import sys
from loguru import logger

# 添加src目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """测试模块导入"""
    try:
        from main import AutoRegistry
        from sites.polyflow_registry import PolyflowRegistry
        from browser.browser_manager import BrowserManager
        from email_handler import EmailHandler
        logger.info("✅ 所有模块导入成功")
        return True
    except ImportError as e:
        logger.error(f"❌ 模块导入失败: {e}")
        return False

def test_config_loading():
    """测试配置文件加载"""
    try:
        import yaml
        with open('../config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        logger.info("✅ 配置文件加载成功")
        logger.info(f"浏览器配置: headless={config['browser']['headless']}")
        return True
    except Exception as e:
        logger.error(f"❌ 配置文件加载失败: {e}")
        return False

async def test_browser_initialization():
    """测试浏览器初始化（不访问网站）"""
    try:
        from browser.browser_manager import BrowserManager
        
        browser_manager = BrowserManager('../config.yaml')
        await browser_manager.initialize()
        
        # 获取页面但不访问任何网站
        page = await browser_manager.get_page()
        
        if page:
            logger.info("✅ 浏览器初始化成功")
            await browser_manager.close()
            return True
        else:
            logger.error("❌ 无法获取浏览器页面")
            return False
            
    except Exception as e:
        logger.error(f"❌ 浏览器初始化失败: {e}")
        return False

async def test_polyflow_registry_creation():
    """测试Polyflow注册器创建"""
    try:
        from browser.browser_manager import BrowserManager
        from email_handler import EmailHandler
        from sites.polyflow_registry import PolyflowRegistry
        
        # 创建依赖对象（不连接真实服务）
        browser_manager = BrowserManager('../config.yaml')
        email_handler = EmailHandler('../config.yaml')
        
        # 创建Polyflow注册器
        polyflow_registry = PolyflowRegistry(browser_manager, email_handler)
        
        logger.info("✅ Polyflow注册器创建成功")
        logger.info(f"目标URL: {polyflow_registry.base_url}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Polyflow注册器创建失败: {e}")
        return False

async def main():
    """主测试函数"""
    logger.info("🧪 开始基本功能验证")
    logger.info("=" * 50)
    
    tests = [
        ("模块导入测试", test_imports),
        ("配置文件加载测试", test_config_loading),
        ("浏览器初始化测试", test_browser_initialization),
        ("Polyflow注册器创建测试", test_polyflow_registry_creation),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n🔍 执行: {test_name}")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            
            if result:
                passed += 1
                logger.info(f"✅ {test_name} - 通过")
            else:
                logger.error(f"❌ {test_name} - 失败")
                
        except Exception as e:
            logger.error(f"❌ {test_name} - 异常: {e}")
    
    logger.info("=" * 50)
    logger.info(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        logger.info("🎉 所有基本功能验证通过！")
        logger.info("💡 提示: 要进行完整测试，请配置.env文件中的邮箱设置")
        return True
    else:
        logger.error("💥 部分功能验证失败")
        return False

if __name__ == "__main__":
    # 配置日志格式
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )
    
    # 运行测试
    success = asyncio.run(main())
    sys.exit(0 if success else 1)