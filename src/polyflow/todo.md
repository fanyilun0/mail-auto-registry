## polyflow api auto reigstry

### 
批量读取sites/email.txt中的邮件地址， 然后逐个执行以下操作

#### 然后通过API调用发送验证码到邮箱的接口
```json
POST https://api-v2.polyflow.tech/api/account/email/send
{"email": "test@email.com","type":"login"}
```

#### 通过imap读取最新的email收到的验证码， 并调用注册的接口
```json
POST https://api-v2.polyflow.tech/api/account/email/login
{"email": "test@email.com","code":"123456","referral_code":""}
```

响应数据
```json
{
    ""success"": true,
    ""msg"": {
        ""token"": ""eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjowLCJhZGRyZXNzIjoiIiwiY2hhaW5faWQiOjAsInZvdWNoZXJzIjowLCJhY2NvdW50X2lkIjoiMjFkNTJmMmYyNjZkNDUzODg2MTA2OGJiMjRiYjZlZjMiLCJ1c2VyX25hbWUiOiIiLCJuaWNrX25hbWUiOiJQRjIxZDUyZjJmMjY2ZDQ1Mzg4NjEwNjhiYjI0YmI2ZWYzIiwiZmlyc3RfbmFtZSI6IiIsImxhc3RfbmFtZSI6IiIsImVtYWlsIjoiIiwicGhvbmUiOiIiLCJhdmF0YXIiOiIiLCJpc19zb2NpYWxfbG9naW4iOnRydWUsImlzX3dhbGxldF9sb2dpbiI6ZmFsc2UsImV4cCI6MTc1MTAzNjAyM30.COf1NFlcIxTo6L0nK90ih5VuU5Xhur9GoZ1WsnQ2Lxs"",
        ""expiry"": 1751036023
    }
}
```
然后把token保存到本地， 同时把时间戳转化为时间也保存到本地， 构建为一个表格，用txt来保存
- email
- token
- expire
（一行一组数据）

### 代码要求：需要把API调用到逻辑用单独的文件来管理

------
TODO：解决API调用403的问题
## 优化调用API

### 现有的执行日志
2025-05-29 21:41:11 | INFO     | __main__:log_test_result:46 - ❌ 失败 - API发送验证码: 发送验证码API调用异常: 403, message='Attempt to decode JSON with unexpected mimetype: text/html', url='https://api-v2.polyflow.tech/api/account/email/send'
2025-05-29 21:41:12 | INFO     | email_handler:connect:40 - 已连接到邮件服务器
2025-05-29 21:41:12 | INFO     | __main__:test_3_email_verification_code_reading:124 - 测试邮件连接和验证码读取功能...
2025-05-29 21:41:12 | INFO     | __main__:log_test_result:46 - ✅ 通过 - IMAP邮件连接: 邮件服务器连接成功，验证码读取功能可用
ç2025-05-29 21:41:13 | INFO     | __main__:log_test_result:46 - ❌ 失败 - 登录API结构验证: 登录API测试异常: 403, message='Attempt to decode JSON with unexpected mimetype: text/html', url='https://api-v2.polyflow.tech/api/account/email/login'

### 添加fake UA和其他反爬虫方式来规避403的问题

### 添加代理 （可选）
新增ployflow/proxies来添加代理避免

--------
