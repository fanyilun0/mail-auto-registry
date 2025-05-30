# 邮箱自动注册工具

一个功能完整的邮箱自动注册工具，支持Gmail IMAP连接、代理管理和验证码自动提取。

## 🚀 快速开始

### 1. 环境配置

#### 方法1: 使用环境变量（推荐）
```bash
# 设置Gmail凭据
export EMAIL_USERNAME="your-email@gmail.com"
export EMAIL_PASSWORD="your-16-digit-app-password"

# 运行程序
./modules/polyflow/start.sh
```

#### 方法2: 使用.env文件
```bash
# 复制示例文件
cp env.example .env

# 编辑.env文件，设置您的Gmail凭据
# EMAIL_USERNAME=your-email@gmail.com
# EMAIL_PASSWORD=your-16-digit-app-password

# 运行程序
./modules/polyflow/start.sh
```

### 2. Gmail应用密码设置

1. 登录Gmail账号
2. 前往 [Google账号安全设置](https://myaccount.google.com/security)
3. 启用"两步验证"
4. 在"应用密码"中生成16位密码
5. 使用生成的应用密码作为 `EMAIL_PASSWORD`

### 3. 测试连接

```bash
# 测试Gmail连接
python3 test_gmail.py

# 测试完整环境
./modules/polyflow/start.sh --test
```

## 📁 项目结构

```
mail-auto-registry/
├── gmail/                    # Gmail邮件处理模块
├── proxy/                    # 代理管理模块
├── modules/polyflow/         # Polyflow注册模块
├── utils/                    # 工具模块（配置加载器）
├── config.yaml              # 主配置文件
├── .env                      # 环境变量文件（需要创建）
├── env.example               # 环境变量示例
├── test_gmail.py             # Gmail连接测试
└── requirements.txt          # Python依赖
```

## 🔧 配置说明

### 环境变量支持

配置文件 `config.yaml` 支持以下环境变量格式：

```yaml
email:
  username: ${EMAIL_USERNAME}           # 必需
  password: ${EMAIL_PASSWORD}           # 必需
  
captcha:
  api_key: ${CAPTCHA_API_KEY}           # 可选
```

### 支持的环境变量

| 变量名 | 说明 | 必需 |
|--------|------|------|
| `EMAIL_USERNAME` | Gmail邮箱地址 | ✅ |
| `EMAIL_PASSWORD` | Gmail应用密码 | ✅ |
| `CAPTCHA_API_KEY` | 验证码服务API密钥 | ❌ |

## 🛠️ 故障排除

### 常见错误

#### 1. 环境变量未设置
```
错误: 邮箱用户名未配置，请设置环境变量 EMAIL_USERNAME
```
**解决方案**: 设置环境变量或创建.env文件

#### 2. Gmail认证失败
```
错误: [AUTHENTICATIONFAILED] Invalid credentials
```
**解决方案**: 
- 检查Gmail应用密码是否正确
- 确认已启用两步验证
- 验证邮箱地址是否正确

#### 3. 配置文件格式错误
```
错误: 环境变量配置错误，请检查.env文件或系统环境变量
```
**解决方案**: 检查环境变量格式是否正确

## 📖 详细文档

更多详细信息请查看：
- [Polyflow模块文档](modules/polyflow/README.md)
- [变更日志](modules/polyflow/CHANGELOG.md)

## 🔒 安全提醒

1. **不要提交.env文件到版本控制**
2. **使用Gmail应用密码，不要使用主密码**
3. **定期更换应用密码**
4. **保护好您的凭据信息**

---

**注意**: 请遵守相关网站的服务条款，合理使用自动化工具。 