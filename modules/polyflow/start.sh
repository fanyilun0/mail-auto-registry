#!/bin/bash

# Polyflow模块主启动脚本
# 支持从任意目录执行

set -e  # 遇到错误立即退出

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 加载通用启动脚本库
# 尝试多个可能的路径
if [ -f "$SCRIPT_DIR/../common_startup.sh" ]; then
    source "$SCRIPT_DIR/../common_startup.sh"
elif [ -f "src/common_startup.sh" ]; then
    source "src/common_startup.sh"
else
    echo "❌ 错误: 无法找到通用启动脚本库"
    echo "请确保 src/common_startup.sh 文件存在"
    exit 1
fi

# 模块特定配置
MODULE_NAME="Polyflow"
MAIN_SCRIPT="polyflow_api_main.py"
REQUIRED_PACKAGES=("aiohttp" "loguru" "yaml" "requests")

# 显示帮助信息
show_help() {
    show_module_help "$MODULE_NAME" "start.sh"
    echo ""
    echo "Polyflow特定功能:"
    echo "  - 邮箱自动注册"
    echo "  - 批量账号处理"
    echo "  - 代理轮换支持"
    echo "  - Token数据保存"
    exit 0
}

# 检查模块特定配置文件
check_polyflow_config() {
    log_info "🔍 检查Polyflow模块配置..."
    
    local email_file="$PROJECT_ROOT/src/polyflow/email.txt"
    local proxy_file="$PROJECT_ROOT/src/polyflow/proxies.txt"
    
    if [ ! -f "$email_file" ]; then
        log_error "❌ 邮箱配置文件不存在: $email_file"
        log_error "请在该文件中添加邮箱地址，每行一个"
        return 1
    else
        local email_count
        email_count=$(wc -l < "$email_file" 2>/dev/null || echo "0")
        log_info "✅ 邮箱配置文件存在，包含 $email_count 个邮箱"
    fi
    
    if [ -f "$proxy_file" ]; then
        local proxy_count
        proxy_count=$(grep -v '^#' "$proxy_file" | grep -v '^$' | wc -l 2>/dev/null || echo "0")
        log_info "✅ 代理配置文件存在，包含 $proxy_count 个代理"
    else
        log_warn "⚠️  代理配置文件不存在，将不使用代理"
    fi
    
    # 创建Polyflow特定目录
    ensure_directories "$PROJECT_ROOT" \
        "data/polyflow_tokens_detailed" \
        "data/reports"
}

# 主函数
main() {
    # 处理命令行参数
    if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
        show_help
    fi
    
    # 通用初始化
    common_init "$MODULE_NAME" "${REQUIRED_PACKAGES[@]}"
    if [ $? -ne 0 ]; then
        exit 1
    fi
    
    # 检查模块特定配置
    check_polyflow_config
    if [ $? -ne 0 ]; then
        exit 1
    fi
    
    # 切换到src目录执行Python脚本
    cd "$PROJECT_ROOT/src" || {
        log_error "无法切换到src目录"
        exit 1
    }
    
    log_info ""
    if [ "$1" = "test" ]; then
        log_info "🧪 启动Polyflow测试模式..."
        log_info "📍 执行路径: $PROJECT_ROOT/src"
        log_info "🐍 Python命令: $PYTHON_CMD"
        log_info "📄 主脚本: $MAIN_SCRIPT"
        log_info ""
        
        $PYTHON_CMD "$MAIN_SCRIPT" test
    else
        log_info "🔄 启动Polyflow批量注册模式..."
        log_info "📍 执行路径: $PROJECT_ROOT/src"
        log_info "🐍 Python命令: $PYTHON_CMD"
        log_info "📄 主脚本: $MAIN_SCRIPT"
        log_info ""
        
        $PYTHON_CMD "$MAIN_SCRIPT"
    fi
    
    local exit_code=$?
    
    log_info ""
    log_info "📊 执行完成！"
    log_info "================================"
    log_info "📋 查看结果:"
    log_info "  - Token数据: $PROJECT_ROOT/data/polyflow_tokens.txt"
    log_info "  - 详细数据: $PROJECT_ROOT/data/polyflow_tokens_detailed/"
    log_info "  - 日志文件: $PROJECT_ROOT/logs/"
    log_info ""
    
    if [ $exit_code -eq 0 ]; then
        log_info "🎉 Polyflow模块执行成功！"
    else
        log_error "❌ Polyflow模块执行失败，退出码: $exit_code"
    fi
    
    exit $exit_code
}

# 执行主函数
main "$@" 