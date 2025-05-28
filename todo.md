请用Python开发一个邮箱自动注册/登录工具，具体要求如下：

### 一、核心功能模块

1. 代理管理
   - 支持HTTP和Socks5代理
   - 在浏览器启动前配置代理
   - 实现代理轮换和失效检测

2. 浏览器自动化
   - 基于Playwright实现
   - 元素定位策略：
     * 优先使用CSS选择器
     * 实现元素可交互状态等待
     * 支持多定位策略回退
   - 封装常见操作异常处理

3. 邮件验证码处理
   - 通过IMAP协议连接proton.me邮箱
   - 验证码提取功能：
     * 正则匹配提取
     * 基于时间戳排序
     * 设置120秒超时机制
   - 实现验证码缓存防重复使用

4. 验证码识别
   - 集成2Captcha等第三方识别服务
   - 支持多类型验证码处理

5. 数据管理
   - Cookie持久化存储
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


### 实际业务需求
以https://app.polyflow.tech/为案例，完成使用浏览器自动化注册动作
1. 导航到url并检索DOM结构
```html
<input class="mt-2 h-[46px] w-full rounded-xl border-none bg-[#454549] p-4 text-sm font-normal placeholder-[#8A8B8D] md:h-[54px]" type="email" placeholder="Enter Email">
```

```html
<div class="relative mt-2 flex h-[46px] w-full items-center rounded-xl border-none bg-[#454549] text-sm font-normal placeholder-[#8A8B8D] md:h-[54px]"><input class="absolute left-0 top-0 h-[46px] w-full rounded-xl border-none bg-[#454549] p-4 text-sm font-normal placeholder-[#8A8B8D] md:h-[54px]" type="number" placeholder="Enter Code" style="padding: 1rem;"><button class="absolute right-[10px] flex h-7 w-[60px] items-center justify-center rounded-md bg-[#8A8B8D] text-black">Send</button></div>
```
需要在打开的浏览器去输入指定的邮件地址然后点击send再配合IMAP获取到验证码后完成登录， 登录后获取数据

获取localStorage中的token并保存到本地

需要尽量抽离为单独的模块来实现， 方便后续迁移