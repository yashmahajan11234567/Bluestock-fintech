PRAGMA foreign_keys = ON;

-- Table: companies
-- Stores core company information such as name, ticker, logos, links, and financial ratios like ROCE and ROE.
-- The 'id' column holds the ticker symbol (text) as the natural primary key.
CREATE TABLE companies (
    id TEXT PRIMARY KEY,
    company_logo TEXT,
    company_name TEXT NOT NULL,
    chart_link TEXT,
    about_company TEXT,
    website TEXT,
    nse_profile TEXT,
    bse_profile TEXT,
    face_value REAL,
    book_value REAL,
    roe_percentage REAL,
    roce_percentage REAL
);

-- Table: profitandloss
-- Contains profit and loss statement line items for each company and year.
CREATE TABLE profitandloss (
    id INTEGER PRIMARY KEY,
    company_id TEXT NOT NULL,
    year TEXT,
    sales INTEGER,
    expenses INTEGER,
    operating_profit REAL,
    opm_percentage REAL,
    other_income INTEGER,
    interest INTEGER,
    depreciation INTEGER,
    profit_before_tax INTEGER,
    tax_percentage REAL,
    net_profit INTEGER,
    eps REAL,
    dividend_payout REAL,
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

-- Table: balancesheet
-- Contains balance sheet line items for each company and year.
CREATE TABLE balancesheet (
    id INTEGER PRIMARY KEY,
    company_id TEXT NOT NULL,
    year TEXT,
    equity_capital INTEGER,
    reserves INTEGER,
    borrowings INTEGER,
    other_liabilities INTEGER,
    total_liabilities INTEGER,
    fixed_assets INTEGER,
    cwip INTEGER,
    investments INTEGER,
    other_asset INTEGER,
    total_assets INTEGER,
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

-- Table: cashflow
-- Contains cash flow statement categories for each company and year.
CREATE TABLE cashflow (
    id INTEGER PRIMARY KEY,
    company_id TEXT NOT NULL,
    year TEXT,
    operating_activity REAL,
    investing_activity REAL,
    financing_activity REAL,
    net_cash_flow REAL,
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

-- Table: analysis
-- Contains growth and return metrics (e.g., CAGR, ROE) for each company.
CREATE TABLE analysis (
    id INTEGER PRIMARY KEY,
    company_id TEXT NOT NULL,
    compounded_sales_growth TEXT,
    compounded_profit_growth TEXT,
    stock_price_cagr TEXT,
    roe TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

-- Table: documents
-- Stores links to annual reports and other documents for each company and year.
CREATE TABLE documents (
    id INTEGER PRIMARY KEY,
    company_id TEXT NOT NULL,
    Year INTEGER,
    Annual_Report TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

-- Table: prosandcons
-- Contains qualitative pros and cons for each company.
CREATE TABLE prosandcons (
    id INTEGER PRIMARY KEY,
    company_id TEXT NOT NULL,
    pros TEXT,
    cons TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

-- Table: sectors
-- Maps each company to its sector, sub-sector, index weight, and market cap category.
CREATE TABLE sectors (
    id INTEGER PRIMARY KEY,
    company_id TEXT NOT NULL,
    broad_sector TEXT,
    sub_sector TEXT,
    index_weight_pct REAL,
    market_cap_category TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

-- Table: stock_prices
-- Contains daily stock price data (open, high, low, close, volume, adjusted close) for each company.
CREATE TABLE stock_prices (
    id INTEGER PRIMARY KEY,
    company_id TEXT NOT NULL,
    date TEXT,
    open_price REAL,
    high_price REAL,
    low_price REAL,
    close_price REAL,
    volume INTEGER,
    adjusted_close REAL,
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

-- Table: financial_ratios
-- Stores various financial ratios (margins, returns, leverage, turnover, etc.) for each company and year.
CREATE TABLE financial_ratios (
    id INTEGER PRIMARY KEY,
    company_id TEXT NOT NULL,
    year TEXT,
    net_profit_margin_pct REAL,
    operating_profit_margin_pct REAL,
    return_on_equity_pct REAL,
    debt_to_equity REAL,
    interest_coverage REAL,
    asset_turnover REAL,
    free_cash_flow_cr REAL,
    capex_cr REAL,
    earnings_per_share REAL,
    book_value_per_share REAL,
    dividend_payout_ratio_pct REAL,
    total_debt_cr INTEGER,
    cash_from_operations_cr REAL,
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

-- Indexes for improved query performance
CREATE INDEX idx_companies_id ON companies(id);
CREATE INDEX idx_profitandloss_company_id ON profitandloss(company_id);
CREATE INDEX idx_profitandloss_year ON profitandloss(year);
CREATE INDEX idx_balancesheet_company_id ON balancesheet(company_id);
CREATE INDEX idx_balancesheet_year ON balancesheet(year);
CREATE INDEX idx_cashflow_company_id ON cashflow(company_id);
CREATE INDEX idx_cashflow_year ON cashflow(year);
CREATE INDEX idx_analysis_company_id ON analysis(company_id);
CREATE INDEX idx_documents_company_id ON documents(company_id);
CREATE INDEX idx_documents_year ON documents(Year);
CREATE INDEX idx_prosandcons_company_id ON prosandcons(company_id);
CREATE INDEX idx_sectors_company_id ON sectors(company_id);
CREATE INDEX idx_stock_prices_company_id ON stock_prices(company_id);
CREATE INDEX idx_stock_prices_date ON stock_prices(date);
CREATE INDEX idx_financial_ratios_company_id ON financial_ratios(company_id);
CREATE INDEX idx_financial_ratios_year ON financial_ratios(year);