# 電漿數據整合與繪圖流程指南

本文件說明如何使用當前專案的腳本，從多個 VTU 模擬檔案建構統合資料表，並依需求繪製 Pin 與電子密度的關係圖。遵循此文件即可完成整個流程。

---

## 1. 專案結構概覽

```
research1/
├─ datasets/               # 以子資料夾存放每個案例 (例如 r2=32/) 下的 .vtu 與 .pins
├─ data/                   # `process_vtu_cases.sh` 產生的統合資料
├─ plots/                  # 建議儲存輸出的圖檔位置
├─ electron_density_env/   # Python 虛擬環境（已安裝所需套件）
├─ generate_pin_table.py   # VTU → 表格轉換核心邏輯
├─ build_dataset.py        # 整併所有案例，輸出統合資料表
├─ plot_pin_statistics.py        # 根據統計表繪製圖形
├─ plot_pin_density_distribution.py  # 依 Pin 範圍繪製密度分布曲線
├─ plot_pin_r2_kde.py             # 同功率多 r2 KDE 比較
├─ plot_r2_comparison.py          # 不同 r2 的彙總曲線比較圖
├─ process_vtu_cases.sh           # 批次整合工具
├─ chart_cli.py                   # 單一入口的互動式繪圖 CLI
└─ analyze_pin_gap.py             # 檢視目前 Pin 覆蓋情況與缺口
```

---

## 2. 先決條件

1. **Python 環境**：建議使用隨附的虛擬環境。
   ```bash
   source electron_density_env/bin/activate
   ```
   若在互動式腳本或 `.sh` 中會自動尋找此環境，通常無須手動啟用。

2. **VTU 與 Pin 列表**：
   - 每個案例需提供 `datasets/<name>.vtu` 與同名的 `datasets/<name>.pins`。
   - `.pins` 內容為對應時間步的 Pin 值，空白或換行分隔。
   - 範例：
     ```
     10 15 20 25
     ```

---

## 3. 建構統合資料

### 3.1 將新案例加入 `datasets/`
1. 在 `datasets/` 下建立以條件命名的資料夾（例如 `r2=32/`）。
2. 將該案例的 `*.vtu` 與同名 `.pins` 放進資料夾內；若沒有子資料夾，預設 dataset 名為檔案名稱。
3. `.pins` 內容為對應時間步的 Pin 值，空白或換行分隔。

### 3.2 執行批次整合
```bash
./process_vtu_cases.sh [datasets_dir] [output_dir]
```
- 省略參數即使用預設：`datasets/`、`data/`。
- 腳本會：
  1. 處理所有 `.vtu`，將其點資料合併成 `data/all_values.csv`。
  2. 依 Pin 聚合，計算統計量（眾數、標準差、四分位、最大最小、樣本數、來源案例數），寫入 `data/all_stats.csv`。
  3. 產出 `data/dataset_index.txt`，列出成功處理的案例名稱。
- 若需要同時輸出一張圖，可再加參數（第 3~5 個）：
  ```bash
  ./process_vtu_cases.sh datasets data plots/pin_auto.png 20 5000
  ```
  上例會在整合後自動呼叫繪圖腳本，生成 Pin ∈ [20, 5000] 的總覽圖。

### 3.3 核對輸出
- `data/all_values.csv`：每筆有效點數據（欄位：`dataset`, `pin`, `point_index`, `value` 等）。
- `data/all_stats.csv`：每個 Pin 的統計摘要。
- `data/dataset_index.txt`：資料來源列表。

---

## 4. 繪圖工具

### 4.1 `chart_cli.py`（建議入口）
執行：
```bash
python chart_cli.py
```
（請先切換到 `research1/` 目錄，再執行上述指令。若已啟動虛擬環境，可直接使用系統的 `python`。）

互動流程：
1. 先挑選資料集（預設 `ALL`，會列出 `datasets/` 底下的子資料夾名稱）。
2. 選擇功能：
   - Pin vs. 電子密度摘要圖（可選眾數/最大/最小/全部，並指定座標尺度）。
   - 電子密度分布（KDE）。
   - 同功率 KDE 比較（選定 Pin 後挑多個 r2）。
   - r2 資料集比較圖（不同 r2 聚合線）。
   - 檢視 Pin 覆蓋缺口。
