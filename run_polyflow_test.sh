#!/bin/bash

# Polyflow需求验证测试启动脚本

echo "=== Polyflow API需求验证测试 ==="
echo ""

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3环境"
    exit 1
fi

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "错误: 虚拟环境目录 venv 不存在"
    echo "请先创建虚拟环境: python3 -m venv venv"
    exit 1
fi

# 检查必要文件
if [ ! -f "src/polyflow/email.txt" ]; then
    echo "错误: 邮箱配置文件 src/polyflow/email.txt 不存在"
    exit 1
fi

if [ ! -f "config.yaml" ]; then
    echo "错误: 配置文件 config.yaml 不存在"
    exit 1
fi

if [ ! -f ".env" ]; then
    echo "警告: 环境变量文件 .env 不存在"
    echo "邮件相关测试可能会失败"
fi

# 创建必要目录
mkdir -p src/data/test_reports
mkdir -p src/logs

echo "环境检查完成，开始执行测试..."
echo ""

# 激活虚拟环境并运行测试
source venv/bin/activate
cd src
python test_polyflow_requirements.py

echo ""
echo "测试执行完成！"
echo ""
echo "查看测试结果："
echo "- 测试报告: src/data/test_reports/"
echo "- 程序日志: src/logs/"
echo "- 详细报告: POLYFLOW_REQUIREMENTS_TEST_REPORT.md"
echo ""

# 显示最新的测试报告摘要
if [ -d "data/test_reports" ]; then
    latest_report=$(ls -t data/test_reports/polyflow_requirements_test_*.json 2>/dev/null | head -1)
    if [ -n "$latest_report" ]; then
        echo "最新测试报告: $latest_report"
        echo "快速查看测试结果："
        python3 -c "
import json
try:
    with open('$latest_report', 'r') as f:
        data = json.load(f)
    summary = data['test_summary']
    requirements = data['requirements_verification']
    
    print(f\"总测试数: {summary['total_tests']}\")
    print(f\"通过测试: {summary['passed_tests']}\")
    print(f\"失败测试: {summary['failed_tests']}\")
    print(f\"成功率: {summary['success_rate']}\")
    print()
    print('需求验证结果:')
    for req, status in requirements.items():
        icon = '✅' if status else '❌'
        print(f'  {icon} {req}: {\"通过\" if status else \"失败\"}')
except Exception as e:
    print(f'无法解析测试报告: {e}')
"
    fi
fi 