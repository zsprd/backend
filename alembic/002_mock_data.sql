-- =====================================================
-- COMPREHENSIVE MOCK DATA FOR PORTFOLIO ANALYTICS
-- 6 months of realistic financial data (March-Sept 2025)
-- =====================================================

BEGIN;

-- =====================================================
-- REFERENCE DATA
-- =====================================================

-- Currencies
INSERT INTO reference_currencies (currency_code, name, symbol, decimal_places)
VALUES ('USD', 'US Dollar', '$', 2),
       ('EUR', 'Euro', '€', 2),
       ('GBP', 'British Pound', '£', 2),
       ('JPY', 'Japanese Yen', '¥', 0),
       ('CAD', 'Canadian Dollar', 'C$', 2),
       ('CHF', 'Swiss Franc', 'CHF', 2),
       ('AUD', 'Australian Dollar', 'A$', 2);

-- Countries
INSERT INTO reference_countries (country_code, country_name, region, currency_code, is_developed)
VALUES ('US', 'United States', 'North America', 'USD', true),
       ('UK', 'United Kingdom', 'Europe', 'GBP', true),
       ('DE', 'Germany', 'Europe', 'EUR', true),
       ('FR', 'France', 'Europe', 'EUR', true),
       ('JP', 'Japan', 'Asia', 'JPY', true),
       ('CA', 'Canada', 'North America', 'CAD', true),
       ('CH', 'Switzerland', 'Europe', 'CHF', true),
       ('AU', 'Australia', 'Asia-Pacific', 'AUD', true),
       ('CN', 'China', 'Asia', 'CNY', false),
       ('IN', 'India', 'Asia', 'INR', false);

-- Exchanges
INSERT INTO reference_exchanges (exchange_code, exchange_name, country_code, currency_code, timezone, market_open,
                                 market_close)
VALUES ('NYSE', 'New York Stock Exchange', 'US', 'USD', 'America/New_York', '09:30:00', '16:00:00'),
       ('NASDAQ', 'NASDAQ Stock Market', 'US', 'USD', 'America/New_York', '09:30:00', '16:00:00'),
       ('LSE', 'London Stock Exchange', 'UK', 'GBP', 'Europe/London', '08:00:00', '16:30:00'),
       ('TSE', 'Tokyo Stock Exchange', 'JP', 'JPY', 'Asia/Tokyo', '09:00:00', '15:30:00'),
       ('TSX', 'Toronto Stock Exchange', 'CA', 'CAD', 'America/Toronto', '09:30:00', '16:00:00'),
       ('XETRA', 'XETRA', 'DE', 'EUR', 'Europe/Berlin', '09:00:00', '17:30:00');

-- Provider Institutions
INSERT INTO provider_institutions (institution_code, name, institution_type, country)
VALUES ('chase', 'JPMorgan Chase Bank', 'bank', 'US'),
       ('schwab', 'Charles Schwab Corporation', 'broker', 'US'),
       ('fidelity', 'Fidelity Investments', 'broker', 'US'),
       ('vanguard', 'Vanguard Group', 'broker', 'US'),
       ('merrill', 'Merrill Lynch', 'broker', 'US'),
       ('yfinance', 'Yahoo Finance', 'data_provider', 'US'),
       ('alphavantage', 'Alpha Vantage', 'data_provider', 'US'),
       ('plaid', 'Plaid Technologies', 'data_provider', 'US');

-- =====================================================
-- SECURITY MASTER DATA
-- =====================================================

-- Major securities with realistic data
INSERT INTO security_master (id, symbol, name, security_type, security_subtype, currency, exchange, country, sector,
                             industry)
VALUES
-- Large Cap US Stocks
('550e8400-e29b-41d4-a716-446655440001', 'AAPL', 'Apple Inc.', 'equity', 'common stock', 'USD', 'NASDAQ', 'US',
 'Technology', 'Consumer Electronics'),
('550e8400-e29b-41d4-a716-446655440002', 'MSFT', 'Microsoft Corporation', 'equity', 'common stock', 'USD', 'NASDAQ',
 'US', 'Technology', 'Software'),
('550e8400-e29b-41d4-a716-446655440003', 'GOOGL', 'Alphabet Inc. Class A', 'equity', 'common stock', 'USD', 'NASDAQ',
 'US', 'Technology', 'Internet'),
('550e8400-e29b-41d4-a716-446655440004', 'AMZN', 'Amazon.com Inc.', 'equity', 'common stock', 'USD', 'NASDAQ', 'US',
 'Consumer Discretionary', 'E-commerce'),
('550e8400-e29b-41d4-a716-446655440005', 'TSLA', 'Tesla Inc.', 'equity', 'common stock', 'USD', 'NASDAQ', 'US',
 'Consumer Discretionary', 'Electric Vehicles'),
('550e8400-e29b-41d4-a716-446655440006', 'NVDA', 'NVIDIA Corporation', 'equity', 'common stock', 'USD', 'NASDAQ', 'US',
 'Technology', 'Semiconductors'),
('550e8400-e29b-41d4-a716-446655440007', 'JPM', 'JPMorgan Chase & Co.', 'equity', 'common stock', 'USD', 'NYSE', 'US',
 'Financials', 'Banking'),
