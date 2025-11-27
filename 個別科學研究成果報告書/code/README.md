# 數據分析程式碼

本目錄包含《COMSOL 模擬 2.45GHz 圓形波導微波電漿之參數研究：不同功率下激發模式轉變分析》研究報告中所有數據分析與視覺化的完整程式碼。

## 📁 目錄結構

```
code/
├── README.md                    # 本文件
├── requirements.txt             # Python 依賴套件清單
│
├── research1_analysis/          # Research 1: Pin vs 電子密度分析
│   ├── build_dataset.py         # 數據聚合與統計計算（核心）
│   ├── generate_pin_table.py    # VTU 檔案解析與功率標註
│   ├── plot_style.py            # 統一繪圖風格配置
│   ├── plot_pin_statistics.py   # Pin vs 電子密度摘要圖（圖 3.2）
│   ├── plot_r2_comparison.py    # r2 資料集比較圖（圖 4.3）
│   └── plot_pin_density_distribution.py  # 電子密度分布圖
│
├── research2_analysis/          # Research 2: 500W 電漿徑向/軸向分析
│   ├── plot_radial_slice.py     # 徑向切片分析（圖 4.1）
│   ├── plot_axis_slice.py       # 軸向切片分析
│   └── plot_decay_radius.py     # 衰減半徑分析
│
└── research3_analysis/          # Research 3: 功率-半徑趨勢分析
    └── plot_research3_trends.py # 功率-半徑趨勢圖（圖 5.1）
```

## 🚀 快速開始

### 1. 安裝依賴套件

```bash
# 確認 Python 版本（需要 3.12+）
python --version

# 安裝所有依賴套件
pip install -r requirements.txt
```

### 2. 數據檔案說明

**⚠️ 重要**：本目錄包含範例數據（`examples/`），完整數據需從以下位置取得：
- Research 1 數據：`../../research1/data/`
- Research 2 數據：`../../research2/500W_ne+Te/`
- Research 3 數據：`../../research3/`

範例數據僅供測試程式碼功能，不包含完整分析結果。

### 3. 環境需求

- **Python**: 3.12+
- **作業系統**: macOS / Linux / Windows
- **記憶體**: 建議 8 GB 以上（處理大型 VTU 檔案時）

## 📊 主要功能

### Research 1: Pin vs 電子密度分析

#### 核心工作流程

```bash
# 1. 處理原始 VTU 檔案（需要在 research1/ 目錄執行）
cd ../../research1
./process_vtu_cases.sh datasets data

# 2. 生成 Pin vs 電子密度圖（log-log）
python plot_pin_statistics.py \
    --stats data/all_stats.csv \
    --series all \
    --scale log \
    --output plots/pin_loglog.png

# 3. 生成 r2 資料集比較圖
python plot_r2_comparison.py \
    --datasets r2=32 r2=39 r2=95 \
    --stat mode \
    --output plots/r2_compare.png
```

#### 關鍵演算法

**KDE 眾數計算**（`build_dataset.py` 第 74-91 行）：
```python
# 在對數空間進行核密度估計
log_vals = np.log10(values)
kde = gaussian_kde(log_vals)
grid = np.linspace(log_vals.min(), log_vals.max(), 512)
mode_log = grid[np.argmax(kde(grid))]
mode_val = 10 ** mode_log
```

**冪次律擬合**（`plot_pin_statistics.py`）：
```python
# 對數空間線性回歸
log_pin = np.log10(pin_values)
log_density = np.log10(density_values)
slope, intercept = np.polyfit(log_pin, log_density, deg=1)
# 結果：n_e = C * P_in^α
```

### Research 2: 500W 電漿徑向/軸向分析

```bash
# 徑向切片分析（固定高度 z）
cd ../../research2
python plot_radial_slice.py --z -50 --show

# 軸向切片分析（固定半徑 r）
python plot_axis_slice.py --radius 0 --samples 400 --show

# 衰減半徑分析
python plot_decay_radius.py --alpha 0.5 0.7 0.9 --show
```

### Research 3: 功率-半徑趨勢分析

```bash
cd ../../research3
python plot_research3_trends.py

# 輸出：
#   - research3_loglog.png （對數-對數圖）
#   - research3_linear.png （線性圖）
```

## 🔬 數據格式說明

### VTU 檔案（COMSOL 輸出）

```
格式：VTK Unstructured Grid
包含欄位：
  - Electron_density (m⁻³)
  - Electron_temperature (eV)
  - 網格點座標 (r, z)
```

### .pins 檔案（功率序列）

```
格式：純文字，空白或換行分隔
範例：
  10.0 20.0 50.0 100.0 200.0 500.0
```

### all_stats.csv（統計摘要）

```csv
dataset,pin,mode,std,min,q1,median,q3,max,valid_points,dataset_count
r2=47.7,10.0,3.8e17,1.2e17,1.5e17,2.9e17,3.7e17,4.5e17,9.3e17,12345,1
...
```

