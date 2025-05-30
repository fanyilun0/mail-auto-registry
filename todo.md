请用Python开发一个邮箱自动注册/登录工具，具体要求如下：

### 一、核心功能模块

1. 代理管理
   - 支持HTTP和Socks5代理
   - 在浏览器启动前配置代理
   - 实现代理轮换和失效检测

2. 自动化调用api
   - 发送邮箱验证码接口
   - 根据登录接口的要求发送email和code

3. 邮件验证码处理
   - 通过IMAP协议连接Google邮箱
   - 验证码提取功能：
     * 正则匹配提取
     * 基于时间戳排序
     * 设置120秒超时机制
   - 实现验证码缓存防重复使用

4. 验证码识别
   - 集成2Captcha等第三方识别服务
   - 支持多类型验证码处理

5. 数据管理
   - Cookie/Token持久化存储
   - 多格式数据导出(JSON/CSV)
   - 敏感信息加密

### 二、工程质量要求

1. 项目结构
   - 采用模块化设计
   - 使用YAML配置文件
   - 完善的日志记录系统

2. 健壮性
   - 实现指数退避重试机制
   - 完善的异常处理流程

3. 性能考虑
   - 浏览器实例池管理
   - 支持并行任务处理
   - 资源释放和内存管理

4. 安全措施
   - 环境变量管理敏感信息
   - 实现请求频率控制
   - 自动化特征隐藏


### 项目文件结构
zou-macmini-m4@192 mail-auto-registry % tree -L 3
.
├── captcha // 处理验证码
│   └── captcha_solver.py
├── config.yaml
├── data // 生成的数据
├── logs // 生成的数据
│   ├── polyflow_api_2025-05-29.log
│   ├── polyflow_api_2025-05-30.log
│   └── verification.log
├── modules // 统一存在需要注册的APP
│   └── polyflow // Module 1
│       ├── __init__.py
│       ├── __pycache__
│       ├── email.txt
│       ├── polyflow_api_client.py
│       ├── polyflow_registry.py
│       ├── proxies.txt
│       ├── start.sh
│       ├── test.sh
│       └── todo.md
├── proxy // 注册过程中提供给Module使用的proxy工具 
│   └── proxy_manager.py
├── requirements.txt
├── todo.md
