#!/bin/bash
# 電漿模擬分析工具啟動腳本

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================"
echo "  電漿模擬數據分析工具"
echo "========================================"
echo ""

# 檢查虛擬環境
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  虛擬環境不存在，正在創建...${NC}"
    python3.12 -m venv venv
    echo -e "${GREEN}✅ 虛擬環境創建完成${NC}"
fi

# 啟動虛擬環境
echo -e "${GREEN}🔧 啟動虛擬環境...${NC}"
source venv/bin/activate

# 檢查依賴
if ! python -c "import numpy, pandas, matplotlib" &> /dev/null; then
    echo -e "${YELLOW}⚠️  依賴套件未安裝，正在安裝...${NC}"
    pip install -r requirements.txt -q
    echo -e "${GREEN}✅ 依賴安裝完成${NC}"
fi

echo -e "${GREEN}🚀 啟動統一 CLI...${NC}"
echo ""

# 執行 CLI
python cli.py

# 退出時提示
echo ""
echo -e "${GREEN}再見！${NC}"
