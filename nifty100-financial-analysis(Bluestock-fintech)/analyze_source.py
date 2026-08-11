import sys
sys.path.insert(0, 'src')
from src.nlp.parser import AnalysisTextParser
import pandas as pd
import re

wb_path = 'Data/raw/analysis.xlsx'
df = pd.read_excel(wb_path, sheet_name='Analysis', header=1)
print('Shape:', df.shape)
print('Columns:', df.columns.tolist())
print()

metric_cols = ['compounded_sales_growth', 'compounded_profit_growth', 'stock_price_cagr', 'roe']
pattern = re.compile(r'(\d+(?:\.\d+)?)\s*Years?\s*:?\s*([+-]?[\d.]+)\s*%|TTM\s*:?\s*([+-]?[\d.]+)\s*%|Last\s*Year\s*:?\s*([+-]?[\d.]+)\s*%|LY\s*:?\s*([+-]?[\d.]+)\s*%', re.IGNORECASE)

total = 0
for idx, row in df.iterrows():
    company = row['company_id']
    print(f'=== {company} (row {idx}) ===')
    for metric in metric_cols:
        val = row[metric]
        if pd.notna(val):
            text = str(val)
            print(f'  {metric}:')
            print(f'    Raw: {repr(text)}')
            matches = list(pattern.finditer(text))
            print(f'    Found: {len(matches)}')
            for m in matches:
                if m.group(1):
                    print(f'      {m.group(1)} Years: {m.group(2)}%')
                elif m.group(3):
                    print(f'      TTM: {m.group(3)}%')
                elif m.group(4):
                    print(f'      Last Year: {m.group(4)}%')
                elif m.group(5):
                    print(f'      LY: {m.group(5)}%')
            total += len(matches)
        else:
            print(f'  {metric}: (empty/NaN)')
print(f'\nTOTAL: {total}')