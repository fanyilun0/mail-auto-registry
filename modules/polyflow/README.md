# Polyflow自动注册工具

一个功能完整的邮箱自动注册工具，支持Gmail IMAP连接、代理管理和验证码自动提取。

## 🚀 主要功能

### 核心特性
- ✅ **真实Gmail连接**: 直接使用IMAP协议连接Gmail
- ✅ **智能验证码提取**: 多种匹配模式，自动识别验证码
- ✅ **代理管理**: 支持HTTP/SOCKS5代理，自动轮换
- ✅ **批量注册**: 支持多邮箱批量处理
- ✅ **完整日志**: 详细的操作日志和错误追踪

### 技术亮点
- 🔧 **模块化设计**: 清晰的代码结构，易于维护
- 🛡️ **安全配置**: 环境变量管理敏感信息
- 📊 **详细报告**: 自动生成注册结果报告
- 🔄 **自动重试**: 智能重试机制，提高成功率

## 📋 系统要求

### 环境依赖
- Python 3.8+
- Gmail账号（需要应用密码）
- 网络连接

### Python包依赖
```bash
pip install -r requirements.txt
```

主要依赖包：
- `aiohttp` - 异步HTTP客户端
- `loguru` - 日志管理
- `pyyaml` - 配置文件解析
- `imaplib` - Gmail IMAP连接（Python内置）

## 🛠️ 安装配置

### 1. 克隆项目
```bash
git clone <repository-url>
cd mail-auto-registry
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 配置Gmail应用密码

#### 步骤1: 启用两步验证
1. 登录Gmail账号
2. 前往 [Google账号安全设置](https://myaccount.google.com/security)
3. 启用"两步验证"

#### 步骤2: 生成应用密码
1. 在安全设置中找到"应用密码"
2. 选择"邮件"和"其他设备"
3. 生成16位应用密码

#### 步骤3: 设置环境变量
```bash
# 设置Gmail凭据
export EMAIL_USERNAME="your-email@gmail.com"
export EMAIL_PASSWORD="your-16-digit-app-password"
```

### 4. 配置邮箱列表
编辑 `modules/polyflow/email.txt`：
```
email1@example.com
email2@example.com
# 注释行以#开头
```

### 5. 配置代理（可选）
编辑 `modules/polyflow/proxies.txt`：
```
127.0.0.1:7890
http://127.0.0.1:8080
http://user:pass@proxy.example.com:3128
```

## 🚀 使用方法

### 快速开始
```bash
# 基本使用（从任意目录执行）
./modules/polyflow/start.sh

# 或者从项目根目录
cd /path/to/mail-auto-registry
./modules/polyflow/start.sh
```

### 运行模式

#### 1. 批量注册模式（默认）
```bash
./modules/polyflow/start.sh
# 或
./modules/polyflow/start.sh --batch
```

#### 2. 单个注册模式
```bash
./modules/polyflow/start.sh --single
```

#### 3. 测试模式
```bash
./modules/polyflow/start.sh --test
```

#### 4. 环境检查
```bash
./modules/polyflow/start.sh --check
```

#### 5. 帮助信息
```bash
./modules/polyflow/start.sh --help
```

### 测试Gmail连接
```bash
# 设置环境变量后测试Gmail连接
python3 test_gmail.py
```

### 运行完整测试
```bash
./modules/polyflow/test.sh
```

## 📁 项目结构

```
mail-auto-registry/
├── gmail/                          # Gmail邮件处理模块
│   ├── __init__.py
│   └── email_handler.py            # Gmail IMAP连接和验证码提取
├── proxy/                          # 代理管理模块
│   └── proxy_manager.py            # 代理轮换和检测
├── modules/polyflow/               # Polyflow注册模块
│   ├── __init__.py
│   ├── main.py                     # 主程序入口
│   ├── polyflow_api_client.py      # API客户端
│   ├── start.sh                    # 启动脚本
│   ├── test.sh                     # 测试脚本
│   ├── email.txt                   # 邮箱列表
│   ├── proxies.txt                 # 代理列表
│   └── README.md                   # 使用说明
├── config.yaml                     # 主配置文件
├── test_gmail.py                   # Gmail连接测试
└── requirements.txt                # Python依赖
```

## ⚙️ 配置说明

### config.yaml 主要配置项

```yaml
# 邮箱配置
email:
  provider: gmail.com
  imap_server: imap.gmail.com
  imap_port: 993
  username: ${EMAIL_USERNAME}        # 环境变量
  password: ${EMAIL_PASSWORD}        # 环境变量
  auth_method: app_password
  timeout: 120

# 代理配置
proxy:
  enabled: false                     # 是否启用代理
  type: http                         # 代理类型: http/socks5
  rotation_interval: 300             # 轮换间隔（秒）
  check_timeout: 10                  # 检测超时（秒）

# 安全配置
security:
  request_delay: 2                   # 请求间隔（秒）
  max_retries: 3                     # 最大重试次数
  retry_delay: 5                     # 重试延迟（秒）

# 日志配置
logging:
  level: INFO                        # 日志级别
  rotation: "1 day"                  # 日志轮换
  retention: "7 days"                # 日志保留
```

## 📊 输出结果

### 日志文件
- `logs/polyflow_main.log` - 主程序日志
- `logs/polyflow_api_*.log` - API调用日志

### 报告文件
- `data/reports/polyflow_batch_report_*.json` - 批量注册报告

### 示例报告格式
```json
{
  "timestamp": "2025-05-30T22:50:29",
  "total_emails": 2,
  "successful": 0,
  "failed": 2,
  "success_rate": 0.0,
  "results": [
    {
      "email": "test@example.com",
      "success": false,
      "error": "验证码不匹配",
      "timestamp": "2025-05-30T22:50:13"
    }
  ]
}
```

## 🔧 故障排除

### 常见问题

#### 1. Gmail连接失败
```
错误: 连接Gmail IMAP服务器失败
```
**解决方案**:
- 检查环境变量是否正确设置
- 确认Gmail应用密码是否有效
- 验证网络连接是否正常

#### 2. 验证码提取失败
```
错误: 未能从邮件中提取到有效的验证码
```
**解决方案**:
- 检查邮件是否已到达
- 确认验证码邮件格式
- 查看日志中的邮件内容

#### 3. 代理连接失败
```
错误: Cannot connect to host 127.0.0.1:7890
```
**解决方案**:
- 启动本地代理服务器
- 检查代理配置是否正确
- 或在config.yaml中禁用代理

#### 4. 模块导入失败
```
错误: 导入模块失败
```
**解决方案**:
- 确保在项目根目录下运行
- 检查Python路径配置
- 重新安装依赖包

### 调试模式
```bash
# 启用详细日志
export LOG_LEVEL=DEBUG
./modules/polyflow/start.sh --test
```

## 🔒 安全注意事项

1. **环境变量**: 敏感信息使用环境变量存储
2. **应用密码**: 使用Gmail应用密码，不要使用主密码
3. **代理安全**: 确保代理服务器的安全性
4. **日志安全**: 定期清理包含敏感信息的日志

## 📈 性能优化

1. **并发控制**: 合理设置请求间隔，避免被限制
2. **代理轮换**: 使用多个代理提高成功率
3. **重试机制**: 智能重试，处理临时性错误
4. **资源管理**: 及时释放连接和资源

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 支持

如果遇到问题或需要帮助：

1. 查看 [CHANGELOG.md](CHANGELOG.md) 了解最新更新
2. 检查 [故障排除](#故障排除) 部分
3. 提交 Issue 描述问题

---

**注意**: 请遵守相关网站的服务条款，合理使用自动化工具。 