('550e8400-e29b-41d4-a716-446655440008', 'JNJ', 'Johnson & Johnson', 'equity', 'common stock', 'USD', 'NYSE', 'US',
 'Healthcare', 'Pharmaceuticals'),

-- ETFs
('550e8400-e29b-41d4-a716-446655440010', 'SPY', 'SPDR S&P 500 ETF Trust', 'fund', 'etf', 'USD', 'NYSE', 'US',
 'Diversified', 'Index Fund'),
('550e8400-e29b-41d4-a716-446655440011', 'VTI', 'Vanguard Total Stock Market ETF', 'fund', 'etf', 'USD', 'NYSE', 'US',
 'Diversified', 'Index Fund'),
('550e8400-e29b-41d4-a716-446655440012', 'QQQ', 'Invesco QQQ Trust', 'fund', 'etf', 'USD', 'NASDAQ', 'US', 'Technology',
 'Index Fund'),
('550e8400-e29b-41d4-a716-446655440013', 'IWM', 'iShares Russell 2000 ETF', 'fund', 'etf', 'USD', 'NYSE', 'US',
 'Small Cap', 'Index Fund'),
('550e8400-e29b-41d4-a716-446655440014', 'EFA', 'iShares MSCI EAFE ETF', 'fund', 'etf', 'USD', 'NYSE', 'US',
 'International', 'Index Fund'),

-- Bonds
('550e8400-e29b-41d4-a716-446655440020', 'TLT', 'iShares 20+ Year Treasury Bond ETF', 'fund', 'etf', 'USD', 'NASDAQ',
 'US', 'Fixed Income', 'Government Bonds'),
('550e8400-e29b-41d4-a716-446655440021', 'AGG', 'iShares Core U.S. Aggregate Bond ETF', 'fund', 'etf', 'USD', 'NYSE',
 'US', 'Fixed Income', 'Corporate Bonds'),

-- Cash
('550e8400-e29b-41d4-a716-446655440030', 'CASH_USD', 'US Dollar Cash', 'cash', 'cash', 'USD', '', 'US', 'Cash', 'Cash'),
('550e8400-e29b-41d4-a716-446655440031', 'CASH_EUR', 'Euro Cash', 'cash', 'cash', 'EUR', '', 'EU', 'Cash', 'Cash');

-- Security identifiers
INSERT INTO security_identifiers (security_id, identifier_type, identifier_value, is_primary)
VALUES
-- Apple
('550e8400-e29b-41d4-a716-446655440001', 'cusip', '037833100', true),
('550e8400-e29b-41d4-a716-446655440001', 'isin', 'US0378331005', false),
-- Microsoft
('550e8400-e29b-41d4-a716-446655440002', 'cusip', '594918104', true),
('550e8400-e29b-41d4-a716-446655440002', 'isin', 'US5949181045', false),
-- SPY ETF
('550e8400-e29b-41d4-a716-446655440010', 'cusip', '78462F103', true),
('550e8400-e29b-41d4-a716-446655440010', 'isin', 'US78462F1030', false);

-- =====================================================
-- BENCHMARK MASTER DATA
-- =====================================================

INSERT INTO benchmark_master (id, symbol, name, description, currency, region, asset_class)
VALUES ('550e8400-e29b-41d4-a716-446655440100', 'SPY', 'S&P 500 Index', 'Large-cap US equity benchmark', 'USD', 'US',
        'Equity'),
       ('550e8400-e29b-41d4-a716-446655440101', 'VTI', 'Total Stock Market', 'Total US stock market benchmark', 'USD',
        'US', 'Equity'),
       ('550e8400-e29b-41d4-a716-446655440102', 'AGG', 'US Aggregate Bond', 'US investment grade bond benchmark', 'USD',
        'US', 'Fixed Income');

-- =====================================================
-- USER ACCOUNTS
-- =====================================================

INSERT INTO user_accounts (id, email, password_hash, full_name, timezone, base_currency, is_verified, created_at)
VALUES ('550e8400-e29b-41d4-a716-446655440201', 'john.doe@email.com', '$2b$10$N9qo8uLOickgx2ZMRZoMye', 'John Doe',
        'America/New_York', 'USD', true, '2024-12-15 10:30:00'),
       ('550e8400-e29b-41d4-a716-446655440202', 'sarah.smith@email.com', '$2b$10$N9qo8uLOickgx2ZMRZoMye', 'Sarah Smith',
        'America/Los_Angeles', 'USD', true, '2024-12-20 14:20:00'),
       ('550e8400-e29b-41d4-a716-446655440203', 'mike.johnson@email.com', '$2b$10$N9qo8uLOickgx2ZMRZoMye',
        'Mike Johnson', 'Europe/London', 'GBP', true, '2025-01-05 09:15:00'),
       ('550e8400-e29b-41d4-a716-446655440204', 'emma.wilson@email.com', '$2b$10$N9qo8uLOickgx2ZMRZoMye', 'Emma Wilson',
        'America/Chicago', 'USD', true, '2025-01-10 16:45:00');

-- User subscriptions
INSERT INTO user_subscriptions (id, user_id, plan_name, status, current_period_start, current_period_end, amount,
                                currency)
