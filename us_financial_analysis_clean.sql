CREATE TABLE IF NOT EXISTS fdic_banks (
    cert            INT PRIMARY KEY,
    name            TEXT,
    city            TEXT,
    stname          TEXT,
    stalp           TEXT,
    asset           NUMERIC,
    dep             NUMERIC,
    netinc          NUMERIC,
    lnlsnet         NUMERIC,
    eq              NUMERIC,
    repdte          TEXT,
    active          INT
);

CREATE TABLE IF NOT EXISTS fdic_financials (
    cert            INT,
    repdte          TEXT,
    asset           NUMERIC,
    dep             NUMERIC,
    netinc          NUMERIC,
    lnlsnet         NUMERIC,
    eq              NUMERIC,
    intinc          NUMERIC,
    eintexp         NUMERIC,
    nonii           NUMERIC,
    nonix           NUMERIC,
    PRIMARY KEY (cert, repdte)
);

CREATE TABLE IF NOT EXISTS fed_consumer_credit (
    report_date     DATE PRIMARY KEY,
    total_credit    NUMERIC,
    revolving       NUMERIC,
    nonrevolving    NUMERIC,
    auto_loans      NUMERIC,
    student_loans   NUMERIC
);


SELECT * FROM fdic_banks LIMIT 10;

SELECT COUNT(*) AS total_banks FROM fdic_banks;

SELECT
    active,
    COUNT(*) AS bank_count
FROM fdic_banks
GROUP BY active;


SELECT
    stname                              AS state,
    COUNT(*)                            AS number_of_banks,
    ROUND(SUM(asset) / 1000000, 2)     AS total_assets_billions,
    ROUND(AVG(asset) / 1000, 2)        AS avg_assets_millions
FROM fdic_banks
WHERE active = 1
GROUP BY stname
ORDER BY total_assets_billions DESC
LIMIT 15;


SELECT
    stname                                          AS state,
    COUNT(*)                                        AS number_of_banks,
    ROUND(SUM(netinc) / 1000000, 2)               AS total_net_income_billions,
    ROUND(AVG(netinc) / 1000, 2)                  AS avg_net_income_millions,
    ROUND(SUM(netinc) / NULLIF(SUM(asset), 0) * 100, 4) AS return_on_assets_pct
FROM fdic_banks
WHERE active = 1
GROUP BY stname
HAVING SUM(netinc) IS NOT NULL
ORDER BY return_on_assets_pct DESC
LIMIT 20;


SELECT
    CASE
        WHEN asset < 100000         THEN '1. Community Bank (Under $100M)'
        WHEN asset < 1000000        THEN '2. Mid-Size Bank ($100M - $1B)'
        WHEN asset < 10000000       THEN '3. Regional Bank ($1B - $10B)'
        WHEN asset < 100000000      THEN '4. Large Bank ($10B - $100B)'
        ELSE                             '5. Mega Bank (Over $100B)'
    END                             AS bank_tier,
    COUNT(*)                        AS number_of_banks,
    ROUND(AVG(netinc) / 1000, 2)  AS avg_net_income_millions,
    ROUND(SUM(asset) / 1000000, 2) AS total_assets_billions
FROM fdic_banks
WHERE active = 1
GROUP BY bank_tier
ORDER BY bank_tier;


