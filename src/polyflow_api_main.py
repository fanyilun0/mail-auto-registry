import asyncio
import sys
import os
from loguru import logger
from email_handler import EmailHandler
from polyflow.polyflow_api_client import PolyflowAPIClient

# 配置日志
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO"
)
logger.add(
    "logs/polyflow_api_{time:YYYY-MM-DD}.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="DEBUG",
    rotation="1 day",
    retention="7 days"
)

async def main():
    """主程序入口"""
    try:
        logger.info("=== Polyflow API自动注册程序启动 ===")
        
        # 初始化邮件处理器
        email_handler = EmailHandler()
        
        # 加载代理列表（可选）
        proxy_list_path = os.path.join(os.path.dirname(__file__), "../src/polyflow/proxies.txt")
        proxy_list = PolyflowAPIClient.load_proxy_list(proxy_list_path)
        if proxy_list:
            logger.info(f"加载了 {len(proxy_list)} 个代理")
        else:
            logger.info("未使用代理，将直接连接")
        
        # 使用异步上下文管理器创建API客户端
        async with PolyflowAPIClient(email_handler, proxy_list) as api_client:
            
            # 加载邮箱列表
            email_list_path = os.path.join(os.path.dirname(__file__), "../src/polyflow/email.txt")
            emails = api_client.load_email_list(email_list_path)
            if not emails:
                logger.error("没有找到可用的邮箱地址")
                return
            
            logger.info(f"准备注册 {len(emails)} 个账号")
            
            # 可选：设置推荐码
            referral_code = ""  # 如果有推荐码可以在这里设置
            
            # 执行批量注册
            results = await api_client.batch_register(
                emails=emails,
                referral_code=referral_code,
                delay_between_requests=15  # 请求间隔15秒，避免频率限制
            )
            
            # 输出最终统计
            successful = [r for r in results if r['success']]
            failed = [r for r in results if not r['success']]
            
            logger.info("=== 批量注册完成 ===")
            logger.info(f"总计处理: {len(results)} 个邮箱")
            logger.info(f"注册成功: {len(successful)} 个")
            logger.info(f"注册失败: {len(failed)} 个")
            logger.info(f"成功率: {len(successful)/len(results)*100:.1f}%")
            
            if successful:
                logger.info("成功注册的邮箱:")
                for result in successful:
                    logger.info(f"  ✅ {result['email']}")
            
            if failed:
                logger.info("注册失败的邮箱:")
                for result in failed:
                    logger.info(f"  ❌ {result['email']}: {result['error']}")
        
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
    except Exception as e:
        logger.error(f"程序执行过程中发生错误: {str(e)}")
    finally:
        logger.info("程序结束")

if __name__ == "__main__":
    # 运行批量注册
    asyncio.run(main()) 