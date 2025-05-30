#!/bin/bash

# Polyflow模块启动脚本
# 解决路径一致性问题，统一Python执行环境

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
print_info "脚本目录: $SCRIPT_DIR"

# 获取项目根目录（向上两级目录）
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
print_info "项目根目录: $PROJECT_ROOT"

# 检查项目根目录是否正确
if [[ ! -f "$PROJECT_ROOT/config.yaml" ]]; then
    print_error "未找到项目根目录，请确保脚本在正确的位置运行"
    exit 1
fi

print_success "项目根目录验证成功"

# 切换到项目根目录
cd "$PROJECT_ROOT"
print_info "当前工作目录: $(pwd)"

# 检查Python环境
check_python() {
    print_info "检查Python环境..."
    
    # 优先检查虚拟环境
    if [[ -d "$PROJECT_ROOT/venv" ]]; then
        print_info "发现虚拟环境，激活中..."
        source "$PROJECT_ROOT/venv/bin/activate"
        print_success "虚拟环境已激活"
    elif [[ -d "$PROJECT_ROOT/.venv" ]]; then
        print_info "发现虚拟环境(.venv)，激活中..."
        source "$PROJECT_ROOT/.venv/bin/activate"
        print_success "虚拟环境已激活"
    else
        print_warning "未发现虚拟环境，使用系统Python"
    fi
    
    # 检查Python版本
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        print_error "未找到Python解释器"
        exit 1
    fi
    
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1)
    print_success "Python环境: $PYTHON_VERSION"
    
    # 检查必要的包
    print_info "检查必要的Python包..."
    if ! $PYTHON_CMD -c "import asyncio, loguru, aiohttp" 2>/dev/null; then
        print_warning "缺少必要的Python包，尝试安装..."
        if [[ -f "$PROJECT_ROOT/requirements.txt" ]]; then
            $PYTHON_CMD -m pip install -r "$PROJECT_ROOT/requirements.txt"
            print_success "依赖包安装完成"
        else
            print_error "未找到requirements.txt文件"
            exit 1
        fi
    else
        print_success "Python包检查通过"
    fi
}

# 检查配置文件
check_config() {
    print_info "检查配置文件..."
    
    if [[ ! -f "$PROJECT_ROOT/config.yaml" ]]; then
        print_error "未找到config.yaml配置文件"
        exit 1
    fi
    
    # 检查邮箱配置文件
    if [[ ! -f "$PROJECT_ROOT/modules/polyflow/email.txt" ]]; then
        print_error "未找到邮箱配置文件: modules/polyflow/email.txt"
        print_info "请创建该文件并添加要注册的邮箱地址（每行一个）"
        exit 1
    fi
    
    # 检查代理配置文件（可选）
    if [[ -f "$PROJECT_ROOT/modules/polyflow/proxies.txt" ]]; then
        print_success "发现代理配置文件"
    else
        print_warning "未发现代理配置文件，将使用直连模式"
    fi
    
    print_success "配置文件检查完成"
}

# 创建必要的目录
create_directories() {
    print_info "创建必要的目录..."
    
    mkdir -p "$PROJECT_ROOT/data/tokens"
    mkdir -p "$PROJECT_ROOT/data/screenshots"
    mkdir -p "$PROJECT_ROOT/data/reports"
    mkdir -p "$PROJECT_ROOT/logs"
    
    print_success "目录创建完成"
}

# 显示使用帮助
show_help() {
    echo "Polyflow自动注册工具启动脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help     显示此帮助信息"
    echo "  -t, --test     运行测试模式"
    echo "  -b, --batch    批量注册模式"
    echo "  -s, --single   单个邮箱注册模式"
    echo "  -c, --check    仅检查环境配置"
    echo ""
    echo "示例:"
    echo "  $0 --batch     # 批量注册所有邮箱"
    echo "  $0 --single    # 单个邮箱注册"
    echo "  $0 --test      # 测试模式"
    echo "  $0 --check     # 检查环境"
}

# 运行主程序
run_main() {
    local mode="$1"
    
    print_info "启动Polyflow注册程序..."
    
    # 设置Python路径，确保能找到模块
    export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
    
    # 运行主程序
    case "$mode" in
        "batch")
            print_info "运行批量注册模式..."
            $PYTHON_CMD "$PROJECT_ROOT/modules/polyflow/main.py"
            ;;
        "test")
            print_info "运行测试模式..."
            $PYTHON_CMD -c "
import sys
sys.path.insert(0, '$PROJECT_ROOT')
try:
    from modules.polyflow.polyflow_api_client import PolyflowAPIClient
    from gmail.email_handler import EmailHandler
    from proxy.proxy_manager import ProxyManager
    print('✅ 模块导入测试成功')
    print('✅ 环境配置正常')
except ImportError as e:
    print(f'❌ 模块导入失败: {e}')
    exit(1)
"
            ;;
        "check")
            print_success "环境检查完成，所有配置正常"
            ;;
        "single")
            print_info "运行单个邮箱注册模式..."
            # 可以在这里添加单个邮箱注册的逻辑
            print_info "单个邮箱注册模式暂未实现，使用批量模式"
            $PYTHON_CMD "$PROJECT_ROOT/modules/polyflow/main.py"
            ;;
        *)
            print_info "运行默认模式（批量注册）..."
            $PYTHON_CMD "$PROJECT_ROOT/modules/polyflow/main.py"
            ;;
    esac
}

# 主函数
main() {
    local mode="batch"
    
    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -t|--test)
                mode="test"
                shift
                ;;
            -b|--batch)
                mode="batch"
                shift
                ;;
            -s|--single)
                mode="single"
                shift
                ;;
            -c|--check)
                mode="check"
                shift
                ;;
            *)
                print_error "未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    print_info "=== Polyflow自动注册工具启动 ==="
    print_info "模式: $mode"
    
    # 执行检查和初始化
    check_python
    check_config
    create_directories
    
    # 运行主程序
    run_main "$mode"
    
    print_success "=== 程序执行完成 ==="
}

# 执行主函数
main "$@"
