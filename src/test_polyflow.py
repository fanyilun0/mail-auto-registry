#!/usr/bin/env python3
"""
Polyflow网站注册功能测试脚本
"""

import asyncio
import os
import sys
from loguru import logger
from dotenv import load_dotenv

# 添加src目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import AutoRegistry

async def test_polyflow_registration():
    """测试Polyflow网站注册功能"""
    
    # 加载环境变量
    load_dotenv()
    
    # 检查必要的环境变量
    required_env_vars = ['EMAIL_USERNAME', 'EMAIL_PASSWORD']
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"缺少必要的环境变量: {', '.join(missing_vars)}")
        logger.error("请在.env文件中设置EMAIL_USERNAME和EMAIL_PASSWORD")
        return False
    
    # 获取测试邮箱
    test_email = os.getenv('TEST_EMAIL')
    if not test_email:
        logger.warning("未设置TEST_EMAIL环境变量，使用默认测试邮箱")
        test_email = os.getenv('EMAIL_USERNAME')  # 使用配置的邮箱作为测试邮箱
    
    logger.info(f"开始测试Polyflow注册功能")
    logger.info(f"测试邮箱: {test_email}")
    
    # 创建注册器实例
    registry = None
    
    try:
        registry = AutoRegistry()
        
        # 执行注册测试
        logger.info("🚀 开始执行Polyflow注册流程...")
        result = await registry.register_polyflow_account(test_email)
        
        # 输出结果
        logger.info("=" * 50)
        logger.info("📊 注册结果报告")
        logger.info("=" * 50)
        
        if result['success']:
            logger.info("✅ 注册状态: 成功")
            logger.info(f"📧 邮箱地址: {result['email']}")
            logger.info(f"🔑 获取Token: {'是' if result['token'] else '否'}")
            if result['token']:
                logger.info(f"🔐 Token预览: {result['token'][:50]}...")
            logger.info(f"⏰ 完成时间: {result['timestamp']}")
            
            # 检查保存的文件
            logger.info("\n📁 生成的文件:")
            
            # 检查token文件
            token_dir = "data/tokens"
            if os.path.exists(token_dir):
                token_files = [f for f in os.listdir(token_dir) if f.endswith('.json')]
                if token_files:
                    latest_token_file = max(token_files, key=lambda x: os.path.getctime(os.path.join(token_dir, x)))
                    logger.info(f"  🔑 Token文件: {latest_token_file}")
            
            # 检查截图文件
            screenshot_dir = "data/screenshots"
            if os.path.exists(screenshot_dir):
                screenshot_files = [f for f in os.listdir(screenshot_dir) if f.endswith('.png')]
                if screenshot_files:
                    latest_screenshot = max(screenshot_files, key=lambda x: os.path.getctime(os.path.join(screenshot_dir, x)))
                    logger.info(f"  📸 截图文件: {latest_screenshot}")
            
        else:
            logger.error("❌ 注册状态: 失败")
            logger.error(f"📧 邮箱地址: {result['email']}")
            logger.error(f"❗ 错误信息: {result['error']}")
            logger.error(f"⏰ 失败时间: {result['timestamp']}")
        
        logger.info("=" * 50)
        
        return result['success']
        
    except Exception as e:
        logger.error(f"测试过程中发生异常: {str(e)}")
        return False
        
    finally:
        # 确保资源被正确关闭
        if registry:
            try:
                await registry.close()
                logger.info("🔒 资源已清理完成")
            except Exception as e:
                logger.error(f"清理资源时发生错误: {str(e)}")

async def main():
    """主函数"""
    logger.info("🧪 Polyflow注册功能测试开始")
    
    success = await test_polyflow_registration()
    
    if success:
        logger.info("🎉 测试完成 - 注册成功!")
        sys.exit(0)
    else:
        logger.error("💥 测试完成 - 注册失败!")
        sys.exit(1)

if __name__ == "__main__":
    # 配置日志格式
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO"
    )
    
    # 运行测试
    asyncio.run(main()) 