#!/usr/bin/env python3
"""Plot average power vs radius (log-log) and report low-radius fit."""

from __future__ import annotations

from pathlib import Path
from typing import Dict

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl

CSV_PATH = Path("research3 - 工作表1.csv")
OUTPUT_LOGLOG = Path("research3_loglog.png")

mpl.rcParams.update({
    "font.family": "Times New Roman",
    "font.size": 14,
    "axes.titlesize": 18,
    "axes.labelsize": 18,
    "xtick.labelsize": 14,
    "ytick.labelsize": 14,
    "axes.grid": False,
})


def load_data() -> pd.DataFrame:
    df = pd.read_csv(CSV_PATH)
    df = df.rename(columns={df.columns[0]: "r", df.columns[1]: "p"})
    df = df.sort_values("r")
    return df


def style_axis(ax: plt.Axes) -> None:
    ax.tick_params(direction="in", length=6, width=1.4)
    ax.minorticks_on()
    ax.tick_params(which="minor", direction="in", length=3, width=1.0)
    for spine in ax.spines.values():
        spine.set_linewidth(1.4)
    ax.grid(True, linestyle="--", linewidth=0.7, alpha=0.3)


def plot_loglog(df: pd.DataFrame) -> Dict[str, float]:
    fig, ax = plt.subplots(figsize=(6.5, 4.5), dpi=300)
    ax.loglog(df["r"], df["p"], color="#c0392b", marker="o", linewidth=2, markersize=5, label="Data")

    subset = df[df["r"] < 36]
    stats: Dict[str, float] = {"count": int(len(subset))}

    if len(subset) >= 2:
        log_r = np.log10(subset["r"].to_numpy())
        log_p = np.log10(subset["p"].to_numpy())
        slope, intercept = np.polyfit(log_r, log_p, deg=1)
        corr = float(np.corrcoef(log_r, log_p)[0, 1])

        fit_r = np.logspace(np.log10(subset["r"].min()), np.log10(subset["r"].max()), 200)
        fit_p = 10 ** (intercept + slope * np.log10(fit_r))
        ax.loglog(fit_r, fit_p, color="#1f618d", linestyle="--", linewidth=2, label="Fit (r < 36 mm)")
        ax.loglog(subset["r"], subset["p"], linestyle="None", marker="o", markersize=6,
                  markerfacecolor="#1f618d", markeredgecolor="#1f618d", alpha=0.85)

        stats.update({
            "slope": slope,
            "intercept": intercept,
            "corr": corr,
            "r_squared": corr ** 2,
            "coeff": 10 ** intercept,
        })

    # 添加參考虛線
    ax.axvline(x=35.9, color="gray", linestyle=":", linewidth=1.5, alpha=0.7, label="r = 35.9 mm")
    ax.axhline(y=20, color="gray", linestyle=":", linewidth=1.5, alpha=0.7, label="P = 20 W")

    ax.set_xlabel("Radius r (mm)")
    ax.set_ylabel("Cutoff Power (W)")
    ax.set_title("Cutoff Power vs Radius")
    ax.legend(loc="upper right", frameon=False, fontsize=12)

    # 在空白處添加擬合方程（左下角區域）
    if len(subset) >= 2 and "slope" in stats:
        equation_text = f"$P \\propto r^{{{stats['slope']:.2f}}}$\n$R^2 = {stats['r_squared']:.4f}$"
        ax.text(0.05, 0.25, equation_text, transform=ax.transAxes,
                fontsize=14, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8, edgecolor='gray', linewidth=1))

    style_axis(ax)
    fig.tight_layout()
    fig.savefig(OUTPUT_LOGLOG)
    plt.close(fig)
    return stats


def main() -> None:
    df = load_data()
    stats = plot_loglog(df)
    print(f"Saved {OUTPUT_LOGLOG}")

    if stats.get("count", 0) >= 2 and "corr" in stats:
        print("Log-log 線性擬合 (r < 36 mm):")
        print(f"  log10(P_avg) = {stats['intercept']:.6f} + {stats['slope']:.6f} * log10(r)")
        print(f"  => P_avg ≈ {stats['coeff']:.6e} * r^{stats['slope']:.6f}")
        print(f"  相關係數 r = {stats['corr']:.6f}, R^2 = {stats['r_squared']:.6f}, 點數 = {int(stats['count'])}")
    else:
        print("r < 36 mm 的資料不足以進行擬合。")


if __name__ == "__main__":
    main()
