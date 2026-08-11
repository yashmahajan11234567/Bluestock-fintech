import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple
import pandas as pd

STANDARD_PATTERN = re.compile(r'(\d+(?:\.\d+)?)\s*Years?\s*:?\s*([+-]?[\d.]+)\s*%', re.IGNORECASE)
TTM_PATTERN = re.compile(r'TTM\s*:?\s*([+-]?[\d.]+)\s*%', re.IGNORECASE)
LAST_YEAR_PATTERN = re.compile(r'Last\s*Year\s*:?\s*([+-]?[\d.]+)\s*%', re.IGNORECASE)
LY_PATTERN = re.compile(r'LY\s*:?\s*([+-]?[\d.]+)\s*%', re.IGNORECASE)

@dataclass
class ParsedRecord:
    company_id: str
    metric_type: str
    period_years: float
    value_pct: float

@dataclass
class ParseFailure:
    id: int
    company_id: str
    metric_type: str
    raw_text: str
    reason: str

class AnalysisTextParser:
    def __init__(self):
        self.standard_pattern = STANDARD_PATTERN
        self.ttm_pattern = TTM_PATTERN
        self.last_year_pattern = LAST_YEAR_PATTERN
        self.ly_pattern = LY_PATTERN
        self.parsed_records = []
        self.parse_failures = []
    
    def parse_cell(self, text, company_id, metric_type, row_id):
        if pd.isna(text) or not text or not str(text).strip():
            self.parse_failures.append(ParseFailure(
                id=row_id,
                company_id=company_id,
                metric_type=metric_type,
                raw_text=str(text) if text else '',
                reason='Blank or NaN value'
            ))
            return []
        text = str(text).strip()
        records = []
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            # Try TTM pattern first (special case)
            ttm_match = self.ttm_pattern.search(line)
            if ttm_match:
                value_str = ttm_match.group(1)
                try:
                    value_pct = float(value_str)
                    records.append(ParsedRecord(
                        company_id=company_id,
                        metric_type=metric_type,
                        period_years=0.0,
                        value_pct=value_pct
                    ))
                    continue
                except ValueError:
                    self.parse_failures.append(ParseFailure(
                        id=row_id, company_id=company_id, metric_type=metric_type,
                        raw_text=line, reason=f'Invalid TTM percentage value: {value_str}'
                    ))
            # Try Last Year pattern (special case - treat as 1 year)
            ly_match = self.last_year_pattern.search(line)
            if ly_match:
                value_str = ly_match.group(1)
                try:
                    value_pct = float(value_str)
                    records.append(ParsedRecord(
                        company_id=company_id,
                        metric_type=metric_type,
                        period_years=1.0,
                        value_pct=value_pct
                    ))
                    continue
                except ValueError:
                    self.parse_failures.append(ParseFailure(
                        id=row_id, company_id=company_id, metric_type=metric_type,
                        raw_text=line, reason=f'Invalid Last Year percentage value: {value_str}'
                    ))
            # Try LY pattern (abbreviated Last Year - treat as 1 year)
            ly_abbr_match = self.ly_pattern.search(line)
            if ly_abbr_match:
                value_str = ly_abbr_match.group(1)
                try:
                    value_pct = float(value_str)
                    records.append(ParsedRecord(
                        company_id=company_id,
                        metric_type=metric_type,
                        period_years=1.0,
                        value_pct=value_pct
                    ))
                    continue
                except ValueError:
                    self.parse_failures.append(ParseFailure(
                        id=row_id, company_id=company_id, metric_type=metric_type,
                        raw_text=line, reason=f'Invalid LY percentage value: {value_str}'
                    ))
            # Try standard pattern
            std_match = self.standard_pattern.search(line)
            if std_match:
                period_str = std_match.group(1)
                value_str = std_match.group(2)
                try:
                    period_years = float(period_str)
                    value_pct = float(value_str)
                    records.append(ParsedRecord(
                        company_id=company_id,
                        metric_type=metric_type,
                        period_years=period_years,
                        value_pct=value_pct
                    ))
                    continue
                except ValueError:
                    self.parse_failures.append(ParseFailure(
                        id=row_id, company_id=company_id, metric_type=metric_type,
                        raw_text=line, reason=f'Invalid numeric value in: {period_str} Years, {value_str}%'
                    ))
            # No pattern matched
            self.parse_failures.append(ParseFailure(
                id=row_id, company_id=company_id, metric_type=metric_type,
                raw_text=line, reason='No matching pattern found'
            ))
        # Also add to parsed_records for consistency with to_dataframes
        self.parsed_records.extend(records)
        return records
    
    def parse_dataframe(self, df):
        self.parsed_records = []
        self.parse_failures = []
        metric_columns = [
            'compounded_sales_growth',
            'compounded_profit_growth',
            'stock_price_cagr',
            'roe'
        ]
        for _, row in df.iterrows():
            row_id = row['id']
            company_id = row['company_id']
            for metric_type in metric_columns:
                cell_text = row[metric_type]
                self.parse_cell(cell_text, company_id, metric_type, row_id)
        return self.parsed_records, self.parse_failures
    
    def to_dataframes(self):
        if self.parsed_records:
            parsed_df = pd.DataFrame([
                {'company_id': r.company_id, 'metric_type': r.metric_type,
                 'period_years': r.period_years, 'value_pct': r.value_pct}
                for r in self.parsed_records
            ])
        else:
            parsed_df = pd.DataFrame(columns=['company_id', 'metric_type', 'period_years', 'value_pct'])
        if self.parse_failures:
            failures_df = pd.DataFrame([
                {'id': f.id, 'company_id': f.company_id, 'metric_type': f.metric_type,
                 'raw_text': f.raw_text, 'reason': f.reason}
                for f in self.parse_failures
            ])
        else:
            failures_df = pd.DataFrame(columns=['id', 'company_id', 'metric_type', 'raw_text', 'reason'])
        return parsed_df, failures_df

