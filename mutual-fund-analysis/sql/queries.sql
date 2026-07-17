-- 1. Top 5 funds by AUM

SELECT
    scheme_name,
    aum_crore
FROM 07_scheme_performance
ORDER BY aum_crore DESC
LIMIT 5;


-- 2. Average NAV per month

SELECT
    strftime('%Y-%m', date) AS month,
    ROUND(AVG(nav),2) AS avg_nav
FROM 02_nav_history
GROUP BY month
ORDER BY month;


-- 3. SIP Year-over-Year Growth

SELECT
    strftime('%Y', transaction_date) AS year,
    COUNT(*) AS sip_transactions,
    SUM(amount_inr) AS total_amount
FROM 08_investor_transactions
WHERE transaction_type='Sip'
GROUP BY year;


-- 4. Transactions by State

SELECT
    state,
    COUNT(*) AS total_transactions,
    SUM(amount_inr) AS amount
FROM 08_investor_transactions
GROUP BY state
ORDER BY amount DESC;


-- 5. Funds with expense ratio below 1%

SELECT
    scheme_name,
    expense_ratio_pct
FROM 07_scheme_performance
WHERE expense_ratio_pct < 1
ORDER BY expense_ratio_pct;


-- 6. Average Expense Ratio by Fund House

SELECT
    fund_house,
    ROUND(AVG(expense_ratio_pct),2) AS avg_expense
FROM 07_scheme_performance
GROUP BY fund_house;


-- 7. Count of Funds by Category

SELECT
    category,
    COUNT(*) AS total_funds
FROM 07_scheme_performance
GROUP BY category;


-- 8. Highest 5-Year Returns

SELECT
    scheme_name,
    return_5yr_pct
FROM 07_scheme_performance
ORDER BY return_5yr_pct DESC
LIMIT 5;


-- 9. Transactions by Payment Mode

SELECT
    payment_mode,
    COUNT(*) AS transactions
FROM 08_investor_transactions
GROUP BY payment_mode;


-- 10. Average Transaction Amount

SELECT
    transaction_type,
    ROUND(AVG(amount_inr),2) AS average_amount
FROM 08_investor_transactions
GROUP BY transaction_type;