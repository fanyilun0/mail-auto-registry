# Polyflow自动注册功能设置指南

## 功能概述

本项目新增了针对 https://app.polyflow.tech/ 网站的自动注册功能，可以自动完成以下流程：

1. 访问Polyflow网站
2. 输入邮箱地址
3. 点击发送验证码
4. 自动获取邮件中的验证码
5. 输入验证码完成登录
6. 提取并保存localStorage中的token

## 环境配置

### 1. 创建.env文件

在项目根目录创建`.env`文件，包含以下配置：

```bash
# 邮箱配置 - 用于接收验证码
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password

# 测试邮箱 - 用于注册测试（可选，默认使用EMAIL_USERNAME）
TEST_EMAIL=your_test_email@gmail.com

# 验证码服务API密钥（可选）
CAPTCHA_API_KEY=your_2captcha_api_key
```

### 2. Gmail应用密码设置

如果使用Gmail，需要：
1. 启用两步验证
2. 生成应用密码
3. 使用应用密码作为EMAIL_PASSWORD

### 3. 安装依赖

```bash
pip install -r requirements.txt
playwright install chromium
```

## 使用方法

### 方法1：使用测试脚本

```bash
cd src
python test_polyflow.py
```

### 方法2：使用主程序

```bash
cd src
python main.py
```

### 方法3：编程调用

```python
from main import AutoRegistry

async def register_polyflow():
    registry = AutoRegistry()
    
    result = await registry.register_polyflow_account("test@example.com")
    
    if result['success']:
        print(f"注册成功，Token: {result['token']}")
    else:
        print(f"注册失败: {result['error']}")
    
    await registry.close()
```

## 输出文件

成功执行后会生成以下文件：

- `data/tokens/` - 保存提取的token信息
- `data/screenshots/` - 保存页面截图用于调试
- `logs/app.log` - 详细的执行日志

## 配置选项

在`config.yaml`中可以调整：

- 浏览器设置（是否无头模式）
- 代理配置
- 超时时间
- 日志级别

## 故障排除

### 常见问题

1. **邮件连接失败**
   - 检查EMAIL_USERNAME和EMAIL_PASSWORD是否正确
   - 确认Gmail应用密码设置正确

2. **页面元素找不到**
   - 网站可能更新了DOM结构
   - 检查截图文件确认页面状态

3. **验证码获取超时**
   - 检查邮件服务器连接
   - 确认邮件没有被过滤到垃圾邮件

4. **Token提取失败**
   - 网站可能使用了不同的token存储方式
   - 检查浏览器控制台和localStorage内容

### 调试模式

设置`config.yaml`中的`browser.headless: false`可以看到浏览器操作过程。

## 模块结构

```
src/
├── sites/
│   ├── __init__.py
│   └── polyflow_registry.py    # Polyflow专用注册器
├── main.py                     # 主程序
├── test_polyflow.py           # 测试脚本
└── ...
```

## 扩展其他网站

基于`PolyflowRegistry`的设计模式，可以轻松扩展支持其他网站：

1. 在`src/sites/`目录创建新的注册器类
2. 在`main.py`中添加对应的方法
3. 创建专用的测试脚本

## 安全注意事项

- 不要将.env文件提交到版本控制
- 定期更换邮箱应用密码
- 谨慎使用代理服务
- 遵守目标网站的使用条款 