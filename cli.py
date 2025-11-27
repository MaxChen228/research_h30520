#!/usr/bin/env python3
"""
統一電漿模擬數據分析 CLI
整合三個研究領域的繪圖與分析工具
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Optional

# 專案根目錄
PROJECT_ROOT = Path(__file__).resolve().parent
PYTHON_BIN = PROJECT_ROOT / "venv" / "bin" / "python"
if not PYTHON_BIN.exists():
    PYTHON_BIN = Path(sys.executable)

# 研究目錄
RESEARCH1 = PROJECT_ROOT / "research1"
RESEARCH2 = PROJECT_ROOT / "research2"
RESEARCH3 = PROJECT_ROOT / "research3"


class PlasmaCLI:
    """電漿模擬統一 CLI 主程式"""

    def __init__(self) -> None:
        self.running = True

    # ------------------------------------------------------------------ 主選單
    def main_menu(self) -> None:
        """顯示主選單並處理使用者選擇"""
        while self.running:
            print("\n" + "=" * 60)
            print("  電漿模擬數據分析工具 - 統一介面")
            print("=" * 60)
            print("\n請選擇研究領域：")
            print("  1) Research 1 - Pin vs 電子密度分析")
            print("  2) Research 2 - 500W 電漿徑向/軸向分析")
            print("  3) Research 3 - 功率-半徑趨勢分析")
            print("  q) 離開")
            print("-" * 60)

            choice = input("輸入選項: ").strip().lower()

            if choice == "1":
                self.launch_research1()
            elif choice == "2":
                self.launch_research2()
            elif choice == "3":
                self.launch_research3()
            elif choice == "q":
                print("再見！")
                self.running = False
            else:
                print("⚠️  無效的選項，請重新輸入。")

    # ------------------------------------------------------------------ Research 1
    def launch_research1(self) -> None:
        """啟動 Research 1 互動式介面"""
        print("\n" + "→" * 30)
        print("啟動 Research 1：Pin vs 電子密度分析")
        print("→" * 30 + "\n")

        # 直接呼叫原有的 chart_cli.py
        chart_cli = RESEARCH1 / "chart_cli.py"
        if not chart_cli.exists():
            print(f"⚠️  找不到 {chart_cli}")
            input("按 Enter 返回主選單...")
            return

        try:
            subprocess.run([str(PYTHON_BIN), str(chart_cli)], check=True)
        except subprocess.CalledProcessError as e:
            print(f"⚠️  執行失敗：{e}")
        except KeyboardInterrupt:
            print("\n已中斷，返回主選單。")

    # ------------------------------------------------------------------ Research 2
    def launch_research2(self) -> None:
        """啟動 Research 2 互動式介面"""
        print("\n" + "→" * 30)
        print("啟動 Research 2：500W 電漿徑向/軸向分析")
        print("→" * 30 + "\n")

        while True:
            print("\n選擇分析類型：")
            print("  1) 徑向切片分析 (Radial Slice)")
            print("  2) 軸向切片分析 (Axial Slice)")
            print("  3) 衰減半徑分析 (Decay Radius)")
            print("  b) 返回主選單")

            choice = input("輸入選項: ").strip().lower()

            if choice == "1":
                self.run_radial_slice()
            elif choice == "2":
                self.run_axial_slice()
            elif choice == "3":
                self.run_decay_radius()
            elif choice == "b":
                break
            else:
                print("⚠️  無效的選項，請重新輸入。")

    def run_radial_slice(self) -> None:
        """執行徑向切片分析"""
        print("\n徑向切片分析設定：")
        z_input = input("切片高度 z (mm，Enter 使用峰值密度位置): ").strip()
        show = input("顯示圖形？(y/n，預設 y): ").strip().lower() or "y"
        output = input("輸出路徑 (Enter 使用預設 plots/radial_slice_*.png): ").strip()

        cmd = [str(PYTHON_BIN), str(RESEARCH2 / "plot_radial_slice.py")]
        if z_input:
            cmd.extend(["--z", z_input])
        if show == "y":
            cmd.append("--show")
        if output:
            cmd.extend(["--output", output])

        self._run_command(cmd)

    def run_axial_slice(self) -> None:
        """執行軸向切片分析"""
        print("\n軸向切片分析設定：")
        radius = input("半徑 r (mm，預設 0): ").strip() or "0"
        samples = input("取樣點數 (預設 400): ").strip() or "400"
        show = input("顯示圖形？(y/n，預設 y): ").strip().lower() or "y"
        output = input("輸出路徑 (Enter 使用預設 plots/axis_slice_*.png): ").strip()

        cmd = [
            str(PYTHON_BIN),
            str(RESEARCH2 / "plot_axis_slice.py"),
            "--radius",
            radius,
            "--samples",
            samples,
        ]
        if show == "y":
            cmd.append("--show")
        if output:
            cmd.extend(["--output", output])

        self._run_command(cmd)

    def run_decay_radius(self) -> None:
        """執行衰減半徑分析"""
        print("\n衰減半徑分析設定：")
        alpha_input = input("衰減係數 alpha (0-1，多個用空格分隔，預設 0.5 0.7 0.9): ").strip()
        show = input("顯示圖形？(y/n，預設 y): ").strip().lower() or "y"
        output = input("輸出路徑 (Enter 使用預設 plots/decay_radius_*.png): ").strip()

        cmd = [str(PYTHON_BIN), str(RESEARCH2 / "plot_decay_radius.py")]
        if alpha_input:
            cmd.append("--alpha")
            cmd.extend(alpha_input.split())
        if show == "y":
            cmd.append("--show")
        if output:
            cmd.extend(["--output", output])

        self._run_command(cmd)

    # ------------------------------------------------------------------ Research 3
    def launch_research3(self) -> None:
        """啟動 Research 3 功率-半徑趨勢分析"""
        print("\n" + "→" * 30)
        print("啟動 Research 3：功率-半徑趨勢分析")
        print("→" * 30 + "\n")

        print("此研究會生成以下圖表：")
        print("  - research3_loglog.png (對數-對數圖)")
        print("  - research3_linear.png (線性圖)")
        print()

        confirm = input("確認執行？(y/n): ").strip().lower()
        if confirm != "y":
            print("已取消。")
            return

        script = RESEARCH3 / "plot_research3_trends.py"
        if not script.exists():
            print(f"⚠️  找不到 {script}")
            input("按 Enter 返回...")
            return

        # 切換到 research3 目錄執行（因為路徑寫死在程式中）
        cmd = [str(PYTHON_BIN), str(script)]
        try:
            subprocess.run(cmd, cwd=str(RESEARCH3), check=True)
            print("\n✅ 圖表已生成於 research3/ 目錄")
        except subprocess.CalledProcessError as e:
            print(f"⚠️  執行失敗：{e}")

        input("\n按 Enter 返回主選單...")

    # ------------------------------------------------------------------ 工具函數
    def _run_command(self, cmd: list[str]) -> None:
        """執行指令並處理錯誤"""
        print("\n" + "-" * 60)
        print("執行指令：")
        print(" ".join(cmd))
        print("-" * 60)

        try:
            subprocess.run(cmd, check=True)
            print("\n✅ 執行完成")
        except subprocess.CalledProcessError as e:
            print(f"\n⚠️  執行失敗：{e}")
        except KeyboardInterrupt:
            print("\n已中斷")

        input("\n按 Enter 繼續...")


def main() -> None:
    """主程式入口"""
    cli = PlasmaCLI()
    try:
        cli.main_menu()
    except KeyboardInterrupt:
        print("\n\n再見！")


if __name__ == "__main__":
    main()