SELECT
    stname                                              AS state,
    COUNT(*)                                            AS total_banks,
    SUM(CASE WHEN netinc < 0 THEN 1 ELSE 0 END)       AS unprofitable_banks,
    ROUND(
        SUM(CASE WHEN netinc < 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2
    )                                                   AS pct_unprofitable
FROM fdic_banks
WHERE active = 1
GROUP BY stname
HAVING COUNT(*) >= 10
ORDER BY pct_unprofitable DESC
LIMIT 15;


SELECT
    b.name                                          AS bank_name,
    b.stname                                        AS state,
    b.city,
    ROUND(b.asset / 1000, 2)                       AS assets_millions,
    ROUND(f.intinc / 1000, 2)                      AS interest_income_millions,
    ROUND(f.eintexp / 1000, 2)                     AS interest_expense_millions,
    ROUND((f.intinc - f.eintexp) / 1000, 2)       AS net_interest_margin_millions,
    ROUND(f.nonii / 1000, 2)                       AS noninterest_income_millions
FROM fdic_banks b
INNER JOIN fdic_financials f
    ON b.cert = f.cert
    AND b.repdte = f.repdte
WHERE b.active = 1
    AND b.asset > 1000000
ORDER BY net_interest_margin_millions DESC
LIMIT 20;


SELECT
    b.name          AS bank_name,
    b.stname        AS state,
    b.asset,
    f.cert          AS has_financial_record
FROM fdic_banks b
LEFT JOIN fdic_financials f
    ON b.cert = f.cert
WHERE b.active = 1
    AND f.cert IS NULL
ORDER BY b.asset DESC
LIMIT 20;


SELECT
    b.name                                          AS bank_name,
    b.stname                                        AS state,
    ROUND(b.asset / 1000, 2)                       AS assets_millions,
    ROUND(b.netinc / 1000, 2)                      AS net_income_millions,
    ROUND(state_avg.avg_assets / 1000, 2)          AS state_avg_assets_millions,
    CASE
        WHEN b.asset > state_avg.avg_assets THEN 'Above State Average'
        ELSE 'Below State Average'
    END                                             AS size_vs_state
FROM fdic_banks b
INNER JOIN (
    SELECT
        stname,
        AVG(asset)  AS avg_assets,
        AVG(netinc) AS avg_netinc
    FROM fdic_banks
    WHERE active = 1
    GROUP BY stname
) AS state_avg
    ON b.stname = state_avg.stname
WHERE b.active = 1
ORDER BY b.stname, b.asset DESC;


SELECT
    b.stname                                                AS state,
    COUNT(*)                                                AS bank_count,
    ROUND(AVG(b.eq / NULLIF(b.asset, 0)) * 100, 2)       AS avg_equity_ratio_pct,
    ROUND(MIN(b.eq / NULLIF(b.asset, 0)) * 100, 2)       AS min_equity_ratio_pct,
    ROUND(MAX(b.eq / NULLIF(b.asset, 0)) * 100, 2)       AS max_equity_ratio_pct
FROM fdic_banks b
WHERE b.active = 1
    AND b.eq > 0
GROUP BY b.stname
HAVING COUNT(*) >= 5
ORDER BY avg_equity_ratio_pct ASC
LIMIT 15;


WITH monthly_credit AS (
    SELECT
        report_date,
        EXTRACT(YEAR FROM report_date)      AS year,
        EXTRACT(MONTH FROM report_date)     AS month,
        total_credit,
        revolving,
        nonrevolving,
        COALESCE(auto_loans, 0)            AS auto_loans,
        COALESCE(student_loans, 0)         AS student_loans
    FROM fed_consumer_credit
    WHERE report_date >= '2010-01-01'
)
SELECT
    year,
    month,
    ROUND(total_credit, 2)                  AS total_credit_billions,
    ROUND(revolving, 2)                     AS revolving_billions,
    ROUND(nonrevolving, 2)                  AS nonrevolving_billions,
    ROUND(auto_loans, 2)                    AS auto_loans_billions,
    ROUND(student_loans, 2)                 AS student_loans_billions
FROM monthly_credit
ORDER BY year, month;


WITH monthly_credit AS (
    SELECT
        report_date,
        EXTRACT(YEAR FROM report_date)  AS year,
        EXTRACT(MONTH FROM report_date) AS month,
        total_credit,
        revolving,
        nonrevolving
    FROM fed_consumer_credit
    WHERE report_date >= '2010-01-01'
)
SELECT
    year,
    month,
    ROUND(total_credit, 2)                  AS total_credit_billions,
    ROUND(
        SUM(total_credit) OVER (
            ORDER BY year, month
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ), 2
    )                                       AS running_total_billions,
    ROUND(
        AVG(total_credit) OVER (
            ORDER BY year, month
            ROWS BETWEEN 11 PRECEDING AND CURRENT ROW
        ), 2
    )                                       AS rolling_12mo_avg_billions
FROM monthly_credit
ORDER BY year, month;


WITH annual_credit AS (
    SELECT
        EXTRACT(YEAR FROM report_date)      AS year,
        AVG(total_credit)                   AS avg_total_credit,
        AVG(revolving)                      AS avg_revolving,
        AVG(nonrevolving)                   AS avg_nonrevolving,
        AVG(auto_loans)                     AS avg_auto_loans,
        AVG(student_loans)                  AS avg_student_loans
    FROM fed_consumer_credit
    WHERE report_date >= '2010-01-01'
    GROUP BY EXTRACT(YEAR FROM report_date)
)
SELECT
    year,
    ROUND(avg_total_credit, 2)              AS total_credit_billions,
    ROUND(LAG(avg_total_credit) OVER (ORDER BY year), 2) AS prior_year_total,
    ROUND(
        (avg_total_credit - LAG(avg_total_credit) OVER (ORDER BY year))
        / NULLIF(LAG(avg_total_credit) OVER (ORDER BY year), 0) * 100, 2
    )                                       AS yoy_growth_pct,
    ROUND(
        (avg_auto_loans - LAG(avg_auto_loans) OVER (ORDER BY year))
        / NULLIF(LAG(avg_auto_loans) OVER (ORDER BY year), 0) * 100, 2
    )                                       AS auto_loan_yoy_growth_pct,
    ROUND(
        (avg_student_loans - LAG(avg_student_loans) OVER (ORDER BY year))
        / NULLIF(LAG(avg_student_loans) OVER (ORDER BY year), 0) * 100, 2
    )                                       AS student_loan_yoy_growth_pct,
    ROUND(
        (avg_revolving - LAG(avg_revolving) OVER (ORDER BY year))
        / NULLIF(LAG(avg_revolving) OVER (ORDER BY year), 0) * 100, 2
    )                                       AS revolving_yoy_growth_pct
FROM annual_credit
ORDER BY year;


WITH annual_credit AS (
    SELECT
        EXTRACT(YEAR FROM report_date)  AS year,
        AVG(total_credit)               AS avg_total_credit,
        AVG(auto_loans)                 AS avg_auto_loans,
        AVG(student_loans)              AS avg_student_loans
    FROM fed_consumer_credit
    WHERE report_date >= '2010-01-01'
    GROUP BY EXTRACT(YEAR FROM report_date)
),
with_growth AS (
    SELECT
        year,
        avg_total_credit,
        avg_auto_loans,
        avg_student_loans,
        (avg_total_credit - LAG(avg_total_credit) OVER (ORDER BY year))
        / NULLIF(LAG(avg_total_credit) OVER (ORDER BY year), 0) * 100 AS total_yoy_growth_pct
    FROM annual_credit
)
SELECT
    year,
    ROUND(avg_total_credit, 2)          AS total_credit_billions,
    ROUND(total_yoy_growth_pct, 2)      AS yoy_growth_pct,
    RANK() OVER (ORDER BY total_yoy_growth_pct DESC) AS growth_rank
FROM with_growth
WHERE total_yoy_growth_pct IS NOT NULL
ORDER BY year;


WITH category_data AS (
    SELECT
        EXTRACT(YEAR FROM report_date)  AS year,
        'Revolving'                     AS debt_category,
        AVG(revolving)                  AS avg_amount
    FROM fed_consumer_credit
    WHERE report_date >= '2010-01-01'
    GROUP BY EXTRACT(YEAR FROM report_date)

    UNION ALL

    SELECT
        EXTRACT(YEAR FROM report_date),
        'Auto Loans',
        AVG(auto_loans)
    FROM fed_consumer_credit
    WHERE report_date >= '2010-01-01'
        AND auto_loans IS NOT NULL
    GROUP BY EXTRACT(YEAR FROM report_date)

    UNION ALL

    SELECT
        EXTRACT(YEAR FROM report_date),
        'Student Loans',
        AVG(student_loans)
    FROM fed_consumer_credit
    WHERE report_date >= '2010-01-01'
        AND student_loans IS NOT NULL
    GROUP BY EXTRACT(YEAR FROM report_date)
),
with_growth AS (
    SELECT
        year,
        debt_category,
        avg_amount,
        (avg_amount - LAG(avg_amount) OVER (PARTITION BY debt_category ORDER BY year))
        / NULLIF(LAG(avg_amount) OVER (PARTITION BY debt_category ORDER BY year), 0)
        * 100 AS yoy_growth_pct
    FROM category_data
)
SELECT
    year,
    debt_category,
    ROUND(avg_amount, 2)                    AS amount_billions,
    ROUND(yoy_growth_pct, 2)               AS yoy_growth_pct,
    RANK() OVER (PARTITION BY year ORDER BY yoy_growth_pct DESC) AS rank_within_year
FROM with_growth
WHERE yoy_growth_pct IS NOT NULL
ORDER BY year, rank_within_year;


WITH
annual_debt AS (
    SELECT
        EXTRACT(YEAR FROM report_date)      AS year,
        ROUND(AVG(total_credit), 2)         AS avg_total_debt_billions,
        ROUND(AVG(revolving), 2)            AS avg_revolving_billions,
        ROUND(AVG(nonrevolving), 2)         AS avg_nonrevolving_billions
    FROM fed_consumer_credit
    WHERE report_date >= '2015-01-01'
    GROUP BY EXTRACT(YEAR FROM report_date)
),
debt_growth AS (
    SELECT
        year,
        avg_total_debt_billions,
        avg_revolving_billions,
        avg_nonrevolving_billions,
        ROUND(
            (avg_total_debt_billions - LAG(avg_total_debt_billions) OVER (ORDER BY year))
            / NULLIF(LAG(avg_total_debt_billions) OVER (ORDER BY year), 0) * 100, 2
        )                                   AS debt_yoy_growth_pct
    FROM annual_debt
),
bank_health AS (
    SELECT
        SUBSTRING(repdte, 1, 4)::INT        AS year,
        COUNT(*)                            AS active_banks,
        ROUND(AVG(netinc / NULLIF(asset, 0)) * 100, 4) AS avg_roa_pct,
        SUM(CASE WHEN netinc < 0 THEN 1 ELSE 0 END) AS unprofitable_bank_count,
        ROUND(
            SUM(CASE WHEN netinc < 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2
        )                                   AS pct_unprofitable
    FROM fdic_banks
    WHERE active = 1
    GROUP BY SUBSTRING(repdte, 1, 4)
)
SELECT
    d.year,
    d.avg_total_debt_billions,
    d.debt_yoy_growth_pct,
    d.avg_revolving_billions,
    d.avg_nonrevolving_billions,
    b.active_banks,
    b.avg_roa_pct                           AS bank_avg_return_on_assets,
    b.unprofitable_bank_count,
    b.pct_unprofitable                      AS pct_banks_unprofitable,
    CASE
        WHEN d.debt_yoy_growth_pct > 5
         AND b.pct_unprofitable > 15        THEN 'HIGH RISK'
        WHEN d.debt_yoy_growth_pct > 3
          OR b.pct_unprofitable > 10        THEN 'MODERATE RISK'
        ELSE                                     'LOW RISK'
    END                                     AS systemic_risk_signal
FROM debt_growth d
LEFT JOIN bank_health b
    ON d.year = b.year
WHERE d.debt_yoy_growth_pct IS NOT NULL
ORDER BY d.year;