VALUES ('550e8400-e29b-41d4-a716-446655440301', '550e8400-e29b-41d4-a716-446655440201', 'premium', 'active',
        '2025-03-01', '2025-10-01', 29.99, 'USD'),
       ('550e8400-e29b-41d4-a716-446655440302', '550e8400-e29b-41d4-a716-446655440202', 'professional', 'active',
        '2025-02-15', '2025-09-15', 99.99, 'USD'),
       ('550e8400-e29b-41d4-a716-446655440303', '550e8400-e29b-41d4-a716-446655440203', 'premium', 'active',
        '2025-01-20', '2025-08-20', 29.99, 'GBP'),
       ('550e8400-e29b-41d4-a716-446655440304', '550e8400-e29b-41d4-a716-446655440204', 'free', 'active', '2025-01-10',
        '2025-08-10', 0.00, 'USD');

-- Provider connections
INSERT INTO provider_connections (id, user_id, institution_id, connection_name, provider_name, data_source, status,
                                  last_sync_at)
VALUES ('550e8400-e29b-41d4-a716-446655440401', '550e8400-e29b-41d4-a716-446655440201',
        (SELECT id FROM provider_institutions WHERE institution_code = 'schwab'),
        'Schwab Brokerage', 'plaid', 'plaid', 'active', '2025-09-17 06:00:00'),
       ('550e8400-e29b-41d4-a716-446655440402', '550e8400-e29b-41d4-a716-446655440202',
        (SELECT id FROM provider_institutions WHERE institution_code = 'fidelity'),
        'Fidelity 401k', 'plaid', 'plaid', 'active', '2025-09-17 06:15:00'),
       ('550e8400-e29b-41d4-a716-446655440403', '550e8400-e29b-41d4-a716-446655440203',
        (SELECT id FROM provider_institutions WHERE institution_code = 'vanguard'),
        'Vanguard ISA', 'manual', 'manual', 'active', '2025-09-16 18:30:00');

-- =====================================================
-- PORTFOLIO ACCOUNTS
-- =====================================================

INSERT INTO portfolio_accounts (id, user_id, institution_id, connection_id, name, account_type, account_subtype,
                                currency)
VALUES
-- John Doe's accounts
('550e8400-e29b-41d4-a716-446655440501', '550e8400-e29b-41d4-a716-446655440201',
 (SELECT id FROM provider_institutions WHERE institution_code = 'schwab'),
 '550e8400-e29b-41d4-a716-446655440401',
 'Schwab Taxable Brokerage', 'investment', 'brokerage', 'USD'),
('550e8400-e29b-41d4-a716-446655440502', '550e8400-e29b-41d4-a716-446655440201',
 (SELECT id FROM provider_institutions WHERE institution_code = 'schwab'),
 '550e8400-e29b-41d4-a716-446655440401',
 'Schwab Roth IRA', 'investment', 'roth', 'USD'),

-- Sarah Smith's accounts
('550e8400-e29b-41d4-a716-446655440503', '550e8400-e29b-41d4-a716-446655440202',
 (SELECT id FROM provider_institutions WHERE institution_code = 'fidelity'),
 '550e8400-e29b-41d4-a716-446655440402',
 'Fidelity 401k', 'investment', '401k', 'USD'),
('550e8400-e29b-41d4-a716-446655440504', '550e8400-e29b-41d4-a716-446655440202',
 (SELECT id FROM provider_institutions WHERE institution_code = 'fidelity'),
 '550e8400-e29b-41d4-a716-446655440402',
 'Fidelity Taxable', 'investment', 'brokerage', 'USD'),

-- Mike Johnson's account
('550e8400-e29b-41d4-a716-446655440505', '550e8400-e29b-41d4-a716-446655440203',
 (SELECT id FROM provider_institutions WHERE institution_code = 'vanguard'),
 '550e8400-e29b-41d4-a716-446655440403',
 'Vanguard Stocks & Shares ISA', 'investment', 'isa', 'GBP'),

-- Emma Wilson's account
('550e8400-e29b-41d4-a716-446655440506', '550e8400-e29b-41d4-a716-446655440204',
 NULL, NULL,
 'Personal Portfolio', 'investment', 'brokerage', 'USD');

-- =====================================================
-- MARKET DATA - PRICES FOR 6 MONTHS
-- =====================================================

-- Generate daily prices for major securities (March 1 - Sept 17, 2025)
-- This creates a realistic price series with some volatility

-- AAPL prices (starting around $175, trending up to ~$195)
DO
$$
DECLARE
curr_date DATE := '2025-03-01';
    end_date
DATE := '2025-09-17';
    base_price
DECIMAL(15,4) := 175.00;
    price
DECIMAL(15,4);
    daily_return
DECIMAL(8,4);
BEGIN
    WHILE
curr_date <= end_date LOOP
        -- Skip weekends
        IF EXTRACT(DOW FROM curr_date) NOT IN (0, 6) THEN
            -- Generate random daily return between -3% and +3%
            daily_return := (random() - 0.5) * 0.06;
            price
:= base_price * (1 + daily_return);

INSERT INTO security_prices (security_id, price_date, close_price, volume)
VALUES ('550e8400-e29b-41d4-a716-446655440001', curr_date, price,
        (50000000 + random() * 50000000)::BIGINT);