3. 依提示輸入 Pin 範圍與輸出路徑（直接 Enter 只顯示、不存檔）。

CLI 會檢查 `data/all_stats.csv` 與 `data/all_values.csv` 是否存在，並顯示實際執行的 Python 指令，方便後續複製使用。

### 4.2 直接呼叫繪圖程式
若希望寫入腳本或排程，可直接使用：
```bash
python plot_pin_statistics.py \
  --stats data/all_stats.csv \
  --series all \
  --scale log \
  --pin-min 30 --pin-max 2000 \
  --output plots/pin_30_2000_log.png
```
- `--dataset`：指定資料集（例如 `r2=32`）；預設 `ALL`。
- `--series`：`mode`、`max`、`min`、`all`。
- `--scale`：`linear` 或 `log`。
- `--pin-min` / `--pin-max`：Pin 篩選條件，可省略代表不限制。
- `--output`：輸出圖檔路徑；省略時會改成互動顯示，不會儲存檔案。

若要在同一張圖比較多個 r2，請改用 `plot_r2_comparison.py`：

```bash
python plot_r2_comparison.py \
  --datasets r2=32 r2=39 r2=95 \
  --stat max \
  --pin-min 30 --pin-max 5000 \
  --output plots/r2_compare_max.png
```

- `--datasets`：至少兩個 r2 名稱（可輸入 `32` 系統會自動補上 `r2=`）。
- `--stat`：選擇單一統計量（`mode` / `max` / `min`）。
- `--output`：輸出圖檔路徑；省略時改為互動顯示。
- 其餘選項與 `plot_pin_statistics.py` 相同，軸向固定使用 log-log。

若要比較同一個 Pin 下不同 r2 的密度分布，可使用：

```bash
python plot_pin_r2_kde.py \
  --pin 500 \
  --datasets r2=32 r2=39 r2=95 \
  --output plots/pin500_r2_kde.png
```

- `--pin`：指定功率值（必填），會比對所有資料集的精確 Pin。
- `--datasets`：至少兩個 r2 名稱，支援 `32` 或 `r2=32` 的寫法。
- `--output`：輸出圖檔路徑；省略時改為互動顯示。

### 4.3 圖形格式特性
- 坐標軸字體為 Times New Roman，字體放大並統一。
- 刻度向內，格線保持淡灰色。
- 圖例置於圖框外側右方，避免遮擋資料。
- Log-log 模式下會自動擬合主要系列並標示斜率（優先順序：眾數 → 最大 → 最小），若資料不足會在終端提示警告。

### 4.4 Pin 覆蓋檢視
```bash
python analyze_pin_gap.py --max-gap 1000
```

`--max-gap` 用來指定要關注的「間距門檻」（單位 W）。腳本會列出所有已覆蓋的 Pin 值，並將間距大於門檻的相鄰 Pin 對列為缺口，方便安排後續模擬以補齊資料。

---

## 5. 常見問題與除錯

| 狀況 | 解法 |
| --- | --- |
| `… pins file missing` | `.vtu` 沒有對應 `.pins`；補上同名檔案或將該 VTU 移出資料夾。 |
| `No VTU files found` | `datasets/` 內沒有任何 `.vtu`。確認路徑或參數是否正確。 |
| `Statistics file not found` | 尚未執行 `process_vtu_cases.sh` 建立統合資料。 |
| `numpy/matplotlib/pandas is required` | 虛擬環境未啟用或缺套件；執行 `source electron_density_env/bin/activate` 後再試。 |
| log 模式未顯示擬合線 | Pin 或資料值出現 0/負值、或該系列點數少於 2 個。檢查原始資料。 |

---

## 6. 推薦工作流程（摘要）

1. 把新的 `.vtu` + `.pins` 放進 `research1/datasets/`。
2. 執行 `./process_vtu_cases.sh` 更新整合資料。
3. 需要圖表時，執行 `python chart_cli.py`，依選單輸入資料集、Pin 範圍與圖表類型。
4. 若需自動化或批次繪圖，可直接呼叫各 Python 腳本並調整參數。

---

遇到新需求或異常，可先檢查本指南所列步驟，再確認上述輸出的 CSV 與圖檔是否刷新成功。若要擴充功能，建議沿用既有腳本的介面與資料格式，確保與整合流程相容。

