# 邮箱自动注册工具

这是一个基于Python的自动化邮箱注册工具，支持代理管理、浏览器自动化、验证码处理等功能。

## 功能特点

- 代理管理
  - 支持HTTP和Socks5代理
  - 自动代理轮换
  - 代理可用性检测

- 浏览器自动化
  - 基于Playwright实现
  - 支持多浏览器实例池
  - 自动化特征隐藏

- 邮件验证码处理
  - 支持IMAP协议
  - 自动提取验证码
  - 验证码缓存机制

- 验证码识别
  - 集成2Captcha服务
  - 支持多种验证码类型

## 安装要求

- Python 3.8+
- 依赖包（见requirements.txt）

## 快速开始

1. 克隆仓库
```bash
git clone https://github.com/yourusername/mail-auto-registry.git
cd mail-auto-registry
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 配置环境变量
创建.env文件并设置以下变量：
```
EMAIL_USERNAME=your_email@proton.me
EMAIL_PASSWORD=your_email_password
CAPTCHA_API_KEY=your_2captcha_api_key
```

4. 配置代理
在config.yaml中配置代理信息：
```yaml
proxy:
  enabled: true
  type: http
  rotation_interval: 300
```

5. 运行程序
```bash
python src/main.py
```

## 配置说明

### config.yaml

```yaml
# 代理配置
proxy:
  enabled: true
  type: http
  rotation_interval: 300
  check_timeout: 10

# 浏览器配置
browser:
  headless: false
  timeout: 30000
  pool_size: 3

# 验证码配置
captcha:
  service: 2captcha
  timeout: 120

# 邮箱配置
email:
  provider: proton.me
  imap_server: imap.proton.me
  imap_port: 993
```

## 使用示例

```python
from src.main import AutoRegistry

async def main():
    registry = AutoRegistry()
    
    success = await registry.register_account(
        target_url="https://example.com/register",
        email="test@example.com",
        password="YourPassword123"
    )
    
    await registry.close()

if __name__ == "__main__":
    asyncio.run(main())
```

## 注意事项

1. 请确保代理服务器可用
2. 建议使用付费的2Captcha服务以提高验证码识别成功率
3. 注意遵守目标网站的使用条款和注册限制
4. 建议适当设置请求延迟，避免触发反爬虫机制

## 目录结构

```
mail-auto-registry/
├── src/
│   ├── proxy/
│   │   └── proxy_manager.py
│   ├── browser/
│   │   └── browser_manager.py
│   ├── email/
│   │   └── email_handler.py
│   ├── captcha/
│   │   └── captcha_solver.py
│   └── main.py
├── config.yaml
├── requirements.txt
├── .env
└── README.md
```

## 贡献指南

欢迎提交Issue和Pull Request来帮助改进这个项目。

## 许可证

MIT License 