base_price
:= price;
END IF;
        curr_date
:= curr_date + INTERVAL '1 day';
END LOOP;
END $$;

-- MSFT prices (starting around $320, trending up to ~$350)
DO
$$
DECLARE
curr_date DATE := '2025-03-01';
    end_date
DATE := '2025-09-17';
    base_price
DECIMAL(15,4) := 320.00;
    price
DECIMAL(15,4);
    daily_return
DECIMAL(8,4);
BEGIN
    WHILE
curr_date <= end_date LOOP
        IF EXTRACT(DOW FROM curr_date) NOT IN (0, 6) THEN
            daily_return := (random() - 0.5) * 0.05;
            price
:= base_price * (1 + daily_return);

INSERT INTO security_prices (security_id, price_date, close_price, volume)
VALUES ('550e8400-e29b-41d4-a716-446655440002', curr_date, price,
        (25000000 + random() * 25000000)::BIGINT);

base_price
:= price;
END IF;
        curr_date
:= curr_date + INTERVAL '1 day';
END LOOP;
END $$;

-- SPY ETF prices (starting around $450, trending up to ~$480)
DO
$$
DECLARE
curr_date DATE := '2025-03-01';
    end_date
DATE := '2025-09-17';
    base_price
DECIMAL(15,4) := 450.00;
    price
DECIMAL(15,4);
    daily_return
DECIMAL(8,4);
BEGIN
    WHILE
curr_date <= end_date LOOP
        IF EXTRACT(DOW FROM curr_date) NOT IN (0, 6) THEN
            daily_return := (random() - 0.5) * 0.04;
            price
:= base_price * (1 + daily_return);

INSERT INTO security_prices (security_id, price_date, close_price, volume)
VALUES ('550e8400-e29b-41d4-a716-446655440010', curr_date, price,
        (80000000 + random() * 40000000)::BIGINT);

base_price
:= price;
END IF;
        curr_date
:= curr_date + INTERVAL '1 day';
END LOOP;
END $$;

-- Add prices for other major securities with similar patterns
-- VTI, QQQ, NVDA, TSLA, etc. (simplified generation)

INSERT INTO security_prices (security_id, price_date, close_price, volume)
SELECT '550e8400-e29b-41d4-a716-446655440011' as security_id,
       date_series                            as price_date,
       220.00 + (random() - 0.5) * 40         as close_price,
       (15000000 + random() * 10000000) ::BIGINT as volume
FROM generate_series('2025-03-01'::date, '2025-09-17'::date, '1 day'::interval) as date_series
WHERE EXTRACT(DOW FROM date_series) NOT IN (0, 6);

-- Cash always $1
INSERT INTO security_prices (security_id, price_date, close_price, volume)
SELECT '550e8400-e29b-41d4-a716-446655440030' as security_id,
       date_series                            as price_date,
       1.0000                                 as close_price,
       0                                      as volume
FROM generate_series('2025-03-01'::date, '2025-09-17'::date, '1 day'::interval) as date_series
WHERE EXTRACT(DOW FROM date_series) NOT IN (0, 6);

-- =====================================================
-- BENCHMARK PRICES
-- =====================================================

-- SPY benchmark data
INSERT INTO benchmark_prices (benchmark_id, price_date, close_price, total_return_1d, total_return_ytd, total_return_1y)
SELECT '550e8400-e29b-41d4-a716-446655440100'                                                                            as benchmark_id,
       sp.price_date,
       sp.close_price,
       ((sp.close_price / LAG(sp.close_price) OVER (ORDER BY sp.price_date)) - 1) * 100                                  as total_return_1d,
       ((sp.close_price / FIRST_VALUE(sp.close_price) OVER (ORDER BY sp.price_date ROWS UNBOUNDED PRECEDING)) - 1) * 100 as total_return_ytd,
       NULL                                                                                                              as total_return_1y
FROM security_prices sp
WHERE sp.security_id = '550e8400-e29b-41d4-a716-446655440010'
ORDER BY sp.price_date;

-- =====================================================
-- PORTFOLIO TRANSACTIONS
-- =====================================================

-- John Doe's Schwab Brokerage transactions
INSERT INTO portfolio_transactions (id, account_id, security_id, transaction_type, transaction_subtype, quantity, price,
                                    amount, trade_date, description)
VALUES
-- Initial purchases in March
('550e8400-e29b-41d4-a716-446655440701', '550e8400-e29b-41d4-a716-446655440501', '550e8400-e29b-41d4-a716-446655440001',
 'buy', 'buy', 100, 175.25, -17525.00, '2025-03-15', 'AAPL - Buy 100 shares'),
('550e8400-e29b-41d4-a716-446655440702', '550e8400-e29b-41d4-a716-446655440501', '550e8400-e29b-41d4-a716-446655440002',
 'buy', 'buy', 50, 321.50, -16075.00, '2025-03-15', 'MSFT - Buy 50 shares'),
('550e8400-e29b-41d4-a716-446655440703', '550e8400-e29b-41d4-a716-446655440501', '550e8400-e29b-41d4-a716-446655440010',
 'buy', 'buy', 200, 452.75, -90550.00, '2025-03-16', 'SPY - Buy 200 shares'),
