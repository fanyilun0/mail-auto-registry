#!/bin/bash

# Polyflow模块测试脚本
# 用于测试启动脚本的各项功能

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() {
    echo -e "${BLUE}[TEST INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[TEST SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[TEST ERROR]${NC} $1"
}

# 获取脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

print_info "=== Polyflow启动脚本测试 ==="
print_info "项目根目录: $PROJECT_ROOT"

# 测试1: 检查脚本是否可执行
test_script_executable() {
    print_info "测试1: 检查脚本执行权限..."
    
    if [[ -x "$SCRIPT_DIR/start.sh" ]]; then
        print_success "start.sh 具有执行权限"
    else
        print_error "start.sh 缺少执行权限"
        return 1
    fi
}

# 测试2: 检查环境配置
test_environment_check() {
    print_info "测试2: 运行环境检查..."
    
    cd "$PROJECT_ROOT"
    if "$SCRIPT_DIR/start.sh" --check; then
        print_success "环境检查通过"
    else
        print_error "环境检查失败"
        return 1
    fi
}

# 测试3: 测试模式
test_test_mode() {
    print_info "测试3: 运行测试模式..."
    
    cd "$PROJECT_ROOT"
    if "$SCRIPT_DIR/start.sh" --test; then
        print_success "测试模式运行成功"
    else
        print_error "测试模式运行失败"
        return 1
    fi
}

# 测试4: 帮助信息
test_help() {
    print_info "测试4: 显示帮助信息..."
    
    cd "$PROJECT_ROOT"
    if "$SCRIPT_DIR/start.sh" --help; then
        print_success "帮助信息显示正常"
    else
        print_error "帮助信息显示失败"
        return 1
    fi
}

# 测试5: 路径一致性
test_path_consistency() {
    print_info "测试5: 测试路径一致性..."
    
    # 从不同目录运行脚本，检查是否都能正确找到项目根目录
    
    # 从根目录运行
    cd "$PROJECT_ROOT"
    if "$SCRIPT_DIR/start.sh" --check >/dev/null 2>&1; then
        print_success "从根目录运行: 成功"
    else
        print_error "从根目录运行: 失败"
        return 1
    fi
    
    # 从模块目录运行
    cd "$SCRIPT_DIR"
    if "./start.sh" --check >/dev/null 2>&1; then
        print_success "从模块目录运行: 成功"
    else
        print_error "从模块目录运行: 失败"
        return 1
    fi
    
    # 从其他目录运行
    cd /tmp
    if "$SCRIPT_DIR/start.sh" --check >/dev/null 2>&1; then
        print_success "从其他目录运行: 成功"
    else
        print_error "从其他目录运行: 失败"
        return 1
    fi
}

# 运行所有测试
run_all_tests() {
    local failed_tests=0
    
    test_script_executable || ((failed_tests++))
    test_help || ((failed_tests++))
    test_environment_check || ((failed_tests++))
    test_test_mode || ((failed_tests++))
    test_path_consistency || ((failed_tests++))
    
    echo ""
    if [[ $failed_tests -eq 0 ]]; then
        print_success "=== 所有测试通过! ==="
        print_info "启动脚本已准备就绪，可以使用以下命令运行:"
        print_info "  ./modules/polyflow/start.sh --batch    # 批量注册"
        print_info "  ./modules/polyflow/start.sh --test     # 测试模式"
        print_info "  ./modules/polyflow/start.sh --check    # 环境检查"
        print_info "  ./modules/polyflow/start.sh --help     # 显示帮助"
    else
        print_error "=== $failed_tests 个测试失败 ==="
        exit 1
    fi
}

# 主函数
main() {
    if [[ $# -eq 0 ]]; then
        run_all_tests
    else
        case $1 in
            --executable)
                test_script_executable
                ;;
            --environment)
                test_environment_check
                ;;
            --test-mode)
                test_test_mode
                ;;
            --help-test)
                test_help
                ;;
            --path)
                test_path_consistency
                ;;
            *)
                echo "用法: $0 [--executable|--environment|--test-mode|--help-test|--path]"
                echo "不带参数运行所有测试"
                exit 1
                ;;
        esac
    fi
}

main "$@"
