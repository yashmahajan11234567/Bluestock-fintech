"""Temporary Day 43 database inspection script."""
import sys
import os
import sqlite3
from pathlib import Path

# Set working directory to project root
os.chdir(Path(__file__).parent)

print('=== ENVIRONMENT ===')
print('Python:', sys.version)
print('CWD:', os.getcwd())

import fastapi; print('fastapi:', fastapi.__version__)
import streamlit; print('streamlit:', streamlit.__version__)
import pandas; print('pandas:', pandas.__version__)
import numpy; print('numpy:', numpy.__version__)
import requests; print('requests:', requests.__version__)
import pytest; print('pytest:', pytest.__version__)

print()
print('=== DATABASE FINGERPRINT (BEFORE TESTING) ===')
DB_PATH = Path('db/nifty100.db')
conn = sqlite3.connect(str(DB_PATH))
conn.row_factory = sqlite3.Row

tables = ['companies','profitandloss','balancesheet','cashflow','analysis','documents','prosandcons','sectors','stock_prices','financial_ratios','market_cap','peer_groups']
print('Row counts:')
for t in tables:
    c = conn.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
    print(f'  {t}: {c}')

print()
print('=== INDEXES ===')
for row in conn.execute("SELECT name, tbl_name FROM sqlite_master WHERE type='index' AND sql IS NOT NULL ORDER BY tbl_name, name"):
    idx_name = row['name']
    tbl_name = row['tbl_name']
    info = conn.execute(f'PRAGMA index_info({idx_name})').fetchall()
    cols = ', '.join(r['name'] for r in info)
    print(f'  {idx_name} on {tbl_name}({cols})')

print()
print('=== 5 COMPANY IDS ===')
rows = conn.execute("SELECT id, company_name FROM companies ORDER BY id LIMIT 5").fetchall()
for r in rows:
    print(f'  {r["id"]:10s} - {r["company_name"]}')

print()
print('=== TABLE SCHEMAS ===')
for t in tables:
    cols = conn.execute(f'PRAGMA table_info({t})').fetchall()
    col_strs = [f'{c["name"]} ({c["type"]})' for c in cols]
    print(f'  {t}: {", ".join(col_strs)}')

conn.close()
print()
print('Done.')
