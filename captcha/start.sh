#!/bin/bash

# Captcha模块启动脚本
# 验证码识别服务

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
MODULE_NAME="Captcha"
MAIN_SCRIPT="captcha_solver.py"
REQUIRED_PACKAGES=("requests" "pillow" "opencv-python" "loguru")

# 显示帮助信息
show_help() {
    show_module_help "$MODULE_NAME" "start.sh"
    echo ""
    echo "Captcha特定功能:"
    echo "  - 验证码识别"
    echo "  - 2Captcha集成"
    echo "  - 图像处理"
    echo "  - 多类型验证码支持"
    exit 0
}

# 检查验证码服务配置
check_captcha_config() {
    log_info "🔍 检查验证码服务配置..."
    
    # 检查API密钥环境变量
    if [ -n "$CAPTCHA_API_KEY" ]; then
        log_info "✅ 找到验证码API密钥环境变量"
    else
        log_warn "⚠️  未设置验证码API密钥环境变量 CAPTCHA_API_KEY"
    fi
    
    # 检查配置文件中的验证码设置
    local config_file="$PROJECT_ROOT/config.yaml"
    if [ -f "$config_file" ]; then
        if grep -q "captcha" "$config_file" 2>/dev/null; then
            log_info "✅ 配置文件包含验证码设置"
        else
            log_warn "⚠️  配置文件中未找到验证码设置"
        fi
    fi
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
    
    # 检查验证码服务配置
    check_captcha_config
    
    # 切换到src目录执行
    cd "$PROJECT_ROOT/src" || {
        log_error "无法切换到src目录"
        exit 1
    }
    
    log_info ""
    if [ "$1" = "test" ]; then
        log_info "🧪 启动Captcha测试模式..."
        $PYTHON_CMD -c "
from captcha.captcha_solver import CaptchaSolver
print('Captcha模块测试')
solver = CaptchaSolver()
print('验证码解析器初始化成功')
"
    else
        log_info "🔐 启动Captcha模块..."
        $PYTHON_CMD -c "
from captcha.captcha_solver import CaptchaSolver
print('Captcha模块启动')
# 在这里添加具体的业务逻辑
"
    fi
    
    local exit_code=$?
    
    log_info ""
    if [ $exit_code -eq 0 ]; then
        log_info "🎉 Captcha模块执行成功！"
    else
        log_error "❌ Captcha模块执行失败"
    fi
    
    exit $exit_code
}

# 执行主函数
main "$@" 