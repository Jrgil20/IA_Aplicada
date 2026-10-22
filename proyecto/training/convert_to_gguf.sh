#!/usr/bin/env bash
# ==============================================================================
# Edge Clean Copilot — Automated GGUF Quantization Pipeline (Phase 3)
#
# Converts consolidated 16-bit Hugging Face weights (merged_model) into
# quantized GGUF binaries (Q4_K_M, Q5_K_M, Q8_0) for edge inference.
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_INPUT_DIR="${SCRIPT_DIR}/output/merged_model"
DEFAULT_OUTPUT_DIR="${SCRIPT_DIR}/output/gguf"
DEFAULT_MODEL_NAME="clean-copilot-1.5b"

INPUT_DIR="${DEFAULT_INPUT_DIR}"
OUTPUT_DIR="${DEFAULT_OUTPUT_DIR}"
MODEL_NAME="${DEFAULT_MODEL_NAME}"
LLAMA_DIR="${LLAMA_CPP_DIR:-}"
ALL_QUANTS=false
CLEAN_F16=false

show_help() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS]

Automates GGUF conversion and quantization for Edge Clean Copilot.

Options:
  -i, --input-dir PATH    Path to consolidated HF model (default: output/merged_model)
  -o, --output-dir PATH   Path to save quantized GGUFs (default: output/gguf)
  -m, --model-name NAME   Base filename for GGUFs (default: clean-copilot-1.5b)
  -l, --llama-dir PATH    Path to llama.cpp repository (autodetected if omitted)
      --all               Generate Q4_K_M, Q5_K_M, and Q8_0 (default: Q4_K_M only)
      --clean-f16         Delete intermediate ~3GB F16 GGUF after quantization
  -h, --help              Show this help message and exit

Prerequisites:
  1. Consolidated weights produced via: python3 train_lora.py --merge
  2. llama.cpp built with convert_hf_to_gguf.py and llama-quantize
EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        -i|--input-dir)
            INPUT_DIR="$2"
            shift 2
            ;;
        -o|--output-dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        -m|--model-name)
            MODEL_NAME="$2"
            shift 2
            ;;
        -l|--llama-dir)
            LLAMA_DIR="$2"
            shift 2
            ;;
        --all)
            ALL_QUANTS=true
            shift
            ;;
        --clean-f16)
            CLEAN_F16=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo "[ERROR] Unknown option: $1" >&2
            echo "Run '$(basename "$0") --help' for usage." >&2
            exit 1
            ;;
    esac
done

echo "========================================================================"
echo "         EDGE CLEAN COPILOT — AUTOMATED GGUF QUANTIZATION PIPELINE       "
echo "========================================================================"
echo "Input HF Directory:  ${INPUT_DIR}"
echo "Output Directory:    ${OUTPUT_DIR}"
echo "Target Model Name:   ${MODEL_NAME}"
echo "Quantization Mode:   $([ "${ALL_QUANTS}" = true ] && echo "ALL (Q4_K_M, Q5_K_M, Q8_0)" || echo "TARGET (Q4_K_M only)")"
echo "Clean F16 Flag:      ${CLEAN_F16}"
echo "------------------------------------------------------------------------"

# 1. Validate Input Directory
if [[ ! -d "${INPUT_DIR}" ]]; then
    echo "[ERROR] Input model directory does not exist: ${INPUT_DIR}" >&2
    echo "Please train and merge the LoRA model first by running:" >&2
    echo "  python3 train_lora.py --merge --output-dir \"${SCRIPT_DIR}/output\"" >&2
    exit 1
fi

if [[ ! -f "${INPUT_DIR}/config.json" ]]; then
    echo "[ERROR] Invalid HF model directory (missing config.json): ${INPUT_DIR}" >&2
    exit 1
fi

# 2. Autodetect Python environment
if [[ -f "/home/ucab-spark1/lora_venv/bin/python3" ]]; then
    PYTHON_BIN="/home/ucab-spark1/lora_venv/bin/python3"
elif command -v python3 &> /dev/null; then
    PYTHON_BIN="$(command -v python3)"
else
    echo "[ERROR] No python3 interpreter found in PATH or /home/ucab-spark1/lora_venv." >&2
    exit 1
fi
echo "[OK] Python runtime: ${PYTHON_BIN}"

