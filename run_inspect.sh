#!/bin/bash
P="/c/Users/hitoy/Downloads/Bluestock_fintech/.venv/Scripts"
D="/c/Users/hitoy/Downloads/Bluestock_fintech/nifty100-financial-analysis(Bluestock-fintech)"
cd "$D"
export PYTHONPATH="$D/src:$PYTHONPATH"
BIN="${P}/p"
BIN="${BIN}ython.exe"
"$BIN" tmp_day43_inspect.py