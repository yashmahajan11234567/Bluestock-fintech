import pathlib

engine_path = pathlib.Path("src/screener/engine.py")
existing = engine_path.read_text(encoding="utf-8")

new_functions = """

def _winsorize_and_scale(series, higher_is_better=True):
    \"\"\"Winsorize at P10/P90 and scale to [0, 100].\"\"\"
    import pandas as pd
    import numpy as np
    s = pd.to_numeric(series, errors="coerce")
    nan_mask = s.isna()
    valid = s[~nan_mask]
    if len(valid) == 0:
        return pd.Series(np.nan, index=series.index)
    p10 = valid.quantile(0.10)
    p90 = valid.quantile(0.90)
    s_w = s.clip(lower=p10, upper=p90)
    mn = s_w.min()
    mx = s_w.max()
    if mx == mn:
        r = pd.Series(np.nan, index=series.index)
        r[~nan_mask] = 50.0
    else:
        r = (s_w - mn) / (mx - mn) * 100.0
        r[nan_mask] = np.nan
    if not higher_is_better:
        r = 100.0 - r
    return r


def compute_profitability_score(df):
    \"\"\"Profitability score from ROE and Operating Profit Margin.\"\"\"
    import numpy as np
    roe = _winsorize_and_scale(df["return_on_equity_pct"], higher_is_better=True)
    opm = _winsorize_and_scale(df["operating_profit_margin_pct"], higher_is_better=True)
    return (roe + opm) / 2.0


def compute_cash_quality_score(df):
    \"\"\"Cash quality score from Free Cash Flow and Operating Cash Flow.\"\"\"
    import numpy as np
    cols = [c for c in ["free_cash_flow_cr", "cash_from_operations_cr"] if c in df.columns]
    if not cols:
        import pandas as pd
        return pd.Series(50.0, index=df.index)
    scaled = [_winsorize_and_scale(df[c], higher_is_better=True) for c in cols]
    if len(scaled) == 1:
        return scaled[0]
    return (scaled[0] + scaled[1]) / 2.0


def compute_growth_score(df):
    \"\"\"Growth score placeholder: returns 50 (no CAGR data).\"\"\"
    import pandas as pd
    return pd.Series(50.0, index=df.index)


def compute_leverage_score(df):
    \"\"\"Leverage score from Debt-to-Equity and Interest Coverage.\"\"\"
    import numpy as np
    import pandas as pd
    # Interest Coverage: treat 'Debt Free' as max value
    ic = df["interest_coverage"]
    ic_num = pd.to_numeric(ic, errors="coerce")
    debt_free = ic.apply(lambda x: isinstance(x, str) and x.strip().lower() == "debt free")
    if debt_free.any():
        mx = ic_num.max()
        if pd.notna(mx):
            ic_num = ic_num.copy()
            ic_num[debt_free] = mx
    de = _winsorize_and_scale(df["debt_to_equity"], higher_is_better=False)
    ic_s = _winsorize_and_scale(ic_num, higher_is_better=True)
    return (de + ic_s) / 2.0

"""

engine_path.write_text(existing + new_functions, encoding="utf-8")
print("Scoring functions added.")
