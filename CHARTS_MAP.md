# 圖表地圖 - 所有可生成的圖表總覽

本文件列出三個研究領域可以生成的所有圖表類型及其說明。

---

## 📊 Research 1: Pin vs 電子密度分析

### 1.1 Pin vs 電子密度摘要圖
**腳本**: `plot_pin_statistics.py`
**輸出範例**: `plots/pin_ALL_mode_log_30_2000.png`

**內容**:
- X 軸：Pin 功率 (W)
- Y 軸：電子密度 (m⁻³)
- 系列選項：
  - 眾數 (mode) - KDE 峰值
  - 最大值 (max)
  - 最小值 (min)
  - 全部 (all) - 三條線同時顯示

**座標選項**:
- Linear（線性座標）
- Log-log（對數座標，自動擬合冪次律）

**用途**: 觀察 Pin 與電子密度的整體趨勢，識別電離閾值

---

### 1.2 電子密度分布圖 (KDE)
**腳本**: `plot_pin_density_distribution.py`
**輸出範例**: `plots/pin_density_ALL_30_2000.png`

**內容**:
- X 軸：電子密度 (m⁻³, log scale)
- Y 軸：機率密度
- 顯示指定 Pin 範圍內所有資料點的密度分布

**用途**: 分析特定功率範圍的電子密度分布特性

---

### 1.3 r2 資料集比較圖
**腳本**: `plot_r2_comparison.py`
**輸出範例**: `plots/pin_compare_mode_r2-32-r2-39-r2-95.png`

**內容**:
- X 軸：Pin 功率 (W, log scale)
- Y 軸：電子密度 (m⁻³, log scale)
- 多條曲線：不同 r2 配置（如 r2=32, r2=39, r2=95）
- 統計量：眾數/最大值/最小值（三選一）

**用途**: 比較不同 r2 參數對電子密度的影響

---

### 1.4 同功率 KDE 比較圖
**腳本**: `plot_pin_r2_kde.py`
**輸出範例**: `plots/pin_kde_500_r2-32-r2-39-r2-95.png`

**內容**:
- X 軸：電子密度 (m⁻³, log scale)
- Y 軸：機率密度
- 多條曲線：同一 Pin 下不同 r2 的密度分布

**用途**: 比較相同功率下，不同 r2 配置的密度分布差異

---

### 1.5 Pin 覆蓋缺口分析
**腳本**: `analyze_pin_gap.py`
**輸出**: 終端機文字輸出（無圖表）

**內容**:
- 列出所有已覆蓋的 Pin 值
- 標示超過指定門檻的 Pin 間距
- 建議需補充的模擬功率點

**用途**: 規劃後續模擬，補齊資料缺口

---

## 🔬 Research 2: 500W 電漿徑向/軸向分析

### 2.1 徑向切片分析圖
**腳本**: `plot_radial_slice.py`
**輸出範例**: `plots/radial_slice_z-50p0.png`

**內容**:
- X 軸：徑向距離 r (mm)
- Y 軸：電子密度 (m⁻³)
- 多條曲線：17 個腔體配置（plasma_500W(1-17).vtu）
- 固定高度 z 的徑向密度分布

**參數**:
- `--z`: 切片高度（預設為峰值密度位置）
- `--cases`: 指定繪製的腔體編號

**用途**: 分析電子密度的徑向衰減特性

---

### 2.2 軸向切片分析圖
**腳本**: `plot_axis_slice.py`
**輸出範例**: `plots/axis_slice_r0.png`

**內容**:
- X 軸：軸向位置 h (mm)
- Y 軸：電子密度 (m⁻³)
- 多條曲線：17 個腔體配置
- 固定半徑 r 的軸向密度分布

**參數**:
- `--radius`: 取樣半徑（預設 r=0，中軸線）
- `--samples`: 取樣點數（預設 400）

**用途**: 分析電子密度的軸向分布與峰值位置

---

