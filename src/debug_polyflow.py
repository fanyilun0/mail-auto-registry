#!/usr/bin/env python3
"""
Polyflow网站DOM结构调试脚本
"""

import asyncio
import os
import sys
from loguru import logger

# 添加src目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from browser.browser_manager import BrowserManager

async def debug_polyflow_page():
    """调试Polyflow页面结构"""
    
    browser_manager = BrowserManager('../config.yaml')
    
    try:
        # 初始化浏览器
        await browser_manager.initialize()
        page = await browser_manager.get_page()
        
        # 访问Polyflow网站
        logger.info("正在访问 https://app.polyflow.tech/")
        await page.goto("https://app.polyflow.tech/")
        
        # 等待页面加载
        await page.wait_for_load_state('networkidle')
        
        # 获取页面标题
        title = await page.title()
        logger.info(f"页面标题: {title}")
        
        # 获取页面URL
        current_url = page.url
        logger.info(f"当前URL: {current_url}")
        
        # 查找所有输入框
        logger.info("查找页面中的所有输入框:")
        inputs = await page.query_selector_all('input')
        for i, input_elem in enumerate(inputs):
            input_type = await input_elem.get_attribute('type')
            placeholder = await input_elem.get_attribute('placeholder')
            name = await input_elem.get_attribute('name')
            id_attr = await input_elem.get_attribute('id')
            class_attr = await input_elem.get_attribute('class')
            
            logger.info(f"  输入框 {i+1}:")
            logger.info(f"    type: {input_type}")
            logger.info(f"    placeholder: {placeholder}")
            logger.info(f"    name: {name}")
            logger.info(f"    id: {id_attr}")
            logger.info(f"    class: {class_attr}")
        
        # 查找所有按钮
        logger.info("查找页面中的所有按钮:")
        buttons = await page.query_selector_all('button')
        for i, button in enumerate(buttons):
            text = await button.text_content()
            type_attr = await button.get_attribute('type')
            class_attr = await button.get_attribute('class')
            
            logger.info(f"  按钮 {i+1}:")
            logger.info(f"    text: {text}")
            logger.info(f"    type: {type_attr}")
            logger.info(f"    class: {class_attr}")
        
        # 保存页面截图
        os.makedirs('../data/debug', exist_ok=True)
        screenshot_path = '../data/debug/polyflow_debug.png'
        await page.screenshot(path=screenshot_path, full_page=True)
        logger.info(f"页面截图已保存: {screenshot_path}")
        
        # 保存页面HTML
        html_content = await page.content()
        html_path = '../data/debug/polyflow_debug.html'
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        logger.info(f"页面HTML已保存: {html_path}")
        
        # 等待一段时间以便观察（如果是非无头模式）
        await page.wait_for_timeout(5000)
        
    except Exception as e:
        logger.error(f"调试过程发生错误: {str(e)}")
        
    finally:
        await browser_manager.close()

async def main():
    """主函数"""
    logger.info("🔍 开始调试Polyflow网站页面结构")
    await debug_polyflow_page()
    logger.info("🔍 调试完成")

if __name__ == "__main__":
    # 配置日志格式
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )
    
    # 运行调试
    asyncio.run(main()) 