欄位說明：
- `dataset`: 資料集名稱（如 r2=47.7）
- `pin`: 輸入功率 (W)
- `mode`: KDE 眾數 (m⁻³)
- `std`: 標準差
- `min, q1, median, q3, max`: 五數摘要
- `valid_points`: 有效樣本數
- `dataset_count`: 來源資料集數量

## 🎨 繪圖風格規範

所有圖表遵循統一規範（`plot_style.py`）：

- **字體**: Times New Roman
- **字體大小**: 標籤 18pt, 刻度 14pt
- **刻度方向**: 向內 (inward)
- **次刻度**: 啟用
- **格線**: 淡灰色虛線（alpha=0.3）
- **圖例**: 框外右側
- **DPI**: 300（出版品質）

## 📝 程式碼說明

### Research 1 核心模組

#### `build_dataset.py` (193 行)
- **功能**: 資料聚合與統計計算
- **核心演算法**:
  - KDE 眾數估計（對數空間）
  - 按 Pin 值聚合統計量
  - 輸出 all_stats.csv 和 all_values.csv
- **使用**: `python build_dataset.py --datasets-dir datasets --output-dir data`

#### `generate_pin_table.py`
- **功能**: VTU 檔案解析與功率標註
- **處理流程**:
  1. 使用 `meshio` 讀取 VTU
  2. 提取電子密度場量
  3. 匹配 .pins 檔案的功率序列
  4. 輸出點級別數據

#### `plot_style.py` (227 行)
- **功能**: 統一繪圖風格配置
- **包含**:
  - AxisStyle 類別（刻度樣式）
  - FigureLayout 類別（版面配置）
  - 風格套用函數

#### `plot_pin_statistics.py`
- **功能**: 生成 Pin vs 電子密度摘要圖
- **參數**:
  - `--stats`: 統計檔案路徑
  - `--series`: mode/max/min/all
  - `--scale`: linear/log
  - `--pin-min/--pin-max`: 功率範圍
  - `--output`: 輸出檔案路徑
- **輸出**: 報告圖 3.2（log-log 圖含冪次律擬合）

#### `plot_r2_comparison.py`
- **功能**: 比較不同 r2 配置
- **參數**:
  - `--datasets`: r2 列表（如 r2=32 r2=39）
  - `--stat`: mode/max/min
- **輸出**: 報告圖 4.3（多條曲線比較）

### Research 2 核心模組

#### `plot_radial_slice.py`
- **功能**: 徑向切片分析
- **參數**:
  - `--z`: 切片高度（預設自動檢測峰值）
  - `--cases`: 指定腔體編號
  - `--show`: 顯示圖形
- **輸出**: 報告圖 4.1

#### `plot_axis_slice.py`
- **功能**: 軸向切片分析
- **參數**:
  - `--radius`: 取樣半徑
  - `--samples`: 取樣點數
- **技術**: LinearTriInterpolator 三角網格插值

#### `plot_decay_radius.py`
- **功能**: 衰減半徑分析
- **參數**:
  - `--alpha`: 衰減係數（如 0.5 0.7 0.9）
- **計算**: 密度降至 α × 峰值密度的徑向位置

### Research 3 核心模組

#### `plot_research3_trends.py`
- **功能**: 功率-半徑趨勢分析
- **輸入**: `research3 - 工作表1.csv`
- **輸出**:
  - 對數-對數圖（含冪次律擬合）
  - 線性圖
- **擬合範圍**: r < 36 mm（波導截止區）

## 🔧 疑難排解

### 常見問題

**Q: 缺少依賴套件**
```bash
# 解決方法
pip install numpy pandas matplotlib scipy vtk meshio
```

**Q: VTU 檔案讀取失敗**
```python
# 檢查檔案格式
import meshio
mesh = meshio.read("your_file.vtu")
print(mesh.point_data.keys())  # 檢查可用欄位
```

**Q: KDE 計算警告**
```
原因：數據點過少（< 2 個）
解決：檢查數據清洗步驟，確保有效值足夠
```

**Q: 圖表中文顯示亂碼**
```python
# 設定中文字體（macOS）
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
```

## 📚 相關文檔

- **完整報告**: 個別科學研究成果報告書.pdf
- **附錄 A**: COMSOL 模擬參數設定
- **附錄 B**: 數據分析方法與程式碼實作（本目錄的詳細說明）

## 🤝 聯絡方式

- **作者**: 陳亮宇
- **指導教授**: 張存續 博士
- **學校**: 國立新竹科學園區實驗高級中等學校
- **年份**: 2025

## 📌 版本資訊

- **Python**: 3.12
- **主要依賴**:
  - numpy: 2.3.3
  - pandas: 2.3.2
  - matplotlib: 3.10.6
  - scipy: 1.16.2
  - vtk: 9.5.2
  - meshio: 5.3.5

---

**最後更新**: 2025-10-20
**程式碼總行數**: ~2000 行
**生成圖表數**: 10+ 張
