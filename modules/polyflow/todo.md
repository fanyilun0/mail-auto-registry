TODO: 
1. ✅ 解决提前读取邮件导致验证码不匹配的问题
- ✅ 在发送send请求之后， 需要等待获取到回调之后再进行读取邮件的code
- ✅ 请求成功的response： {"success":true,"msg":{}}

2. ✅ 需要正确把所需要的数据保存到本地
- ✅ 已实现token数据保存功能
- ✅ 支持JSON和批量文件格式保存

3. ✅ 我在根路径下执行 % ./modules/polyflow/start.sh， 这个sh文件需要处理
- ✅ 统一设置python执行环境
- ✅ 启动python文件 同时需要统一执行的目录（在根目录执行还是在当前目录执行），需要避免由于各python执行的路径不一致导致的路径错误
- ✅ 解决潜在的由于执行路径不一致导致的路径/文件错误的问题

## 已完成的功能

### 启动脚本功能
- ✅ 自动检测项目根目录
- ✅ 统一Python环境管理（支持虚拟环境自动激活）
- ✅ 路径一致性保证（无论从哪个目录执行都能正确工作）
- ✅ 依赖包自动检查和安装
- ✅ 配置文件验证
- ✅ 必要目录自动创建
- ✅ 多种运行模式支持

### 使用方法

#### 基本使用
```bash
# 从项目根目录运行（推荐）
./modules/polyflow/start.sh

# 从模块目录运行
cd modules/polyflow
./start.sh

# 从任意目录运行
/path/to/project/modules/polyflow/start.sh
```

#### 运行模式
```bash
# 批量注册模式（默认）
./modules/polyflow/start.sh --batch

# 测试模式（检查环境和模块导入）
./modules/polyflow/start.sh --test

# 环境检查模式
./modules/polyflow/start.sh --check

# 显示帮助信息
./modules/polyflow/start.sh --help

# 单个邮箱注册模式
./modules/polyflow/start.sh --single
```

#### 测试脚本
```bash
# 运行所有测试
./modules/polyflow/test.sh

# 运行特定测试
./modules/polyflow/test.sh --environment
./modules/polyflow/test.sh --path
```

### 文件结构
```
modules/polyflow/
├── start.sh              # 主启动脚本
├── test.sh               # 测试脚本
├── main.py               # 主程序入口
├── polyflow_api_client.py # API客户端
├── polyflow_registry.py   # 浏览器自动化注册器
├── email.txt             # 邮箱配置文件
├── proxies.txt           # 代理配置文件（可选）
└── __init__.py           # 模块初始化文件
```

### 配置要求
1. 确保 `email.txt` 文件存在并包含要注册的邮箱地址
2. 确保 `config.yaml` 配置文件正确设置
3. 可选：配置 `proxies.txt` 文件以使用代理

### 注意事项
- 脚本会自动检测并激活虚拟环境（venv 或 .venv）
- 所有路径问题已解决，支持从任意目录执行
- 自动创建必要的数据目录（data/tokens, data/screenshots, data/reports, logs）
- 支持依赖包自动安装