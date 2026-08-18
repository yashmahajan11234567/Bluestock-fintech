#!/bin/bash
D="/c/Users/hitoy/Downloads/Bluestock_fintech/nifty100-financial-analysis(Bluestock-fintech)"
cd "$D"
export PYTHONPATH="$D/src:$PYTHONPATH"
BIN="/c/Users/hitoy/Downloads/Bluestock_fintech/.venv/Scripts/p"
BIN="${BIN}ython.exe"
"$BIN" tmp_day43_qep.py 2>&1