# 3. Autodetect llama.cpp directory
if [[ -z "${LLAMA_DIR}" ]]; then
    CANDIDATES=(
        "${HOME}/llama.cpp"
        "/home/ucab-spark1/llama.cpp"
        "${SCRIPT_DIR}/../../llama.cpp"
        "${SCRIPT_DIR}/../llama.cpp"
    )
    for c in "${CANDIDATES[@]}"; do
        if [[ -d "${c}" && -f "${c}/convert_hf_to_gguf.py" ]]; then
            LLAMA_DIR="${c}"
            break
        fi
    done
fi

if [[ -z "${LLAMA_DIR}" || ! -f "${LLAMA_DIR}/convert_hf_to_gguf.py" ]]; then
    echo "[ERROR] llama.cpp repository not found." >&2
    echo "Please specify path via --llama-dir <path> or export LLAMA_CPP_DIR=<path>." >&2
    exit 1
fi
echo "[OK] llama.cpp found: ${LLAMA_DIR}"

# 4. Locate llama-quantize binary
QUANTIZE_BIN=""
QUANTIZE_CANDIDATES=(
    "${LLAMA_DIR}/build/bin/llama-quantize"
    "${LLAMA_DIR}/build/bin/Release/llama-quantize"
    "${LLAMA_DIR}/llama-quantize"
    "$(command -v llama-quantize 2>/dev/null || true)"
)
for q in "${QUANTIZE_CANDIDATES[@]}"; do
    if [[ -n "${q}" && -x "${q}" ]]; then
        QUANTIZE_BIN="${q}"
        break
    fi
done

if [[ -z "${QUANTIZE_BIN}" ]]; then
    echo "[ERROR] 'llama-quantize' binary not found or not executable." >&2
    echo "Please compile llama.cpp first: (cd \"${LLAMA_DIR}\" && cmake -B build && cmake --build build --config Release)" >&2
    exit 1
fi
echo "[OK] llama-quantize:  ${QUANTIZE_BIN}"
echo "------------------------------------------------------------------------"

mkdir -p "${OUTPUT_DIR}"

# 5. Convert HF Weights to Unquantized F16 GGUF
F16_GGUF="${OUTPUT_DIR}/${MODEL_NAME}-f16.gguf"
echo "--> Step 1/2: Converting Hugging Face model to F16 GGUF..."
"${PYTHON_BIN}" "${LLAMA_DIR}/convert_hf_to_gguf.py" \
    "${INPUT_DIR}" \
    --outfile "${F16_GGUF}" \
    --outtype f16

if [[ ! -f "${F16_GGUF}" ]]; then
    echo "[ERROR] F16 GGUF conversion failed. Output file not found: ${F16_GGUF}" >&2
    exit 1
fi
F16_SIZE=$(du -h "${F16_GGUF}" | cut -f1)
echo "[SUCCESS] Created F16 GGUF: ${F16_GGUF} (${F16_SIZE})"

# 6. Quantize to Target GGUF Formats
QUANTS=("q4_k_m")
if [[ "${ALL_QUANTS}" = true ]]; then
    QUANTS=("q4_k_m" "q5_k_m" "q8_0")
fi

echo "--> Step 2/2: Quantizing model weights..."
for q in "${QUANTS[@]}"; do
    TARGET_GGUF="${OUTPUT_DIR}/${MODEL_NAME}-${q}.gguf"
    echo "  [Quantizing] -> ${TARGET_GGUF} (type: ${q^^})..."
    "${QUANTIZE_BIN}" "${F16_GGUF}" "${TARGET_GGUF}" "${q^^}"
    Q_SIZE=$(du -h "${TARGET_GGUF}" | cut -f1)
    echo "  [DONE] Saved: ${TARGET_GGUF} (${Q_SIZE})"
done

# 7. Optional Cleanup of Intermediate F16 GGUF
if [[ "${CLEAN_F16}" = true ]]; then
    echo "--> Cleaning up intermediate F16 GGUF (${F16_GGUF})..."
    rm -f "${F16_GGUF}"
    echo "[OK] Removed ${F16_GGUF} to save disk space."
fi

echo "========================================================================"
echo "          [SUCCESS] GGUF QUANTIZATION PIPELINE COMPLETED                "
echo "========================================================================"
ls -lh "${OUTPUT_DIR}"/*.gguf
echo "========================================================================"
EOF
