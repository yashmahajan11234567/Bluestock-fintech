#!/bin/bash
# Wrapper script to run Day 43 inspection
PROJECT_DIR="/c/Users/hitoy/Downloads/Bluestock_fintech/nifty100-financial-analysis(Bluestock-fintech)"
VENV_PY="/c/Users/hitoy/Downloads/Bluestock_fintech/.venv/Scripts/python.exe"

cd "$PROJECT_DIR"
export PYTHONPATH="$PROJECT_DIR/src:$PYTHONPATH"
VENV="$VENV_PY"
"$VENV" tmp_day43_inspect.py
