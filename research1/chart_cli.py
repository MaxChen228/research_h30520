#!/usr/bin/env python3
"""Interactive CLI for charting plasma datasets."""

from __future__ import annotations

import re
import subprocess
import sys
import textwrap
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_STATS = PROJECT_ROOT / "data/all_stats.csv"
DEFAULT_VALUES = PROJECT_ROOT / "data/all_values.csv"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "plots"
PYTHON_BIN = PROJECT_ROOT / "electron_density_env" / "bin" / "python"
if not PYTHON_BIN.exists():
    PYTHON_BIN = Path(sys.executable)


def slugify(value: str) -> str:
    """Convert dataset names into filesystem-friendly slugs."""
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    lowercase = ascii_value.lower()
    cleaned = re.sub(r"[^a-z0-9]+", "-", lowercase).strip("-")
    return cleaned or "dataset"


def normalize_path(path: str) -> Path:
    if not path:
        return DEFAULT_OUTPUT_DIR
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return PROJECT_ROOT / candidate


@dataclass
class DatasetEntry:
    name: str
    pin_count: int
    pin_min: Optional[float] = None
    pin_max: Optional[float] = None


class ChartCLI:
    def __init__(self, stats_path: Path, values_path: Path) -> None:
        self.stats_path = stats_path
        self.values_path = values_path
        self._stats_df: pd.DataFrame | None = None
        self.datasets = self._load_datasets()
        self.current_dataset = self.datasets[0].name if self.datasets else "ALL"

    # ------------------------------------------------------------------ loading helpers
    def _get_stats_df(self) -> pd.DataFrame:
        if self._stats_df is not None:
            return self._stats_df
        if not self.stats_path.exists():
            raise FileNotFoundError(f"Statistics file not found: {self.stats_path}")
        self._stats_df = pd.read_csv(self.stats_path)
        return self._stats_df

    def _load_datasets(self) -> List[DatasetEntry]:
        try:
            df = self._get_stats_df()[["dataset", "pin"]].copy()
        except Exception:
            return [DatasetEntry("ALL", 0)]

        if df.empty:
            return [DatasetEntry("ALL", 0)]

        df["dataset"] = df["dataset"].astype(str)
        df["pin_numeric"] = pd.to_numeric(df["pin"], errors="coerce")

        global_valid = df["pin_numeric"].dropna()
        all_entry = DatasetEntry(
            "ALL",
            int(global_valid.nunique()),
            float(global_valid.min()) if not global_valid.empty else None,
            float(global_valid.max()) if not global_valid.empty else None,
        )

        entries: List[DatasetEntry] = []
        for dataset, group in df.groupby("dataset"):
            if dataset.strip().upper() == "ALL":
                continue
            numeric = group["pin_numeric"].dropna()
            pin_count = int(numeric.nunique())
            pin_min = float(numeric.min()) if pin_count else None
            pin_max = float(numeric.max()) if pin_count else None
            entries.append(DatasetEntry(str(dataset), pin_count, pin_min, pin_max))

        def sort_key(entry: DatasetEntry):
            name = entry.name
            if name == "ALL":
                return (-1, 0.0)
            if name.lower().startswith("r2="):
                try:
                    return (0, float(name.split("=", 1)[1]))
                except ValueError:
                    pass
            return (1, name.lower())

        entries.sort(key=sort_key)
        return [all_entry] + entries

    def refresh_datasets(self) -> None:
        self._stats_df = None
        self.datasets = self._load_datasets()
        if self.datasets:
            if self.current_dataset not in {d.name for d in self.datasets}:
                self.current_dataset = self.datasets[0].name
        else:
            self.current_dataset = "ALL"

    # ------------------------------------------------------------------ dataset selection
    def select_dataset(self) -> str:
        self.refresh_datasets()
        while True:
            print("\n可用資料集：")
            name_w, count_w, range_w = self._column_widths()
            header_name = "名稱".ljust(name_w)
            header_count = "Pin 筆數".rjust(count_w)
            header_range = "Pin 範圍 (W)".ljust(range_w)
            print(f"     {header_name}  {header_count}  {header_range}")
            print(f"     {'-' * name_w}  {'-' * count_w}  {'-' * range_w}")
            for idx, entry in enumerate(self.datasets, start=1):
                prefix = "*" if entry.name == self.current_dataset else " "
                label = f" {prefix} {idx:>2}) "
                name_field = entry.name.ljust(name_w)
                count_field = str(entry.pin_count).rjust(count_w)
                range_field = self._format_pin_range(entry).ljust(range_w)
                print(f"{label}{name_field}  {count_field}  {range_field}")
            raw = input(f"選擇資料集 (Enter 使用 {self.current_dataset}): ").strip()
            if not raw:
                return self.current_dataset
            if raw.isdigit():
                idx = int(raw)
                if 1 <= idx <= len(self.datasets):
                    self.current_dataset = self.datasets[idx - 1].name
                    return self.current_dataset
            for entry in self.datasets:
                if entry.name.lower() == raw.lower():
                    self.current_dataset = entry.name
                    return self.current_dataset
            print("⚠️ 無效的輸入，請重新選擇。")

    def select_multiple_datasets(self) -> List[str]:
        self.refresh_datasets()
        available = [entry.name for entry in self.datasets if entry.name != "ALL"]
        if not available:
            raise SystemExit("目前沒有可比較的個別資料集。")

        print("\n可比較的 r2 資料集：")
        for idx, name in enumerate(available, start=1):
            entry = next(e for e in self.datasets if e.name == name)
            range_info = self._format_pin_range(entry)
            print(f"  {idx:>2}) {name:<12}  Pin 筆數 {entry.pin_count:<4}  範圍 {range_info}")

        return self._multi_select_from_names(available, min_count=2)

    def _column_widths(self) -> tuple[int, int, int]:
        name_w = max(len("名稱"), *(len(entry.name) for entry in self.datasets))
        count_w = max(len("Pin 筆數"), *(len(str(entry.pin_count)) for entry in self.datasets))
        range_w = max(len("Pin 範圍 (W)"), *(len(self._format_pin_range(entry)) for entry in self.datasets))
        return name_w, count_w, range_w

    @staticmethod
    def _format_pin_range(entry: DatasetEntry) -> str:
        if entry.pin_min is None or entry.pin_max is None:
            return "—"
        left = ChartCLI._format_pin_value(entry.pin_min)
        right = ChartCLI._format_pin_value(entry.pin_max)
        if left == right:
            return left
        return f"{left}–{right}"

    @staticmethod
    def _format_pin_value(value: float) -> str:
        value = float(value)
        if value.is_integer():
            if abs(value) >= 1000:
                return f"{value:,.0f}"
            return f"{int(value)}"
        if abs(value) >= 1000:
            return f"{value:,.0f}"
        return f"{value:g}"

    @staticmethod
    def _normalize_dataset_name(name: str) -> str:
        name = name.strip()
        if name.lower().startswith("r2="):
            return name
        return f"r2={name}"

    def _multi_select_from_names(self, available: List[str], raw: Optional[str] = None, *, min_count: int = 1) -> List[str]:
        available_sorted = list(available)
        available_map = {name.lower(): name for name in available_sorted}

        def parse_tokens(text: str) -> List[str]:
            tokens: List[str] = []
            for chunk in text.split(','):
                tokens.extend(chunk.strip().split())
            return [tok for tok in tokens if tok]

        while True:
            if raw is None:
                print("\n可選擇的資料集：")
                for idx, name in enumerate(available_sorted, start=1):
                    print(f"  {idx:>2}) {name}")
                raw = input("輸入選項（支援 1-3,5 或 r2=32 / 32 形式）: ").strip()
            if not raw:
                print("⚠️ 請至少輸入一個資料集。")
                raw = None
                continue

            tokens = parse_tokens(raw)
            chosen: List[str] = []

            def add_choice(name: str) -> None:
                if name not in chosen:
                    chosen.append(name)

            valid = True
            for token in tokens:
                if '-' in token:
                    parts = token.split('-')
                    if len(parts) == 2 and all(part.strip().isdigit() for part in parts if part.strip()):
                        start, end = (int(part.strip()) for part in parts)
                        step = 1 if start <= end else -1
                        for idx in range(start, end + step, step):
                            if 1 <= idx <= len(available_sorted):
                                add_choice(available_sorted[idx - 1])
                            else:
                                print(f"⚠️ 編號 {idx} 超出範圍。")
                                valid = False
                                break
                        if not valid:
                            break
                        continue
                normalized = self._normalize_dataset_name(token)
                if normalized.lower() in available_map:
                    add_choice(available_map[normalized.lower()])
                    continue
                if token.isdigit():
                    idx = int(token)
                    if 1 <= idx <= len(available_sorted):
                        add_choice(available_sorted[idx - 1])
                        continue
                print(f"⚠️ 找不到對應資料集：{token}")
                valid = False
                break

            if not valid:
                raw = None
                continue
            if len(chosen) < min_count:
                print(f"⚠️ 至少需選擇 {min_count} 個資料集。")
                raw = None
                continue
            return chosen

    # ------------------------------------------------------------------ pin & dataset filtering
    def prompt_pin_value(self) -> float:
        try:
            df = self._get_stats_df()
        except FileNotFoundError as exc:
            raise SystemExit(str(exc)) from exc

        pin_values = np.sort(df["pin"].dropna().unique())
        if pin_values.size == 0:
            raise SystemExit("統計表中沒有 Pin 資料。")

        print("\n可用 Pin 值 (W)：")
        formatted = ", ".join(f"{val:g}" for val in pin_values)
        print(textwrap.fill(formatted, width=80, subsequent_indent="    "))

        while True:
            raw = input("選擇 Pin 值 (W): ").strip()
            if not raw:
                print("⚠️ 請輸入數值。")
                continue
            try:
                value = float(raw)
            except ValueError:
                print("⚠️ 非法數值，請重新輸入。")
                continue
            matches = pin_values[np.isclose(pin_values, value, atol=1e-6)]
            if matches.size == 0:
                nearest = pin_values[np.argmin(np.abs(pin_values - value))]
                print(f"⚠️ 找不到 {value:g} W，最接近的是 {nearest:g} W。請輸入列表中的值。")
                continue
            return float(matches[0])

    def select_datasets_for_pin(self, pin_value: float) -> List[str]:
        df = self._get_stats_df()
        mask = np.isclose(df["pin"], pin_value, atol=1e-6)
        available = sorted(df.loc[mask, "dataset"].astype(str).unique())
        if not available:
            raise SystemExit(f"Pin {pin_value:g} W 沒有可用資料集。")

        print("\n在 Pin = {0:g} W 可用的資料集：".format(pin_value))
        for idx, name in enumerate(available, start=1):
            print(f"  {idx:>2}) {name}")
        return self._multi_select_from_names(available, min_count=2)

    # ------------------------------------------------------------------ prompts
    def prompt_pin_range(self) -> tuple[Optional[float], Optional[float]]:
        def to_float(value: str) -> Optional[float]:
            value = value.strip()
            if not value:
                return None
            try:
                return float(value)
            except ValueError:
                return None

        min_val = to_float(input("Pin 最小值 (空白表示不限): "))
        max_val = to_float(input("Pin 最大值 (空白表示不限): "))
        if min_val is not None and max_val is not None and min_val > max_val:
            print("⚠️ 最小值大於最大值，將自動交換。")
            min_val, max_val = max_val, min_val
        return min_val, max_val

    def prompt_series(self) -> str:
        options = {
            "1": ("mode", "眾數 (KDE peak)"),
            "2": ("max", "最大值"),
            "3": ("min", "最小值"),
            "4": ("all", "全部 (眾數 + 最大 + 最小)"),
        }
        while True:
            print("\n選擇要繪製的資料類型：")
            for key, (_, desc) in options.items():
                print(f"  {key}) {desc}")
            raw = input("輸入選項 (預設 4): ").strip() or "4"
            if raw in options:
                print(f"➡️  已選 {options[raw][1]}")
                return options[raw][0]
            print("⚠️ 無效的選項，請重新輸入。")

    def prompt_statistic(self) -> str:
        options = {
            "1": ("mode", "眾數 (KDE peak)"),
            "2": ("max", "最大值"),
            "3": ("min", "最小值"),
        }
        while True:
            print("\n選擇要比較的統計量：")
            for key, (_, desc) in options.items():
                print(f"  {key}) {desc}")
            raw = input("輸入選項 (預設 1): ").strip() or "1"
            if raw in options:
                print(f"➡️  已選 {options[raw][1]}")
                return options[raw][0]
            print("⚠️ 無效的選項，請重新輸入。")

    def prompt_scale(self) -> str:
        while True:
            raw = input("座標尺度 [L=線性, G=log-log] (預設 G): ").strip().lower() or "g"
            if raw in {"l", "linear"}:
                return "linear"
            if raw in {"g", "log", "log-log"}:
                return "log"
            print("⚠️ 無效的選項，請輸入 L 或 G。")

    def prompt_output(self, default_name: str) -> Optional[Path]:
        prompt = f"輸出檔案 (Enter 僅顯示, 或輸入路徑儲存，例如 plots/{default_name}): "
        raw = input(prompt).strip()
        if not raw:
            return None
        return normalize_path(raw)

    def prompt_max_gap(self) -> float:
        raw = input("缺口門檻 (預設 1000W): ").strip()
        if not raw:
            return 1000.0
        try:
            return float(raw)
        except ValueError:
            print("⚠️ 非法數值，使用預設 1000W。")
            return 1000.0

    # ------------------------------------------------------------------ actions
    def run_summary(self) -> None:
        dataset = self.select_dataset()
        print(f"\n使用資料集：{dataset}")
        pin_min, pin_max = self.prompt_pin_range()
        series = self.prompt_series()
        scale = self.prompt_scale()

        slug = slugify(dataset)
        desc_min = "min" if pin_min is None else f"{pin_min:g}"
        desc_max = "max" if pin_max is None else f"{pin_max:g}"
        default_name = f"pin_{slug}_{series}_{scale}_{desc_min}_{desc_max}.png"
        output_path = self.prompt_output(default_name)
        if output_path is not None:
            output_path.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            str(PYTHON_BIN),
            str(PROJECT_ROOT / "plot_pin_statistics.py"),
            "--stats",
            str(self.stats_path),
            "--dataset",
            dataset,
            "--series",
            series,
            "--scale",
            scale,
        ]
        if output_path is not None:
            cmd.extend(["--output", str(output_path)])
        if pin_min is not None:
            cmd.extend(["--pin-min", str(pin_min)])
        if pin_max is not None:
            cmd.extend(["--pin-max", str(pin_max)])

        self.run_command(cmd)

    def run_density(self) -> None:
        dataset = self.select_dataset()
        print(f"\n使用資料集：{dataset}")
        pin_min, pin_max = self.prompt_pin_range()

        slug = slugify(dataset)
        desc_min = "min" if pin_min is None else f"{pin_min:g}"
        desc_max = "max" if pin_max is None else f"{pin_max:g}"
        default_name = f"pin_density_{slug}_{desc_min}_{desc_max}.png"
        output_path = self.prompt_output(default_name)
        if output_path is not None:
            output_path.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            str(PYTHON_BIN),
            str(PROJECT_ROOT / "plot_pin_density_distribution.py"),
            "--csv",
            str(self.values_path),
            "--dataset",
            dataset,
        ]
        if output_path is not None:
            cmd.extend(["--output", str(output_path)])
        if pin_min is not None:
            cmd.extend(["--pin-min", str(pin_min)])
        if pin_max is not None:
            cmd.extend(["--pin-max", str(pin_max)])

        self.run_command(cmd)

    def run_r2_comparison(self) -> None:
        datasets = self.select_multiple_datasets()
        print(f"\n比較資料集：{', '.join(datasets)}")
        pin_min, pin_max = self.prompt_pin_range()
        stat = self.prompt_statistic()

        slug = "-".join(slugify(ds) for ds in datasets)
        desc_min = "min" if pin_min is None else f"{pin_min:g}"
        desc_max = "max" if pin_max is None else f"{pin_max:g}"
        default_name = f"pin_compare_{stat}_{slug}_{desc_min}_{desc_max}.png"
        output_path = self.prompt_output(default_name)
        if output_path is not None:
            output_path.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            str(PYTHON_BIN),
            str(PROJECT_ROOT / "plot_r2_comparison.py"),
            "--stats",
            str(self.stats_path),
            "--stat",
            stat,
        ]
        if output_path is not None:
            cmd.extend(["--output", str(output_path)])
        cmd.append("--datasets")
        cmd.extend(datasets)

        if pin_min is not None:
            cmd.extend(["--pin-min", str(pin_min)])
        if pin_max is not None:
            cmd.extend(["--pin-max", str(pin_max)])

        self.run_command(cmd)

    def run_pin_kde_comparison(self) -> None:
        pin_value = self.prompt_pin_value()
        datasets = self.select_datasets_for_pin(pin_value)
        print(f"\n比較 Pin = {pin_value:g} W 下的資料集：{', '.join(datasets)}")

        slug = "-".join(slugify(ds) for ds in datasets)
        default_name = f"pin_kde_{pin_value:g}_{slug}.png"
        output_path = self.prompt_output(default_name)
        if output_path is not None:
            output_path.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            str(PYTHON_BIN),
            str(PROJECT_ROOT / "plot_pin_r2_kde.py"),
            "--csv",
            str(self.values_path),
            "--stats",
            str(self.stats_path),
            "--pin",
            f"{pin_value:g}",
        ]
        if output_path is not None:
            cmd.extend(["--output", str(output_path)])
        cmd.append("--datasets")
        cmd.extend(datasets)

        self.run_command(cmd)

    def run_gap(self) -> None:
        dataset = self.select_dataset()
        gap = self.prompt_max_gap()
        cmd = [
            str(PYTHON_BIN),
            str(PROJECT_ROOT / "analyze_pin_gap.py"),
            "--stats",
            str(self.stats_path),
            "--dataset",
            dataset,
            "--max-gap",
            str(gap),
        ]
        self.run_command(cmd)

    # ------------------------------------------------------------------ executor
    def run_command(self, cmd: List[str]) -> None:
        print("\n----------------------------------------")
        print("執行指令:")
        print(" ".join(cmd))
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as exc:
            print(f"⚠️ 指令執行失敗：{exc}")

    def main_loop(self) -> None:
        while True:
            print("\n========================================")
            print("圖表產生工具")
            print("目前資料集: ", self.current_dataset)
            print("----------------------------------------")
            print("  1) Pin vs. 電子密度摘要圖")
            print("  2) 電子密度分布（KDE）")
            print("  3) 檢視 Pin 覆蓋缺口")
            print("  4) r2 資料集比較圖")
            print("  5) 同功率 KDE 比較")
            print("  q) 離開")
            choice = input("輸入選項: ").strip().lower()
            if choice == "1":
                self.run_summary()
            elif choice == "2":
                self.run_density()
            elif choice == "3":
                self.run_gap()
            elif choice == "4":
                self.run_r2_comparison()
            elif choice == "5":
                self.run_pin_kde_comparison()
            elif choice == "q":
                print("Bye")
                return
            else:
                print("⚠️ 無效的選項，請重新輸入。")


def main() -> None:
    cli = ChartCLI(DEFAULT_STATS, DEFAULT_VALUES)
    cli.main_loop()


if __name__ == "__main__":
    main()
