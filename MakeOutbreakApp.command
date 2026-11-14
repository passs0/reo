#!/bin/zsh
set -eu

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

# Ensure Homebrew tools are in PATH
if [[ -f "/opt/homebrew/bin/brew" ]]; then
    eval "$(/opt/homebrew/bin/brew shellenv)"
elif [[ -f "/usr/local/bin/brew" ]]; then
    eval "$(/usr/local/bin/brew shellenv)"
fi

echo ""
echo "========================================================"
echo "    Resident Evil Outbreak - macOS Native App Compiler  "
echo "========================================================"
echo ""

# Run compiler script
if python3 "$DIR/make_mac_app.py" "$@"; then
    echo ""
    echo "[✓] Process completed successfully."
else
    build_status=$?
    echo ""
    echo "[✗] Build failed or exited with status $build_status."
    echo "Press Enter to close this window..."
    read -r _
    exit $build_status
fi
