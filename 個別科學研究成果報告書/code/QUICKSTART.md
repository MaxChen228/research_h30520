# 快速開始指南

## ⚡ 5 分鐘快速上手

### 步驟 1: 安裝依賴
```bash
pip install -r requirements.txt
```

### 步驟 2: 生成報告中的關鍵圖表

#### 圖 3.2 - Pin vs 電子密度（log-log）
```bash
cd ../research1
python ../個別科學研究成果報告書/code/research1_analysis/plot_pin_statistics.py \
    --stats data/all_stats.csv \
    --series all \
    --scale log \
    --output plots/figure_3_2.png
```

#### 圖 4.1 - 徑向切片分析
```bash
cd ../research2
python ../個別科學研究成果報告書/code/research2_analysis/plot_radial_slice.py \
    --z -50 \
    --output plots/figure_4_1.png
```

#### 圖 5.1 - 功率-半徑趨勢
```bash
cd ../research3
python ../個別科學研究成果報告書/code/research3_analysis/plot_research3_trends.py
```

## 🔍 驗證程式碼

### 檢查 KDE 眾數計算
```python
import numpy as np
from scipy.stats import gaussian_kde

# 模擬數據
density_values = np.random.lognormal(17, 0.5, 1000)

# KDE 眾數計算
log_vals = np.log10(density_values)
kde = gaussian_kde(log_vals)
grid = np.linspace(log_vals.min(), log_vals.max(), 512)
mode_log = grid[np.argmax(kde(grid))]
mode = 10 ** mode_log

print(f"KDE 眾數: {mode:.2e} m⁻³")
```

### 檢查冪次律擬合
```python
import numpy as np

# 模擬 Pin vs 密度數據
pin = np.array([10, 20, 50, 100, 200, 500, 1000])
density = 1e15 * pin ** 0.75

# 對數空間線性回歸
log_pin = np.log10(pin)
log_density = np.log10(density)
slope, intercept = np.polyfit(log_pin, log_density, deg=1)

print(f"冪次指數 α = {slope:.2f}")
print(f"係數 C = {10**intercept:.2e}")
```

## 📊 主要程式檔案對應表

| 報告圖表 | 程式檔案 | 位置 |
|---------|---------|------|
| 圖 3.2 | plot_pin_statistics.py | research1_analysis/ |
| 圖 4.1 | plot_radial_slice.py | research2_analysis/ |
| 圖 4.3 | plot_r2_comparison.py | research1_analysis/ |
| 圖 5.1 | plot_research3_trends.py | research3_analysis/ |

## 🛠️ 常用指令

### 處理新的 VTU 檔案
```bash
cd ../research1
python ../個別科學研究成果報告書/code/research1_analysis/generate_pin_table.py \
    new_data.vtu \
    new_data.pins
```

### 重新生成統計表
```bash
cd ../research1
python ../個別科學研究成果報告書/code/research1_analysis/build_dataset.py \
    --datasets-dir datasets \
    --output-dir data
```

### 批次生成所有圖表
```bash
# 在 research1/ 目錄
./chart_cli.py  # 互動式選單
```

## 💡 技巧與訣竅

### 自訂功率範圍
```bash
python plot_pin_statistics.py \
    --stats data/all_stats.csv \
    --pin-min 100 \
    --pin-max 1000 \
    --output plots/custom_range.png
```

### 比較特定 r2 配置
```bash
python plot_r2_comparison.py \
    --datasets r2=32 r2=47.7 r2=95 \
    --stat mode \
    --output plots/custom_r2.png
```

### 調整圖表風格
編輯 `plot_style.py` 中的參數：
```python
# 修改字體大小
mpl.rcParams['axes.labelsize'] = 20  # 預設 18

# 修改刻度長度
mpl.rcParams['xtick.major.size'] = 8.0  # 預設 6.0
```

## 🐛 快速除錯

### 檔案找不到
```bash
# 確認當前目錄
pwd

# 列出可用檔案
ls data/*.csv
ls datasets/*/
```

### 記憶體不足
```python
# 在 build_dataset.py 中分批處理
# 修改第 137 行：
all_values.append(values_df.sample(frac=0.5))  # 只取 50%
```

### 圖表不顯示
```python
# 加入互動模式
import matplotlib.pyplot as plt
plt.ion()  # 啟用互動模式
plt.show(block=True)  # 阻塞直到關閉視窗
```

## 📞 需要幫助？

1. 查看 `README.md` 完整文檔
2. 檢查報告附錄 B「數據分析方法與程式碼實作」
3. 閱讀程式碼中的 docstring 註解

---

**最後更新**: 2025-10-20
