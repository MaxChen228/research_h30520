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
    A[COMSOL Multiphysics 6.0<br/>2D 軸對稱 + 電磁-電漿耦合模組] --> B{參數掃描設計}

    B --> C[實驗一：功率掃描<br/>P_in = 1~10⁵ W<br/>固定 r = 47.7mm]
    B --> D[實驗二：幾何掃描<br/>r = 5~1000mm<br/>尋找 P_cutoff]

    C --> E[VTU 輸出<br/>電子密度 n_e<br/>能量沉積分布]
    D --> E

    E --> F[數據處理]
    F --> F1[generate_pin_table.py<br/>VTU 解析]
    F1 --> F2[build_dataset.py<br/>KDE 統計]

    F2 --> G{核心物理發現}

    G --> M1[轉變一：點火閾值<br/>E > E_crit 雪崩式擊穿<br/>低功率出現斷層]
    G --> M2[轉變二：模式轉換<br/>n_e > n_cr 時發生<br/>E-mode → W-mode]

    M1 --> T1[區域 III<br/>未點火<br/>P < P_cutoff]
    M2 --> T2[區域 II<br/>體積波加熱<br/>E-mode]
    M2 --> T3[區域 I<br/>表面波加熱<br/>W-mode]

    T1 --> R1[Research 1<br/>功率-密度標度律]
    T2 --> R1
    T3 --> R1

    T2 --> R2[Research 2<br/>空間分布分析]
    T3 --> R2

    T1 --> R3[Research 3<br/>幾何效應]
    T2 --> R3

    R1 --> S1[n_e ∝ P_in^0.73-0.78<br/>擴散與體複合並存]
    R2 --> S2[能量沉積從體積中心<br/>轉移到介面薄層<br/>δ_p ∝ 1/√n_e]
    R3 --> S3[P_cutoff ∝ r^-7.42<br/>截止波導漸逝波<br/>徑向飽和 r>200mm]

    S1 --> K[三區域運行地圖]
    S2 --> K
    S3 --> K

    K --> K1[點火閾值 E_crit<br/>決定能否產生電漿]
    K --> K2[臨界密度 n_cr<br/>決定加熱模式]
    K --> K3[波導截止與物理尺度<br/>決定幾何耦合效率]

    style A fill:#e1f5ff
    style M1 fill:#ffe1e1
    style M2 fill:#ffe1e1
    style T1 fill:#f5f5f5
    style T2 fill:#fff4e1
    style T3 fill:#e8f5e9
    style K fill:#e3f2fd
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
- COMSOL Multiphysics 6.2
- 主要依賴：numpy, pandas, matplotlib, vtk, scipy

完整依賴清單見 `requirements.txt`