('550e8400-e29b-41d4-a716-446655440704', '550e8400-e29b-41d4-a716-446655440501', '550e8400-e29b-41d4-a716-446655440030',
 'cash', 'deposit', 1, 1.00, 50000.00, '2025-03-14', 'Cash deposit'),

-- Additional buys through the months
('550e8400-e29b-41d4-a716-446655440705', '550e8400-e29b-41d4-a716-446655440501', '550e8400-e29b-41d4-a716-446655440001',
 'buy', 'buy', 50, 182.30, -9115.00, '2025-05-20', 'AAPL - Additional purchase'),
('550e8400-e29b-41d4-a716-446655440706', '550e8400-e29b-41d4-a716-446655440501', '550e8400-e29b-41d4-a716-446655440006',
 'buy', 'buy', 25, 450.00, -11250.00, '2025-06-10', 'NVDA - Buy 25 shares'),

-- Some selling activity
('550e8400-e29b-41d4-a716-446655440707', '550e8400-e29b-41d4-a716-446655440501', '550e8400-e29b-41d4-a716-446655440010',
 'sell', 'sell', 50, 465.20, 23260.00, '2025-07-15', 'SPY - Partial sale'),

-- Dividends
('550e8400-e29b-41d4-a716-446655440708', '550e8400-e29b-41d4-a716-446655440501', '550e8400-e29b-41d4-a716-446655440001',
 'dividend', 'dividend', 0, 0, 150.00, '2025-08-15', 'AAPL - Quarterly dividend');

-- Sarah Smith's 401k transactions
INSERT INTO portfolio_transactions (id, account_id, security_id, transaction_type, transaction_subtype, quantity, price,
                                    amount, trade_date, description)
VALUES ('550e8400-e29b-41d4-a716-446655440709', '550e8400-e29b-41d4-a716-446655440503',
        '550e8400-e29b-41d4-a716-446655440011', 'buy', 'buy', 500, 222.00, -111000.00, '2025-03-01',
        'VTI - 401k contribution'),
       ('550e8400-e29b-41d4-a716-446655440710', '550e8400-e29b-41d4-a716-446655440503',
        '550e8400-e29b-41d4-a716-446655440021', 'buy', 'buy', 100, 105.50, -10550.00, '2025-03-01',
        'AGG - Bond allocation'),
       ('550e8400-e29b-41d4-a716-446655440711', '550e8400-e29b-41d4-a716-446655440503',
        '550e8400-e29b-41d4-a716-446655440011', 'buy', 'buy', 100, 225.50, -22550.00, '2025-04-01',
        'VTI - Monthly contribution'),
       ('550e8400-e29b-41d4-a716-446655440712', '550e8400-e29b-41d4-a716-446655440503',
        '550e8400-e29b-41d4-a716-446655440011', 'buy', 'buy', 100, 228.75, -22875.00, '2025-05-01',
        'VTI - Monthly contribution'),
       ('550e8400-e29b-41d4-a716-446655440713', '550e8400-e29b-41d4-a716-446655440503',
        '550e8400-e29b-41d4-a716-446655440011', 'buy', 'buy', 100, 231.20, -23120.00, '2025-06-01',
        'VTI - Monthly contribution');

-- =====================================================
-- PORTFOLIO HOLDINGS (Latest positions)
-- =====================================================

-- John Doe's current holdings (as of 2025-09-17)
INSERT INTO portfolio_holdings (account_id, security_id, quantity, cost_basis, as_of_date)
VALUES ('550e8400-e29b-41d4-a716-446655440501', '550e8400-e29b-41d4-a716-446655440001', 150, 177.50,
        '2025-09-17'), -- 150 AAPL @ avg $177.50
       ('550e8400-e29b-41d4-a716-446655440501', '550e8400-e29b-41d4-a716-446655440002', 50, 321.50,
        '2025-09-17'), -- 50 MSFT @ $321.50
       ('550e8400-e29b-41d4-a716-446655440501', '550e8400-e29b-41d4-a716-446655440010', 150, 454.25,
        '2025-09-17'), -- 150 SPY @ avg $454.25
       ('550e8400-e29b-41d4-a716-446655440501', '550e8400-e29b-41d4-a716-446655440006', 25, 450.00,
        '2025-09-17'), -- 25 NVDA @ $450
       ('550e8400-e29b-41d4-a716-446655440501', '550e8400-e29b-41d4-a716-446655440030', 15000, 1.00, '2025-09-17');
-- $15,000 cash

-- John Doe's Roth IRA holdings
INSERT INTO portfolio_holdings (account_id, security_id, quantity, cost_basis, as_of_date)
VALUES ('550e8400-e29b-41d4-a716-446655440502', '550e8400-e29b-41d4-a716-446655440011', 200, 220.00,
        '2025-09-17'), -- 200 VTI @ $220
       ('550e8400-e29b-41d4-a716-446655440502', '550e8400-e29b-41d4-a716-446655440030', 5000, 1.00, '2025-09-17');
-- $5,000 cash

