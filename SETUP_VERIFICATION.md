# 邮箱自动注册工具 - 安装验证指南

本文档提供逐步验证指南，确保项目的所有功能组件都能正常工作。

## 前置要求检查

### 1. Python 版本检查
```bash
python3 --version
# 应该显示 Python 3.8+ (推荐 3.11 或 3.12，避免 3.13)
```

### 2. 系统依赖检查 (macOS)
```bash
# 检查是否安装了必要的开发工具
xcode-select --install
```

## 环境设置验证

### 步骤 1: 虚拟环境创建
```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 验证虚拟环境
which python
# 应该显示项目目录下的 venv/bin/python
```

### 步骤 2: 依赖安装验证
```bash
# 升级pip
pip install --upgrade pip

# 安装依赖
pip install -r requirements.txt

# 验证关键包安装
python -c "import playwright; print('Playwright installed successfully')"
python -c "import yaml; print('PyYAML installed successfully')"
python -c "import aiohttp; print('aiohttp installed successfully')"
```

### 步骤 3: Playwright 浏览器安装
```bash
# 安装浏览器
playwright install

# 验证浏览器安装
playwright install --dry-run
```

## 配置文件验证

### 步骤 4: 环境变量配置
```bash
# 创建 .env 文件
cat > .env << EOF
EMAIL_USERNAME=your_email@proton.me
EMAIL_PASSWORD=your_email_password
CAPTCHA_API_KEY=your_2captcha_api_key
EOF

# 验证环境变量加载
python -c "
from dotenv import load_dotenv
import os
load_dotenv()
print('EMAIL_USERNAME:', os.getenv('EMAIL_USERNAME'))
print('CAPTCHA_API_KEY:', 'Set' if os.getenv('CAPTCHA_API_KEY') else 'Not set')
"
```

### 步骤 5: 配置文件验证
```bash
# 验证 config.yaml 语法
python -c "
import yaml
with open('config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)
print('Config loaded successfully')
print('Proxy enabled:', config['proxy']['enabled'])
print('Browser headless:', config['browser']['headless'])
"
```

## 功能模块验证

### 步骤 6: 代理管理模块验证
```bash
# 测试代理管理器
python -c "
import asyncio
import sys
sys.path.append('src')
from proxy.proxy_manager import ProxyManager

async def test_proxy():
    manager = ProxyManager()
    print('ProxyManager created successfully')
    # 这里可以添加更多测试

asyncio.run(test_proxy())
"
```

### 步骤 7: 浏览器管理模块验证
```bash
# 测试浏览器管理器
python -c "
import asyncio
import sys
sys.path.append('src')
from browser.browser_manager import BrowserManager

async def test_browser():
    manager = BrowserManager()
    print('BrowserManager created successfully')
    await manager.close()

asyncio.run(test_browser())
"
```

### 步骤 8: 邮件处理模块验证
```bash
# 测试邮件处理器（需要真实邮箱配置）
python -c "
import sys
sys.path.append('src')
from email.email_handler import EmailHandler

handler = EmailHandler()
print('EmailHandler created successfully')
"
```

### 步骤 9: 验证码服务验证
```bash
# 测试验证码服务（需要API密钥）
python -c "
import sys
sys.path.append('src')
from captcha.captcha_solver import CaptchaSolver

solver = CaptchaSolver()
print('CaptchaSolver created successfully')
"
```

## 集成测试

### 步骤 10: 主程序启动测试
```bash
# 测试主程序导入
python -c "
import sys
sys.path.append('src')
from main import AutoRegistry
print('AutoRegistry imported successfully')
"
```

### 步骤 11: 配置加载测试
```bash
# 完整配置加载测试
python src/main.py --test-config
```

## 日志系统验证

### 步骤 12: 日志目录和文件
```bash
# 检查日志目录
ls -la logs/

# 测试日志写入
python -c "
from loguru import logger
logger.add('logs/test.log')
logger.info('Test log message')
print('Log test completed')
"

# 检查日志文件
cat logs/test.log
```

## 网络连接验证

### 步骤 13: 网络连接测试
```bash
# 测试基本网络连接
python -c "
import aiohttp
import asyncio

async def test_connection():
    async with aiohttp.ClientSession() as session:
        async with session.get('https://httpbin.org/ip') as response:
            print('Network test successful:', await response.json())

asyncio.run(test_connection())
"
```

## 故障排除

### 常见问题及解决方案

#### 1. greenlet 编译错误
```bash
# 如果遇到 greenlet 编译问题，使用预编译版本
pip install --only-binary=greenlet greenlet
```

#### 2. Playwright 浏览器下载失败
```bash
# 手动下载浏览器
PLAYWRIGHT_BROWSERS_PATH=0 playwright install chromium
```

#### 3. 权限问题
```bash
# 修复权限
chmod +x venv/bin/*
```

#### 4. 代理连接问题
```bash
# 测试代理连接
curl --proxy http://your-proxy:port https://httpbin.org/ip
```

## 验证清单

完成以下检查项：

- [ ] Python 版本正确 (3.8+)
- [ ] 虚拟环境创建成功
- [ ] 所有依赖包安装成功
- [ ] Playwright 浏览器安装完成
- [ ] 环境变量配置正确
- [ ] config.yaml 语法正确
- [ ] 代理管理模块可导入
- [ ] 浏览器管理模块可导入
- [ ] 邮件处理模块可导入
- [ ] 验证码服务模块可导入
- [ ] 主程序可导入
- [ ] 日志系统工作正常
- [ ] 网络连接正常

## 下一步

验证完成后，您可以：

1. 配置真实的邮箱账户信息
2. 获取 2Captcha API 密钥
3. 配置代理服务器（如需要）
4. 开始使用自动注册功能

## 技术支持

如果在验证过程中遇到问题：

1. 检查错误日志：`tail -f logs/app.log`
2. 确认所有环境变量已正确设置
3. 验证网络连接和代理配置
4. 查看项目 Issues 或提交新的问题报告 