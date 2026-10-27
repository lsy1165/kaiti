#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/server_config.env"

eval "$(conda shell.bash hook)"
conda activate "$CONDA_ENV_NAME"

PAIR_DATA_DIR="${PAIR_DATA_DIR:-$PROJECT_ROOT/code/data/stage04_complex_conditions/paired_samples}"
RESULT_ROOT="${RESULT_ROOT:-$PROJECT_ROOT/code/outputs/stage04_complex_conditions/mvxnet_comparison_results}"

mkdir -p "$RESULT_ROOT"

if [[ ! -d "$PAIR_DATA_DIR" ]]; then
  echo "ERROR: paired sample directory not found: $PAIR_DATA_DIR"
  echo "Create paired samples first with code/src/stage04_complex_conditions/create_one_to_one_conditions.py"
  exit 1
fi

mapfile -t PAIR_DIRS < <(find "$PAIR_DATA_DIR" -mindepth 1 -maxdepth 1 -type d | sort)

if [[ "${#PAIR_DIRS[@]}" -eq 0 ]]; then
  echo "ERROR: no paired clean/complex samples found in: $PAIR_DATA_DIR"
  exit 1
fi

for path in "$MVXNET_CONFIG" "$MVXNET_CKPT"; do
  if [[ ! -f "$path" ]]; then
    echo "ERROR: required file not found: $path"
    exit 1
  fi
done

run_one_sample() {
  local pair_name="$1"
  local variant="$2"
  local sample_dir="$3"
  local output_dir="$4"

  mapfile -t info_files < <(find "$sample_dir" -maxdepth 1 -type f -name "*.pkl" | sort)
  if [[ "${#info_files[@]}" -ne 1 ]]; then
    echo "ERROR: expected exactly one pkl in $sample_dir, found ${#info_files[@]}"
    exit 1
  fi

  local info="${info_files[0]}"
  local stem
  stem="$(basename "$info" .pkl)"
  local image="$sample_dir/$stem.png"
  local pcd="$sample_dir/$stem.bin"

  for sample_path in "$image" "$pcd" "$info"; do
    if [[ ! -f "$sample_path" ]]; then
      echo "ERROR: required sample file not found: $sample_path"
      exit 1
    fi
  done

  mkdir -p "$output_dir"
  echo "Running MVX-Net pair=$pair_name variant=$variant sample=$stem"

  python demo/multi_modality_demo.py \
    "$pcd" \
    "$image" \
    "$info" \
    "$MVXNET_CONFIG" \
    "$MVXNET_CKPT" \
    --device "$DEVICE" \
    --pred-score-thr "$PRED_SCORE_THR" \
    --out-dir "$output_dir" \
    --cam-type CAM2 \
    2>&1 | tee "$output_dir/inference.log"

  echo -e "$pair_name\t$variant\t$stem\t$image\t$pcd\t$info\t$output_dir" >> "$SUMMARY"
}

cd "$MMDET3D_DIR"

SUMMARY="$RESULT_ROOT/summary.tsv"
echo -e "pair\tvariant\tsample\timage\tpoint_cloud\tinfo\toutput_dir" > "$SUMMARY"

for pair_dir in "${PAIR_DIRS[@]}"; do
  pair_name="$(basename "$pair_dir")"
  clean_dir="$pair_dir/clean"
  complex_dir="$pair_dir/complex"

  if [[ ! -d "$clean_dir" ]] || [[ ! -d "$complex_dir" ]]; then
    echo "ERROR: pair directory must contain clean/ and complex/: $pair_dir"
    exit 1
  fi

  pair_output="$RESULT_ROOT/$pair_name"
  run_one_sample "$pair_name" "clean" "$clean_dir" "$pair_output/clean"
  run_one_sample "$pair_name" "complex" "$complex_dir" "$pair_output/complex"

  if [[ -f "$pair_dir/pair_info.json" ]]; then
    cp "$pair_dir/pair_info.json" "$pair_output/pair_info.json"
  fi
done

echo "Clean/complex MVX-Net comparison outputs saved to: $RESULT_ROOT"
echo "Summary: $SUMMARY"