-- Sarah Smith's 401k holdings
INSERT INTO portfolio_holdings (account_id, security_id, quantity, cost_basis, as_of_date)
VALUES ('550e8400-e29b-41d4-a716-446655440503', '550e8400-e29b-41d4-a716-446655440011', 800, 225.50,
        '2025-09-17'), -- 800 VTI @ avg $225.50
       ('550e8400-e29b-41d4-a716-446655440503', '550e8400-e29b-41d4-a716-446655440021', 100, 105.50,
        '2025-09-17'), -- 100 AGG @ $105.50
       ('550e8400-e29b-41d4-a716-446655440503', '550e8400-e29b-41d4-a716-446655440030', 2500, 1.00, '2025-09-17');
-- $2,500 cash

-- Sarah Smith's taxable account
INSERT INTO portfolio_holdings (account_id, security_id, quantity, cost_basis, as_of_date)
VALUES ('550e8400-e29b-41d4-a716-446655440504', '550e8400-e29b-41d4-a716-446655440003', 75, 125.00,
        '2025-09-17'), -- 75 GOOGL @ $125
       ('550e8400-e29b-41d4-a716-446655440504', '550e8400-e29b-41d4-a716-446655440012', 100, 385.50,
        '2025-09-17'), -- 100 QQQ @ $385.50
       ('550e8400-e29b-41d4-a716-446655440504', '550e8400-e29b-41d4-a716-446655440030', 8000, 1.00, '2025-09-17');
-- $8,000 cash

-- Mike Johnson's ISA holdings (UK)
INSERT INTO portfolio_holdings (account_id, security_id, quantity, cost_basis, as_of_date)
VALUES ('550e8400-e29b-41d4-a716-446655440505', '550e8400-e29b-41d4-a716-446655440014', 500, 75.50,
        '2025-09-17'), -- 500 EFA @ £75.50
       ('550e8400-e29b-41d4-a716-446655440505', '550e8400-e29b-41d4-a716-446655440031', 5000, 1.00, '2025-09-17');
-- £5,000 cash

-- =====================================================
-- ANALYTICS SUMMARY DATA (Weekly snapshots)
-- =====================================================

-- Generate weekly analytics summary for John Doe's brokerage account
DO
$$
DECLARE
summary_date DATE;
    market_val
DECIMAL(15,2);
    cost_val
DECIMAL(15,2);
    week_return
DECIMAL(10,4);
BEGIN
FOR summary_date IN
SELECT date_trunc('week', generate_series('2025-03-15'::date, '2025-09-17'::date, '1 week'::interval)) ::date
    LOOP
        -- Calculate approximate market value and returns with some realistic variation
        market_val := 200000 + (random() - 0.5) * 50000 + (summary_date - '2025-03-15'::date) * 100;
cost_val
:= market_val * (0.85 + random() * 0.1); -- Cost basis typically lower
        week_return
:= (random() - 0.5) * 0.06; -- Weekly return between -3% and +3%

INSERT INTO analytics_summary (account_id, as_of_date, market_value, cost_basis, cash_balance,
                               unrealized_gain, weekly_return, monthly_return, ytd_return,
                               equity_value, fund_value, cash_value, domestic_value,
                               currency, holdings_count)
VALUES ('550e8400-e29b-41d4-a716-446655440501',
        summary_date,
        market_val,
        cost_val,
        15000.00,
        market_val - cost_val,
        week_return,
        (random() - 0.5) * 0.15, -- Monthly return
        ((market_val / 175000.00) - 1) * 100, -- YTD return from base
        market_val * 0.65, -- 65% equity
        market_val * 0.25, -- 25% funds
        15000.00, -- 10% cash
        market_val * 0.95, -- 95% domestic
        'USD',
        5);
END LOOP;
END $$;

-- Generate analytics for other accounts (abbreviated - extend as needed)
INSERT INTO analytics_summary (account_id, as_of_date, market_value, cost_basis, cash_balance,
                               unrealized_gain, weekly_return, ytd_return,
                               equity_value, fund_value, cash_value, domestic_value,
                               currency, holdings_count)
VALUES
-- Sarah's 401k recent summary
('550e8400-e29b-41d4-a716-446655440503', '2025-09-17', 185000.00, 170000.00, 2500.00,
 15000.00, 0.0125, 0.0883, 170000.00, 12500.00, 2500.00, 185000.00, 'USD', 3),

-- Mike's ISA summary
('550e8400-e29b-41d4-a716-446655440505', '2025-09-17', 42750.00, 40000.00, 5000.00,
 2750.00, 0.0095, 0.0687, 0.00, 37750.00, 5000.00, 20000.00, 'GBP', 2);

-- =====================================================
-- PERFORMANCE ANALYTICS
-- =====================================================

INSERT INTO analytics_performance (account_id, as_of_date, benchmark_symbol, alpha, beta, correlation,
                                   volatility, sharpe_ratio, max_drawdown, current_drawdown,
                                   best_day_return, worst_day_return, win_rate)
VALUES
-- John Doe's performance vs SPY
('550e8400-e29b-41d4-a716-446655440501', '2025-09-17', 'SPY', 0.0125, 1.15, 0.85,
 0.1850, 0.65, -0.0875, -0.0125, 0.0345, -0.0298, 55.2),

