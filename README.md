# COMSOL 2.45GHz 微波電漿模擬研究

國立新竹科學園區實驗高級中等學校 第十五屆科學班個別科學研究

研究者：陳亮宇
指導教授：張存續 教授（國立清華大學）

## 研究內容

使用 COMSOL Multiphysics 建立二維軸對稱模型，探討 2.45 GHz 微波電漿的：

1. 功率-密度標度律（n_e ∝ P_in^0.73-0.78）
2. 體積波到表面波的模式轉換
3. 腔體幾何對點火功率的影響

完整研究報告見 `個別科學研究成果報告書/個別科學研究成果報告書.pdf`

## 研究流程

```mermaid
flowchart TD
    A[COMSOL Multiphysics 6.0<br/>2D 軸對稱模型] --> B{參數掃描}

    B --> C[實驗一：功率掃描<br/>P_in = 1~10⁵ W<br/>固定 r = 47.7 mm]
    B --> D[實驗二：幾何掃描<br/>r = 5~1000 mm<br/>尋找點火功率 P_cutoff]

    C --> E[VTU 數據輸出<br/>電子密度、溫度分布]
    D --> E

    E --> F[數據處理管線]
    F --> F1[generate_pin_table.py<br/>解析 VTU + 分配功率標籤]
    F1 --> F2[build_dataset.py<br/>KDE 統計聚合]

    F2 --> G{三個研究方向}

    G --> H[Research 1<br/>功率-密度標度律]
    G --> I[Research 2<br/>500W 空間分布]
    G --> J[Research 3<br/>功率-半徑趨勢]

    H --> H1[發現：n_e ∝ P_in^0.73-0.78<br/>次線性冪次律]
    I --> I1[發現：徑向尺度飽和<br/>大腔體 r>200mm]
    J --> J1[發現：P_cutoff ∝ r^-7.42<br/>截止波導點火困難]

    H1 --> K[核心結論]
    I1 --> K
    J1 --> K

    K --> K1[點火閾值與模式轉換<br/>雙邊界運行地圖]
    K --> K2[擴散-複合損失競爭<br/>限制能量耦合效率]
    K --> K3[波導截止與飽和<br/>幾何效應量化]

    style A fill:#e1f5ff
    style E fill:#fff4e1
    style K fill:#e8f5e9
    style H1 fill:#f3e5f5
    style I1 fill:#f3e5f5
    style J1 fill:#f3e5f5
```

## 資料夾結構

```
research1/          功率掃描分析（Pin vs 電子密度）
research2/          500W 電漿空間分布分析
research3/          功率-半徑趨勢分析
個別科學研究成果報告書/   LaTeX 研究報告
簡報/               Beamer 簡報
```

## 重現分析結果

```bash
# 安裝依賴
pip install -r requirements.txt

# 執行分析工具
python cli.py
```

所有圖表生成代碼位於各 research 資料夾的 `plot_*.py` 檔案。

## 數據說明

原始 VTU 模擬數據（121MB）因檔案大小限制未包含在倉庫中。

已包含的統計摘要檔案（`research1/data/all_stats.csv`）足以重現報告中的所有圖表。

## 環境

- Python 3.12
- COMSOL Multiphysics 6.0（僅用於原始模擬）
- 主要依賴：numpy, pandas, matplotlib, vtk, scipy

完整依賴清單見 `requirements.txt`
