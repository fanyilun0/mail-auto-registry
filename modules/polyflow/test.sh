#!/bin/bash

# Polyflow模块测试启动脚本
# 专门用于快速测试和调试

set -e

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 加载通用启动脚本库
if [ -f "$SCRIPT_DIR/../common_startup.sh" ]; then
    source "$SCRIPT_DIR/../common_startup.sh"
elif [ -f "src/common_startup.sh" ]; then
    source "src/common_startup.sh"
else
    echo "❌ 错误: 无法找到通用启动脚本库"
    exit 1
fi

# 模块特定配置
MODULE_NAME="Polyflow-Test"
MAIN_SCRIPT="polyflow_api_main.py"
REQUIRED_PACKAGES=("aiohttp" "loguru" "yaml")

# 显示帮助信息
show_help() {
    echo "🧪 Polyflow测试模式启动器"
    echo "================================"
    echo "使用方法:"
    echo "  ./test.sh                        # 运行单个邮箱测试"
    echo "  ./test.sh --help                # 显示帮助"
    echo ""
    echo "从项目根目录执行:"
    echo "  ./src/polyflow/test.sh          # 运行测试"
    echo ""
    echo "功能说明:"
    echo "  - 快速环境检查"
    echo "  - 单个邮箱注册测试"
    echo "  - 适合开发调试使用"
    echo "  - 简化的错误输出"
    exit 0
}

# 快速检查核心文件
quick_check() {
    log_info "📋 快速检查核心文件..."
    
    local files_to_check=(
        "$PROJECT_ROOT/config.yaml"
        "$PROJECT_ROOT/src/polyflow/email.txt"
        "$PROJECT_ROOT/src/polyflow_api_main.py"
        "$PROJECT_ROOT/src/polyflow/polyflow_api_client.py"
    )
    
    for file in "${files_to_check[@]}"; do
        if [ -f "$file" ]; then
            log_info "✅ $(basename "$file")"
        else
            log_error "❌ $(basename "$file") (缺失)"
        fi
    done
}

# 主函数
main() {
    # 处理命令行参数
    if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
        show_help
    fi
    
    log_info "🧪 $MODULE_NAME 启动器"
    log_info "====================="
    
    # 查找项目根目录
    local project_root
    project_root="$(find_project_root)"
    log_info "📁 项目路径: $project_root"
    
    # 切换到项目根目录
    cd "$project_root" || {
        log_error "无法切换到项目根目录"
        exit 1
    }
    
    # 检查Python环境
    log_info "🐍 检查Python环境..."
    local python_cmd=""
    
    # 优先检查虚拟环境
    if [ -f "$project_root/venv/bin/python3" ]; then
        python_cmd="$project_root/venv/bin/python3"
        log_info "✅ 使用虚拟环境Python3: $python_cmd"
    elif [ -f "$project_root/venv/bin/python" ]; then
        python_cmd="$project_root/venv/bin/python"
        log_info "✅ 使用虚拟环境Python: $python_cmd"
    elif command -v python3 &> /dev/null; then
        python_cmd="python3"
        log_info "✅ 使用系统Python3: $(which python3)"
    elif command -v python &> /dev/null; then
        python_cmd="python"
        log_info "✅ 使用系统Python: $(which python)"
    else
        log_error "❌ 错误: 未找到Python环境"
        exit 1
    fi
    
    # 导出Python命令
    export PYTHON_CMD="$python_cmd"
    
    # 快速检查核心文件
    export PROJECT_ROOT="$project_root"
    quick_check
    
    # 创建必要目录
    mkdir -p data logs src/logs
    
    # 设置Python路径
    setup_python_path "$project_root"
    
    log_info ""
    log_info "🚀 启动测试模式..."
    log_info "================================"
    
    # 切换到src目录执行
    cd src || {
        log_error "无法切换到src目录"
        exit 1
    }
    
    $PYTHON_CMD "$MAIN_SCRIPT" test
    
    local exit_code=$?
    
    log_info ""
    if [ $exit_code -eq 0 ]; then
        log_info "📊 测试完成！"
    else
        log_error "❌ 测试失败，退出码: $exit_code"
    fi
    
    exit $exit_code
}

# 执行主函数
main "$@" 