-- Sarah's 401k performance
('550e8400-e29b-41d4-a716-446655440503', '2025-09-17', 'VTI', 0.0085, 0.98, 0.92,
 0.1650, 0.58, -0.0625, -0.0075, 0.0285, -0.0245, 58.7);

-- =====================================================
-- RISK ANALYTICS
-- =====================================================

INSERT INTO analytics_risk (account_id, as_of_date, var_95_1d, var_99_1d, cvar_95_1d, cvar_99_1d,
                            volatility, concentration_hhi, largest_position_pct, top_5_concentration)
VALUES
-- John Doe's risk metrics
('550e8400-e29b-41d4-a716-446655440501', '2025-09-17', -0.0185, -0.0275, -0.0235, -0.0345,
 0.1850, 0.2500, 25.5, 85.2),

-- Sarah's 401k risk metrics (lower risk due to diversification)
('550e8400-e29b-41d4-a716-446655440503', '2025-09-17', -0.0165, -0.0245, -0.0198, -0.0298,
 0.1650, 0.6500, 85.5, 98.5);

-- =====================================================
-- EXPOSURE ANALYTICS
-- =====================================================

INSERT INTO analytics_exposure (account_id, as_of_date,
                                allocation_by_security_type, allocation_by_security_subtype, allocation_by_sector,
                                allocation_by_industry, allocation_by_country, allocation_by_region,
                                allocation_by_currency, top_holdings, top_5_weight, top_10_weight,
                                largest_position_weight)
VALUES
-- John Doe's exposure breakdown
('550e8400-e29b-41d4-a716-446655440501', '2025-09-17',
 '{"equity": 65.5, "fund": 25.0, "cash": 9.5}'::jsonb,
 '{"common_stock": 65.5, "etf": 25.0, "cash": 9.5}'::jsonb,
 '{"technology": 45.2, "financial": 15.8, "diversified": 25.0, "cash": 9.5}'::jsonb,
 '{"consumer_electronics": 25.5, "software": 17.5, "semiconductors": 2.2, "index_fund": 25.0, "cash": 9.5, "other": 20.3}'::jsonb,
 '{"US": 95.0, "cash": 5.0}'::jsonb,
 '{"north_america": 95.0, "cash": 5.0}'::jsonb,
 '{"USD": 100.0}'::jsonb,
 '[{"symbol": "AAPL", "weight": 25.5, "value": 29250}, {"symbol": "SPY", "weight": 25.0, "value": 68138}, {"symbol": "MSFT", "weight": 17.5, "value": 17075}]'::jsonb,
 85.2, 85.2, 25.5),

-- Sarah's 401k exposure (more diversified)
('550e8400-e29b-41d4-a716-446655440503', '2025-09-17',
 '{"fund": 97.5, "cash": 2.5}'::jsonb,
 '{"etf": 97.5, "cash": 2.5}'::jsonb,
 '{"diversified": 85.5, "fixed_income": 12.0, "cash": 2.5}'::jsonb,
 '{"index_fund": 85.5, "corporate_bonds": 12.0, "cash": 2.5}'::jsonb,
 '{"US": 97.5, "cash": 2.5}'::jsonb,
 '{"north_america": 97.5, "cash": 2.5}'::jsonb,
 '{"USD": 100.0}'::jsonb,
 '[{"symbol": "VTI", "weight": 85.5, "value": 180400}, {"symbol": "AGG", "weight": 12.0, "value": 10550}]'::jsonb,
 97.5, 97.5, 85.5);

-- =====================================================
-- MARKET RATES (FX and Interest Rates)
-- =====================================================

-- Daily USD/EUR, USD/GBP rates for 6 months
INSERT INTO market_rates (rate_type, from_currency, to_currency, rate, rate_date)
SELECT 'fx',
       'USD',
       'EUR',
       0.85 + (random() - 0.5) * 0.1, -- EUR/USD around 0.85 with variation
       date_series
FROM generate_series('2025-03-01'::date, '2025-09-17'::date, '1 day'::interval) as date_series
WHERE EXTRACT(DOW FROM date_series) NOT IN (0, 6);

INSERT INTO market_rates (rate_type, from_currency, to_currency, rate, rate_date)
SELECT 'fx',
       'USD',
       'GBP',
       0.78 + (random() - 0.5) * 0.08, -- GBP/USD around 0.78 with variation
       date_series
FROM generate_series('2025-03-01'::date, '2025-09-17'::date, '1 day'::interval) as date_series
WHERE EXTRACT(DOW FROM date_series) NOT IN (0, 6);

-- Risk-free rates (10-year Treasury)
INSERT INTO market_rates (rate_type, from_currency, to_currency, rate, rate_date)
SELECT 'risk_free',
       'USD',
       'USD',
       0.045 + (random() - 0.5) * 0.008, -- 10Y Treasury around 4.5%
       date_series
FROM generate_series('2025-03-01'::date, '2025-09-17'::date, '1 week'::interval) as date_series;

-- =====================================================
-- CORPORATE ACTIONS & DIVIDENDS
-- =====================================================