def parse_analysis_text(text, company_id, metric_type, row_id):
    parser = AnalysisTextParser()
    return parser.parse_cell(text, company_id, metric_type, row_id)

def parse_cell_value(text):
    # Try TTM
    ttm_match = TTM_PATTERN.search(str(text))
    if ttm_match:
        try:
            return 0.0, float(ttm_match.group(1))
        except ValueError:
            return None
    # Try Last Year
    ly_match = LAST_YEAR_PATTERN.search(str(text))
    if ly_match:
        try:
            return 1.0, float(ly_match.group(1))
        except ValueError:
            return None
    # Try LY (abbreviated)
    ly_abbr_match = LY_PATTERN.search(str(text))
    if ly_abbr_match:
        try:
            return 1.0, float(ly_abbr_match.group(1))
        except ValueError:
            return None
    # Try standard
    std_match = STANDARD_PATTERN.search(str(text))
    if std_match:
        try:
            return float(std_match.group(1)), float(std_match.group(2))
        except ValueError:
            return None
    return None

def cross_validate_cagr(parsed_df, profit_loss_df, stock_prices_df, companies_df):
    from ..analytics.cagr import calculate_cagr
    validation_results = []
    for _, row in parsed_df.iterrows():
        company_id = row['company_id']
        metric_type = row['metric_type']
        period_years = row['period_years']
        parsed_value = row['value_pct']
        if metric_type == 'roe':
            validation_results.append({
                'company_id': company_id, 'metric_type': metric_type,
                'period_years': period_years, 'parsed_value_pct': parsed_value,
                'computed_value_pct': None, 'divergence_pct': None,
                'divergence_flag': 'SKIPPED: ROE is not a CAGR metric'
            })
            continue
        if period_years == 0:
            validation_results.append({
                'company_id': company_id, 'metric_type': metric_type,
                'period_years': period_years, 'parsed_value_pct': parsed_value,
                'computed_value_pct': None, 'divergence_pct': None,
                'divergence_flag': 'SKIPPED: TTM period (not year-based)'
            })
            continue
        computed_value = None
        divergence = None
        flag = None
        if metric_type == 'compounded_sales_growth':
            company_pl = profit_loss_df[profit_loss_df['company_id'] == company_id].copy()
            if len(company_pl) >= 2:
                company_pl['year_sorted'] = company_pl['year'].astype(str)
                company_pl = company_pl.sort_values('year')
                start_sales = company_pl.iloc[0]['sales']
                end_sales = company_pl.iloc[-1]['sales']
                try:
                    start_year = int(str(company_pl.iloc[0]['year']).split()[-1])
                    end_year = int(str(company_pl.iloc[-1]['year']).split()[-1])
                    actual_years = end_year - start_year
                    if actual_years > 0:
                        computed_value = calculate_cagr(start_sales, end_sales, actual_years)
                except (ValueError, IndexError):
                    pass
        elif metric_type == 'compounded_profit_growth':
            company_pl = profit_loss_df[profit_loss_df['company_id'] == company_id].copy()
            if len(company_pl) >= 2:
                company_pl = company_pl.sort_values('year')
                start_profit = company_pl.iloc[0]['net_profit']
                end_profit = company_pl.iloc[-1]['net_profit']
                try:
                    start_year = int(str(company_pl.iloc[0]['year']).split()[-1])
                    end_year = int(str(company_pl.iloc[-1]['year']).split()[-1])
                    actual_years = end_year - start_year
                    if actual_years > 0:
                        computed_value = calculate_cagr(start_profit, end_profit, actual_years)
                except (ValueError, IndexError):
                    pass
        elif metric_type == 'stock_price_cagr':
            company_sp = stock_prices_df[stock_prices_df['company_id'] == company_id].copy()
            if len(company_sp) >= 2:
                company_sp = company_sp.sort_values('date')
                start_price = company_sp.iloc[0]['close']
                end_price = company_sp.iloc[-1]['close']
                try:
                    start_date = pd.to_datetime(company_sp.iloc[0]['date'])
                    end_date = pd.to_datetime(company_sp.iloc[-1]['date'])
                    actual_years = (end_date - start_date).days / 365.25
                    if actual_years > 0:
                        computed_value = calculate_cagr(start_price, end_price, actual_years)
                except (ValueError, KeyError, IndexError):
                    pass
        if computed_value is not None:
            divergence = abs(parsed_value - computed_value)
            if divergence > 5.0:
                flag = f'DIVERGENCE >5%: parsed={parsed_value:.2f}%, computed={computed_value:.2f}%'
            else:
                flag = f'OK: parsed={parsed_value:.2f}%, computed={computed_value:.2f}%'
        else:
            flag = 'NO COMPARABLE DATA: Insufficient source data for cross-validation'
        validation_results.append({
            'company_id': company_id, 'metric_type': metric_type,
            'period_years': period_years, 'parsed_value_pct': parsed_value,
            'computed_value_pct': computed_value, 'divergence_pct': divergence,
            'divergence_flag': flag
        })
    return pd.DataFrame(validation_results)

