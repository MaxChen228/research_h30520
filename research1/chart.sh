#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
PYTHON_BIN="${PYTHON:-python3}"
if [ -x "$PROJECT_ROOT/electron_density_env/bin/python" ]; then
  PYTHON_BIN="$PROJECT_ROOT/electron_density_env/bin/python"
fi

STATS_FILE="$PROJECT_ROOT/data/all_stats.csv"
VALUES_FILE="$PROJECT_ROOT/data/all_values.csv"

print_divider() { printf '\n%s\n' "----------------------------------------"; }

normalize_path() {
  local input="$1"
  if [ -z "$input" ]; then
    echo ""
  elif [[ "$input" = /* ]]; then
    echo "$input"
  else
    echo "$PROJECT_ROOT/$input"
  fi
}

ensure_parent_dir() {
  local path="$1"
  local dir
  dir=$(dirname "$path")
  mkdir -p "$dir"
}

slugify() {
  echo "$1" | tr '[:upper:]' '[:lower:]' | tr ' /' '__' | tr -cs 'a-z0-9._-' '_'
}

get_dataset_options() {
  "$PYTHON_BIN" - "$STATS_FILE" <<'PY'
import sys
from pathlib import Path

stats_path = Path(sys.argv[1])
datasets = ["ALL"]
if stats_path.exists():
    try:
        import pandas as pd
        df = pd.read_csv(stats_path, usecols=["dataset"])
        datasets.extend(sorted(d for d in df["dataset"].unique() if d != "ALL"))
    except Exception:
        pass
print(" ".join(dict.fromkeys(datasets)))
PY
}

select_dataset() {
  if [ ! -f "$STATS_FILE" ]; then
    echo "ALL"
    return
  fi
  local dataset_line
  dataset_line=$(get_dataset_options)
  if [ -z "$dataset_line" ]; then
    echo "ALL"
    return
  fi
  IFS=' ' read -r -a DATASETS <<< "$dataset_line"
  if [ "${#DATASETS[@]}" -eq 0 ]; then
    DATASETS=("ALL")
  fi
  while true; do
    print_divider
    echo "選擇資料集："
    local i=1
    for item in "${DATASETS[@]}"; do
      printf "  %d) %s\n" "$i" "$item"
      i=$((i + 1))
    done
    read -r -p "輸入選項: " choice
    if [[ $choice =~ ^[0-9]+$ ]] && [ "$choice" -ge 1 ] && [ "$choice" -le "${#DATASETS[@]}" ]; then
      echo "${DATASETS[$((choice-1))]}"
      return
    fi
    echo "無效的選項，請重新輸入。"
  done
}

run_summary_plot() {
  if [ ! -f "$STATS_FILE" ]; then
    echo "Error: 統計資料不存在 ($STATS_FILE)。請先執行 ./process_vtu_cases.sh。" >&2
    return 1
  fi

  local dataset=$(select_dataset)
  print_divider
  local pin_min="" pin_max=""
  read -r -p "Pin 最小值 (留空表示不限制): " pin_min
  read -r -p "Pin 最大值 (留空表示不限制): " pin_max

  echo "選擇要繪製的資料類型:"
  echo "  1) 眾數 (KDE peak)"
  echo "  2) 最大值"
  echo "  3) 最小值"
  echo "  4) 全部 (眾數 + 最大 + 最小)"
  local choice=""
  while [[ ! $choice =~ ^[1-4]$ ]]; do
    read -r -p "輸入選項編號 (1-4): " choice
    [[ $choice =~ ^[1-4]$ ]] || echo "請輸入 1-4 範圍內的數字。"
  done
  local series label
  case "$choice" in
    1) series="mode" ; label="mode" ;;
    2) series="max" ; label="max" ;;
    3) series="min" ; label="min" ;;
    4) series="all" ; label="all" ;;
  esac

  echo "選擇座標尺度:"
  echo "  L) 線性 (Linear)"
  echo "  G) log-log (兩軸皆為對數)"
  local scale_choice=""
  while [[ ! $scale_choice =~ ^[LlGg]$ ]]; do
    read -r -p "輸入 L 或 G: " scale_choice
    [[ $scale_choice =~ ^[LlGg]$ ]] || echo "請輸入 L 或 G。"
  done
  local scale
  if [[ $scale_choice =~ ^[Ll]$ ]]; then
    scale="linear"
  else
    scale="log"
  fi

  local dataset_slug=$(slugify "$dataset")
  local default_name="pin_${dataset_slug}_${label}_${scale}_summary.png"
  read -r -p "輸出檔案路徑 (預設: plots/${default_name}): " output
  output=$(normalize_path "${output:-plots/${default_name}}")
  ensure_parent_dir "$output"

  local cmd=("$PYTHON_BIN" "$PROJECT_ROOT/plot_pin_statistics.py" \
    --stats "$STATS_FILE" \
    --dataset "$dataset" \
    --series "$series" \
    --scale "$scale" \
    --output "$output")
  if [ -n "$pin_min" ]; then cmd+=(--pin-min "$pin_min"); fi
  if [ -n "$pin_max" ]; then cmd+=(--pin-max "$pin_max"); fi

  print_divider
  printf '執行指令: %s\n' "${cmd[*]}"
  "${cmd[@]}"
  printf '\n完成！圖檔已輸出至: %s\n' "$output"
}

run_density_plot() {
  if [ ! -f "$VALUES_FILE" ]; then
    echo "Error: 原始數據不存在 ($VALUES_FILE)。請先執行 ./process_vtu_cases.sh。" >&2
    return 1
  fi

  local dataset=$(select_dataset)
  print_divider
  local pin_min="" pin_max=""
  read -r -p "Pin 最小值 (留空表示不限制): " pin_min
  read -r -p "Pin 最大值 (留空表示不限制): " pin_max

  local dataset_slug=$(slugify "$dataset")
  local default_name="pin_density_${dataset_slug}_${pin_min:-min}_${pin_max:-max}.png"
  read -r -p "輸出檔案路徑 (預設: plots/${default_name}): " output
  output=$(normalize_path "${output:-plots/${default_name}}")
  ensure_parent_dir "$output"

  local cmd=("$PYTHON_BIN" "$PROJECT_ROOT/plot_pin_density_distribution.py" \
    --csv "$VALUES_FILE" \
    --dataset "$dataset" \
    --output "$output")
  if [ -n "$pin_min" ]; then cmd+=(--pin-min "$pin_min"); fi
  if [ -n "$pin_max" ]; then cmd+=(--pin-max "$pin_max"); fi

  print_divider
  printf '執行指令: %s\n' "${cmd[*]}"
  "${cmd[@]}"
  printf '\n完成！圖檔已輸出至: %s\n' "$output"
}

while true; do
  print_divider
  echo "選擇要產生的圖表："
  echo "  1) Pin vs. 電子密度摘要圖"
  echo "  2) 電子密度分布（KDE）"
  echo "  q) 離開"
  read -r -p "輸入選項: " selection
  case "$selection" in
    1) run_summary_plot ;;
    2) run_density_plot ;;
    q|Q) echo "Bye"; exit 0 ;;
    *) echo "無效的選項，請重新輸入。" ;;
  esac
done
