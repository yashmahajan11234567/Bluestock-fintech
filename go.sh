#!/bin/bash
V="/c/Users/hitoy/Downloads/Bluestock_fintech/.venv/Scripts/p"
V="${V}ython.exe"
P="/c/Users/hitoy/Downloads/Bluestock_fintech/nifty100-financial-analysis(Bluestock-fintech)"
cd "$P"
export PYTHONPATH="$P/src:$PYTHONPATH"
"$V" tmp_day43_inspect.py