-- Quarterly dividends for major holdings
INSERT INTO corporate_dividends (security_id, ex_date, pay_date, amount_per_share, frequency)
VALUES ('550e8400-e29b-41d4-a716-446655440001', '2025-05-15', '2025-05-22', 0.24, 'quarterly'), -- AAPL Q2
       ('550e8400-e29b-41d4-a716-446655440001', '2025-08-15', '2025-08-22', 0.25, 'quarterly'), -- AAPL Q3
       ('550e8400-e29b-41d4-a716-446655440002', '2025-05-20', '2025-05-28', 0.68, 'quarterly'), -- MSFT Q2
       ('550e8400-e29b-41d4-a716-446655440002', '2025-08-20', '2025-08-28', 0.72, 'quarterly'), -- MSFT Q3
       ('550e8400-e29b-41d4-a716-446655440007', '2025-04-10', '2025-04-18', 1.05, 'quarterly'), -- JPM Q1
       ('550e8400-e29b-41d4-a716-446655440007', '2025-07-10', '2025-07-18', 1.15, 'quarterly');
-- JPM Q2

-- Stock split for NVDA
INSERT INTO corporate_actions (security_id, action_type, ex_date, effective_date, details)
VALUES ('550e8400-e29b-41d4-a716-446655440006', 'split', '2025-06-07', '2025-06-08',
        '{"ratio": "10:1", "description": "10-for-1 stock split"}'::jsonb);

-- =====================================================
-- SYSTEM OPERATIONS DATA
-- =====================================================

-- Recent system jobs
INSERT INTO system_jobs (user_id, job_type, job_name, status, total_records, processed_records, started_at,
                         completed_at)
VALUES ('550e8400-e29b-41d4-a716-446655440201', 'data_import', 'Schwab Account Sync', 'completed', 500, 500,
        '2025-09-17 06:00:00', '2025-09-17 06:05:00'),
       ('550e8400-e29b-41d4-a716-446655440202', 'analytics_calc', 'Portfolio Analytics Update', 'completed', 1200, 1200,
        '2025-09-17 05:30:00', '2025-09-17 05:45:00'),
       ('550e8400-e29b-41d4-a716-446655440203', 'data_import', 'Manual Portfolio Update', 'completed', 50, 50,
        '2025-09-16 18:30:00', '2025-09-16 18:32:00');

-- Sample system logs
INSERT INTO system_logs (log_level, message, context, user_id, source)
VALUES ('info', 'User login successful', '{"ip": "192.168.1.1", "browser": "Chrome"}',
        '550e8400-e29b-41d4-a716-446655440201', 'auth_service'),
       ('info', 'Portfolio analytics calculated', '{"account_count": 2, "duration_ms": 1250}',
        '550e8400-e29b-41d4-a716-446655440201', 'analytics_engine'),
       ('warn', 'Price data delayed for TSLA', '{"symbol": "TSLA", "delay_minutes": 15}', NULL, 'price_service'),
       ('info', 'Daily backup completed', '{"backup_size_gb": 2.5, "duration_minutes": 12}', NULL, 'backup_service');

-- =====================================================
-- NOTIFICATIONS
-- =====================================================

INSERT INTO user_notifications (user_id, notification_type, title, message, is_read)
VALUES ('550e8400-e29b-41d4-a716-446655440201', 'alert', 'Portfolio Performance Update',
        'Your portfolio gained 2.3% this week, outperforming the S&P 500.', false),
       ('550e8400-e29b-41d4-a716-446655440201', 'system', 'Account Sync Complete',
        'Successfully synced your Schwab brokerage account with 5 new transactions.', true),
       ('550e8400-e29b-41d4-a716-446655440202', 'alert', 'Rebalancing Opportunity',
        'Your asset allocation has drifted. Consider rebalancing your 401k.', false),
       ('550e8400-e29b-41d4-a716-446655440203', 'import', 'Manual Update Processed',
        'Your ISA portfolio has been updated with latest holdings.', true);

COMMIT;

-- =====================================================
-- VERIFICATION QUERIES
-- =====================================================

-- Verify data was inserted correctly
SELECT 'Users created: ' || COUNT(*)
FROM user_accounts;
SELECT 'Securities created: ' || COUNT(*)
FROM security_master;
SELECT 'Accounts created: ' || COUNT(*)
FROM portfolio_accounts;
SELECT 'Price records: ' || COUNT(*)
FROM security_prices;
SELECT 'Transactions: ' || COUNT(*)
FROM portfolio_transactions;
SELECT 'Holdings: ' || COUNT(*)
FROM portfolio_holdings;
SELECT 'Analytics summaries: ' || COUNT(*)
FROM analytics_summary;

-- Sample portfolio overview query
SELECT ua.full_name,
       pa.name                                                  as account_name,
       SUM(ph.quantity * sp.close_price)                        as current_value,
       STRING_AGG(sm.symbol || ': ' || ph.quantity::text, ', ') as holdings
FROM user_accounts ua
         JOIN portfolio_accounts pa ON ua.id = pa.user_id
         JOIN portfolio_holdings ph ON pa.id = ph.account_id
         JOIN security_master sm ON ph.security_id = sm.id
         LEFT JOIN security_prices sp ON sm.id = sp.security_id
    AND sp.price_date = '2025-09-17'
WHERE ph.as_of_date = '2025-09-17'
GROUP BY ua.full_name, pa.name, pa.id
ORDER BY ua.full_name, pa.name;
