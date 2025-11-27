# 500W_ne+Te 資料狀態說明

## 檔案清單
- 來源資料夾：`research2/500W_ne+Te/`
- 共 17 個 VTU 檔案，檔名格式 `plasma_500W(<index>).vtu`，`<index>` 為 1–17。

## 檔案結構
- 每個檔案皆為 `UnstructuredGrid`（三角形單元）。
- 節點數與單元數因檔案而異，範圍如下（清理後僅列有效節點數）：
  | 檔名 | 節點數 |
  | --- | --- |
  | plasma_500W(1).vtu | 339 |
  | plasma_500W(2).vtu | 419 |
  | plasma_500W(3).vtu | 596 |
  | plasma_500W(4).vtu | 524 |
  | plasma_500W(5).vtu | 588 |
  | plasma_500W(6).vtu | 649 |
  | plasma_500W(7).vtu | 704 |
  | plasma_500W(8).vtu | 749 |
  | plasma_500W(9).vtu | 901 |
  | plasma_500W(10).vtu | 1055 |
  | plasma_500W(11).vtu | 1192 |
  | plasma_500W(12).vtu | 1333 |
  | plasma_500W(13).vtu | 1923 |
  | plasma_500W(14).vtu | 2497 |
  | plasma_500W(15).vtu | 3067 |
  | plasma_500W(16).vtu | 4500 |
  | plasma_500W(17).vtu | 5952 |

## 點資料內容
- `Electron_temperature` (Float64)
- `Electron_density` (Float64)

清理前上述欄位大部分節點為 `NaN`。已執行批次腳本移除所有溫度與密度任一為 `NaN` 的節點，並同步刪除引用這些節點的三角形單元；目前檔案內的節點資料皆為有限數值。

## 注意事項
1. 清理後的節點座標與原始網格無法直接對應（節點數不同）。若需與原始完整網格比較，請保留原始檔案的備份。
2. 檔案內沒有 FieldData 或時間步資訊，僅能以檔名編號辨識順序。
3. 若要整合進既有 pipeline，可將這批檔案複製到 `datasets/` 內對應的 r2 子資料夾，另行建立 `.pins` 列表與擬合流程。
4. 虛擬環境 `electron_density_env/` 已複製一份至 `research2/` 供獨立使用。

## 徑向切片繪圖
- `plot_radial_slice.py` 可在固定 z 位置比較 17 個腔體的電子密度徑向分布。
- 預設會從 `500W_ne+Te/` 讀取 `plasma_500W(*).vtu`，並在 `plots/` 產生 `radial_slice_z…png`。
- 主要參數：
  - `--z`: 可選，手動指定切片高度（預設會找出各檔案電子密度的峰值所在 z）。
  - `--cases`: 可選，輸入索引清單僅繪指定腔體。
  - `--samples`: 徑向取樣點數（預設 400）。
  - `--show`: 繪製後開啟視窗檢視。
  - `--output`: 手動指定輸出路徑。
  - 若未提供 `--z`，執行時會列出各檔案自動選到的峰值 z，並輸出為 `radial_slice_z_peak-density.png`。
- 範例：
  ```bash
  electron_density_env/bin/python plot_radial_slice.py --z -50 --show
  ```
  上例會繪製全部 17 個腔體並在視窗顯示，同時將圖片存到 `plots/radial_slice_z-50p0.png`。
- `plot_axis_slice.py` 會沿著指定半徑（預設 r=0）取樣，輸出高度 h 與電子密度的關係曲線。
  - `--radius`: 指定取樣半徑。
  - `--samples`: 軸向取樣點數。
  - `--cases`: 限制套用檔案索引。
  - 執行時會列出各檔案的 h 範圍與峰值所在位置，並輸出 `axis_slice_r*.png`。
- `plot_decay_radius.py` 計算徑向密度衰減到 `alpha×峰值` 時的位置，並與腔體半徑對照：
  - `--alpha`: 衰減係數 (0~1)，可一次指定多個值。
  - `--z`: 可覆寫切片高度，預設使用各檔峰值。
  - `--samples`, `--cases`, `--show`, `--output` 與其他腳本一致。
  - 繪圖同時會描出 `y=x` 虛線方便比較。

