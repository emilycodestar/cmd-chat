#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"
MARKER_FILE="$VENV_DIR/.cmd-chat-deps-installed"

if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
else
    echo "Python 3 was not found on PATH."
    exit 1
fi

if [[ ! -d "$VENV_DIR" ]]; then
    "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

if [[ ! -f "$MARKER_FILE" || "$SCRIPT_DIR/requirements.txt" -nt "$MARKER_FILE" ]]; then
    python -m pip install --upgrade pip
    python -m pip install -r "$SCRIPT_DIR/requirements.txt"
    touch "$MARKER_FILE"
fi

if [[ $# -eq 0 ]]; then
    cat <<'EOF'
Usage:
  ./start.sh serve 0.0.0.0 3000 --password mysecret
  ./start.sh connect SERVER_IP 3000 username mysecret
EOF
    exit 0
fi

python "$SCRIPT_DIR/cmd_chat.py" "$@"