### 2.3 衰減半徑分析圖
**腳本**: `plot_decay_radius.py`
**輸出範例**: `plots/decay_radius_alpha_0p5_0p7_0p9.png`

**內容**:
- X 軸：腔體半徑 (mm)
- Y 軸：衰減半徑 (mm)
- 多條曲線：不同衰減係數 α（如 0.5, 0.7, 0.9）
- 虛線 y=x：參考線

**說明**:
- 衰減半徑 = 密度降至 α×峰值密度 的徑向位置
- α=0.5 表示半高寬位置

**用途**: 量化電漿束縛效果，評估不同腔體的密度分布範圍

---

## 📈 Research 3: 功率-半徑趨勢分析

### 3.1 功率-半徑對數圖
**腳本**: `plot_research3_trends.py`
**輸出**: `research3/research3_loglog.png`

**內容**:
- X 軸：半徑 (mm, log scale)
- Y 軸：平均功率 (W, log scale)
- 紅色圓點：實驗資料
- 藍色虛線：冪次律擬合（r < 36mm）
- 標註擬合參數與決定係數 R²

**用途**: 分析功率與半徑的冪次律關係，獲得縮放指數

---

### 3.2 功率-半徑線性圖
**腳本**: `plot_research3_trends.py`
**輸出**: `research3/research3_linear.png`

**內容**:
- X 軸：半徑 (mm, linear scale)
- Y 軸：平均功率 (W, linear scale)
- 藍色圓點：實驗資料
- 橙色虛線：線性擬合

**用途**: 直觀展示功率-半徑關係，適合非對數分析

---

## 🎨 圖表風格統一規範

所有圖表遵循以下設計規範：

### 字型
- 主字型：Times New Roman
- 標籤字體：18pt
- 刻度字體：14pt

### 圖表元素
- **刻度方向**：向內（inward）
- **次刻度**：啟用
- **格線**：淡灰色虛線（`--`, alpha=0.3）
- **圖例位置**：框外右側
- **線寬**：主線 2.0，輔助線 1.4

### 顏色配置
- 研究 1：藍色系（主線藍色 #2c3e50）
- 研究 2：彩虹色譜（區分 17 個腔體）
- 研究 3：紅色/藍色對比

---

## 📁 輸出目錄結構

```
research/
├── research1/plots/          # Research 1 所有圖表
├── research2/plots/          # Research 2 所有圖表
└── research3/
    ├── research3_loglog.png  # 對數圖
    └── research3_linear.png  # 線性圖
```

---

## 🚀 快速生成指令

### 使用統一 CLI（推薦）
```bash
python cli.py
# 然後依照選單選擇研究領域與圖表類型
```

### 直接命令行（進階用戶）

**Research 1:**
```bash
# Pin 摘要圖
python research1/plot_pin_statistics.py --stats research1/data/all_stats.csv \
  --series all --scale log --pin-min 30 --pin-max 2000 --output plots/summary.png

# r2 比較圖
python research1/plot_r2_comparison.py --datasets r2=32 r2=39 r2=95 \
  --stat mode --output plots/r2_compare.png
```

**Research 2:**
```bash
# 徑向切片
python research2/plot_radial_slice.py --z -50 --show

# 軸向切片
python research2/plot_axis_slice.py --radius 0 --show

# 衰減半徑
python research2/plot_decay_radius.py --alpha 0.5 0.7 0.9 --show
```

**Research 3:**
```bash
cd research3
python plot_research3_trends.py
```

---

## 📊 圖表數量統計

| 研究領域 | 圖表類型數 | 可變參數組合 |
|---------|-----------|-------------|
| Research 1 | 5 種 | 無限（依資料集與參數） |
| Research 2 | 3 種 | 無限（依參數） |
| Research 3 | 2 種 | 固定（基於單一 CSV） |
| **總計** | **10 種** | **高度可配置** |

---

**更新日期**: 2025-10-19
**維護者**: 電漿模擬分析團隊