def main():
    project_root = Path(__file__).resolve().parents[2]
    analysis_path = project_root / 'Data' / 'raw' / 'analysis.xlsx'
    output_dir = project_root / 'Data' / 'output'
    output_dir.mkdir(parents=True, exist_ok=True)
    df = pd.read_excel(analysis_path, sheet_name='Analysis', header=1)
    parser = AnalysisTextParser()
    parser.parse_dataframe(df)
    parsed_df, failures_df = parser.to_dataframes()
    parsed_path = output_dir / 'analysis_parsed.csv'
    parsed_df.to_csv(parsed_path, index=False)
    print(f'Saved {len(parsed_df)} parsed records to {parsed_path}')
    failures_path = output_dir / 'parse_failures.csv'
    failures_df.to_csv(failures_path, index=False)
    print(f'Saved {len(failures_df)} parse failures to {failures_path}')
    pl_path = project_root / 'Data' / 'raw' / 'profitandloss.xlsx'
    sp_path = project_root / 'Data' / 'raw' / 'stock_prices.xlsx'
    comp_path = project_root / 'Data' / 'raw' / 'companies.xlsx'
    profit_loss_df = pd.read_excel(pl_path, header=1)
    stock_prices_df = pd.read_excel(sp_path, header=1)
    companies_df = pd.read_excel(comp_path, header=1)
    stock_prices_df.columns = ['id', 'company_id', 'date', 'open', 'high', 'low', 'close', 'volume', 'adj_close']
    validation_df = cross_validate_cagr(parsed_df, profit_loss_df, stock_prices_df, companies_df)
    validation_path = output_dir / 'cagr_cross_validation.csv'
    validation_df.to_csv(validation_path, index=False)
    print(f'Saved cross-validation results to {validation_path}')
    print('=== SUMMARY ===')
    print(f'Total parsed records: {len(parsed_df)}')
    print(f'Total parse failures: {len(failures_df)}')
    print(f'Cross-validation results: {len(validation_df)}')
    divergence_count = len(validation_df[validation_df['divergence_flag'].str.contains('DIVERGENCE >5%', na=False)])
    print(f'Records with >5% divergence: {divergence_count}')
    if len(failures_df) > 0:
        print('Parse failure breakdown:')
        print(failures_df.groupby('reason').size())

if __name__ == '__main__':
    main()
