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