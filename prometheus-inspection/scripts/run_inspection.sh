#!/bin/bash

# Prometheus 巡检执行脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 默认配置
CONFIG_FILE="${CONFIG_FILE:-config/inspection_config.yml}"
OUTPUT_DIR="${OUTPUT_DIR:-reports}"
FORMATS="${FORMATS:-html json}"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=============================================="
echo "Prometheus 巡检脚本"
echo "=============================================="
echo ""

# 检查 Python 环境
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}错误：未找到 Python3${NC}"
    exit 1
fi

# 检查依赖
echo "检查依赖..."
if ! python3 -c "import requests" 2>/dev/null; then
    echo -e "${YELLOW}安装依赖...${NC}"
    pip3 install -r requirements.txt
fi

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -c|--config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        -u|--url)
            PROMETHEUS_URL="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        -f|--format)
            FORMATS="$2"
            shift 2
            ;;
        -h|--help)
            echo "用法：$0 [选项]"
            echo ""
            echo "选项:"
            echo "  -c, --config FILE    配置文件路径 (默认：config/inspection_config.yml)"
            echo "  -u, --url URL        Prometheus 服务器 URL"
            echo "  -o, --output DIR     报告输出目录 (默认：reports)"
            echo "  -f, --format FMTS    报告格式，空格分隔 (默认：html json)"
            echo "  -h, --help           显示帮助信息"
            exit 0
            ;;
        *)
            echo -e "${RED}未知选项：$1${NC}"
            exit 1
            ;;
    esac
done

# 构建命令
CMD="python3 main.py --config $CONFIG_FILE --output $OUTPUT_DIR"

if [ -n "$PROMETHEUS_URL" ]; then
    CMD="$CMD --url $PROMETHEUS_URL"
fi

for fmt in $FORMATS; do
    CMD="$CMD --format $fmt"
done

# 执行巡检
echo "执行命令：$CMD"
echo ""
eval $CMD

EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ 巡检完成${NC}"
elif [ $EXIT_CODE -eq 1 ]; then
    echo -e "${YELLOW}⚠ 巡检完成，发现严重问题${NC}"
else
    echo -e "${RED}✗ 巡检失败${NC}"
fi

exit $EXIT_CODE
