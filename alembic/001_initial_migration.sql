-- =====================================================
-- ZSPRD Portfolio Analytics Database - MVP Schema
-- =====================================================
-- Professional portfolio analytics platform for HNWIs
-- Scalable architecture supporting multiple data providers
-- Core analytics: performance, risk, exposure analysis
-- =====================================================

BEGIN;

-- =====================================================
-- EXTENSIONS & FUNCTIONS
-- =====================================================

-- Enable UUID generation for primary keys
CREATE
EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable cryptographic functions for sensitive data
CREATE
EXTENSION IF NOT EXISTS "pgcrypto";

-- =====================================================
-- ENUMS - Standardized data classifications
-- =====================================================

-- Subscription plan types
CREATE TYPE plan_type_enum AS ENUM (
    'free',           -- Basic portfolio tracking
    'premium',        -- Advanced analytics & reporting
    'professional',   -- Institution-grade features
    'enterprise'      -- White-label & API access
);

-- Account classification (primary categorization)
CREATE TYPE account_type_enum AS ENUM (
    'investment',     -- Brokerage, 401k, IRA accounts
    'depository',     -- Checking, savings, money market
    'credit',         -- Credit cards, lines of credit
    'loan',           -- Mortgages, student loans
    'other'           -- Catch-all for other account types
);

-- Account subtypes (detailed categorization)
CREATE TYPE account_subtype_enum AS ENUM (
    'brokerage', 'ira', 'roth', '401k', 'isa',
    'checking', 'savings', 'money market', 'cd',
    'credit card', 'mortgage', 'student', 'personal',
    'cash management', 'crypto', 'paypal', 'loan',
    'auto', 'business', 'commercial', 'line of credit',
    'other'
);

-- Security types (broad asset categories)
CREATE TYPE security_type_enum AS ENUM (
    'equity',         -- Stocks
    'fund',           -- Mutual funds, ETFs
    'debt',           -- Bonds, bills, notes
    'option',         -- Options, warrants
    'future',         -- Futures contracts
    'forward',        -- Forward contracts
    'swap',           -- Swaps, CFDs
    'cash',           -- Cash equivalents
    'digital',        -- Digital assets/crypto
    'other'           -- Commodities, REITs, alternatives
);

-- Security subtypes (specific classifications)
CREATE TYPE security_subtype_enum AS ENUM (
    'common stock', 'preferred stock', 'etf', 'mutual fund',
    'index fund', 'bond', 'bill', 'note', 'option', 'warrant',
    'cash', 'cryptocurrency', 'reit', 'commodity'
);

-- Transaction types (investment actions)
CREATE TYPE transaction_type_enum AS ENUM (
    'buy', 'sell', 'cash', 'transfer', 'fee',
    'dividend', 'interest', 'cancel', 'adjustment',
    'split', 'merger', 'spinoff'
);

-- Transaction subtypes (specific actions)
CREATE TYPE transaction_subtype_enum AS ENUM (
    'buy', 'sell', 'deposit', 'withdrawal',
    'dividend', 'interest', 'fee',
    'transfer in', 'transfer out', 'cancel', 'adjustment',
    'stock split', 'merger', 'spinoff'
);

-- Data source tracking (origin of data)
CREATE TYPE data_source_enum AS ENUM (
    'plaid',          -- Plaid API integration
    'yfinance',       -- Yahoo Finance API
    'alphavantage',   -- Alpha Vantage API
    'manual',         -- User manual entry
    'csv',            -- CSV/Excel upload
    'calculated'      -- System computed values
);

-- =====================================================
-- USER MANAGEMENT
-- Identity, authentication, billing
-- =====================================================

-- Core user accounts and authentication
CREATE TABLE user_accounts
(
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email         VARCHAR(320) UNIQUE NOT NULL,
    password_hash VARCHAR(255),                   -- bcrypt hash
    full_name     VARCHAR(255),
    timezone      VARCHAR(50)      DEFAULT 'UTC',
    base_currency CHAR(3)          DEFAULT 'USD', -- User's reporting currency
    is_active     BOOLEAN          DEFAULT true,
    is_verified   BOOLEAN          DEFAULT false, -- Email verification status
    last_login_at TIMESTAMPTZ,
    created_at    TIMESTAMPTZ      DEFAULT NOW(),
    updated_at    TIMESTAMPTZ      DEFAULT NOW()
);

-- User session management for authentication
CREATE TABLE user_sessions
(
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id       UUID                NOT NULL REFERENCES user_accounts (id) ON DELETE CASCADE,
    refresh_token VARCHAR(500) UNIQUE NOT NULL,
    expires_at    TIMESTAMPTZ         NOT NULL,
    created_at    TIMESTAMPTZ      DEFAULT NOW(),
    last_used_at  TIMESTAMPTZ      DEFAULT NOW(),
    ip_address    INET,
    user_agent    VARCHAR(500)
);

-- Subscription management and billing
CREATE TABLE user_subscriptions
(
    id                     UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id                UUID           NOT NULL REFERENCES user_accounts (id) ON DELETE CASCADE,
    plan_name              plan_type_enum NOT NULL,
    status                 VARCHAR(20)    NOT NULL, -- 'active', 'cancelled', 'past_due'
    current_period_start   DATE           NOT NULL,
    current_period_end     DATE           NOT NULL,
    cancelled_at           DATE,
    stripe_subscription_id VARCHAR(255) UNIQUE,     -- Stripe integration
    stripe_customer_id     VARCHAR(255),
    amount                 DECIMAL(10, 2),
    currency               CHAR(3)          DEFAULT 'USD',
    created_at             TIMESTAMPTZ      DEFAULT NOW(),
    updated_at             TIMESTAMPTZ      DEFAULT NOW()
);

-- System notifications and alerts
CREATE TABLE user_notifications
(
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id           UUID         NOT NULL REFERENCES user_accounts (id) ON DELETE CASCADE,
    notification_type VARCHAR(50)  NOT NULL, -- 'alert', 'system', 'import'
    title             VARCHAR(255) NOT NULL,
    message           TEXT         NOT NULL,
    is_read           BOOLEAN          DEFAULT false,
    read_at           TIMESTAMPTZ,
    created_at        TIMESTAMPTZ      DEFAULT NOW()
);

-- =====================================================
-- PROVIDER INTEGRATIONS
-- External data source management (provider-agnostic)
-- =====================================================

-- Financial institutions and data providers
CREATE TABLE provider_institutions
(
    id                   UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    institution_code VARCHAR(50) UNIQUE NOT NULL, -- 'chase', 'schwab', 'yfinance'
    name             VARCHAR(255)       NOT NULL, -- 'JPMorgan Chase Bank'
    institution_type VARCHAR(50)        NOT NULL, -- 'bank', 'broker', 'data_provider'
    country          CHAR(2)     DEFAULT 'US',
    logo_url             TEXT,
    is_active        BOOLEAN     DEFAULT true,
    created_at       TIMESTAMPTZ DEFAULT NOW(),
    updated_at       TIMESTAMPTZ DEFAULT NOW()
);

-- Data source connections (API, file uploads, manual)
CREATE TABLE provider_connections
(
    id                 UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID         NOT NULL REFERENCES user_accounts (id) ON DELETE CASCADE,
    institution_id  UUID         REFERENCES provider_institutions (id) ON DELETE SET NULL,
    connection_name VARCHAR(255) NOT NULL,        -- User-friendly name
    provider_name   VARCHAR(50)  NOT NULL,        -- 'plaid', 'csv', 'yfinance'
    data_source        data_source_enum NOT NULL,
    access_token    TEXT,                         -- Encrypted access tokens
    status          VARCHAR(50) DEFAULT 'active', -- 'active', 'error', 'disconnected'
    error_message      TEXT,
    last_sync_at       TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- External ID mapping (provider-agnostic identifier mapping)
CREATE TABLE provider_mappings
(
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    connection_id UUID         NOT NULL REFERENCES provider_connections (id) ON DELETE CASCADE,
    entity_type   VARCHAR(50)  NOT NULL, -- 'account', 'security', 'transaction'
    internal_id   UUID         NOT NULL, -- Our internal ID
    external_id   VARCHAR(255) NOT NULL, -- Provider's ID
    created_at    TIMESTAMPTZ      DEFAULT NOW(),

    UNIQUE (connection_id, entity_type, external_id)
);

-- =====================================================
-- SECURITY MASTER
-- Security reference data and market prices
-- =====================================================

-- Master security reference (stocks, bonds, funds, etc.)
CREATE TABLE security_master
(
    id                 UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol             VARCHAR(50),                    -- Trading symbol (AAPL, MSFT)
    name               VARCHAR(500)       NOT NULL,    -- Full security name
    security_type      security_type_enum NOT NULL,
    security_subtype   security_subtype_enum,
    currency           CHAR(3)          DEFAULT 'USD', -- Trading currency
    exchange           VARCHAR(20),                    -- Primary exchange (NYSE, NASDAQ)
    country            CHAR(2),                        -- Country of incorporation
    sector             VARCHAR(100),                   -- GICS sector
    industry           VARCHAR(100),                   -- GICS industry
    is_cash_equivalent BOOLEAN          DEFAULT false,
    option_details     JSONB,                          -- {strike, expiry, type, underlying}
    bond_details       JSONB,                          -- {maturity, coupon, rating, issuer}
    data_source        data_source_enum DEFAULT 'manual',
    created_at         TIMESTAMPTZ      DEFAULT NOW(),
    updated_at         TIMESTAMPTZ      DEFAULT NOW()
);

-- Daily market prices and volume data
CREATE TABLE security_prices
(
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    security_id UUID           NOT NULL REFERENCES security_master (id) ON DELETE CASCADE,
    price_date  DATE           NOT NULL,
    close_price DECIMAL(15, 4) NOT NULL, -- Closing price
    volume      BIGINT,                  -- Trading volume
    data_source data_source_enum DEFAULT 'calculated',
    created_at  TIMESTAMPTZ      DEFAULT NOW(),

    UNIQUE (security_id, price_date)
);

-- Multiple security identifiers (CUSIP, ISIN, provider IDs)
CREATE TABLE security_identifiers
(
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    security_id      UUID        NOT NULL REFERENCES security_master (id) ON DELETE CASCADE,
    identifier_type  VARCHAR(20) NOT NULL,           -- 'cusip', 'isin', 'plaid_id', 'symbol'
    identifier_value VARCHAR(50) NOT NULL,
    is_primary       BOOLEAN          DEFAULT false, -- Primary identifier for this type
    created_at       TIMESTAMPTZ      DEFAULT NOW(),

    UNIQUE (identifier_type, identifier_value)
);

-- =====================================================
-- PORTFOLIO DATA
-- User investment accounts, holdings, transactions
-- =====================================================

-- Investment accounts (brokerage, 401k, IRA, etc.)
CREATE TABLE portfolio_accounts
(
    id                 UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id        UUID         NOT NULL REFERENCES user_accounts (id) ON DELETE CASCADE,
    institution_id UUID         REFERENCES provider_institutions (id) ON DELETE SET NULL,
    connection_id  UUID         REFERENCES provider_connections (id) ON DELETE SET NULL,
    name           VARCHAR(255) NOT NULL,     -- Account name/nickname
    account_type       account_type_enum NOT NULL,
    account_subtype    account_subtype_enum,
    currency       CHAR(3)     DEFAULT 'USD', -- Base currency of account
    is_active      BOOLEAN     DEFAULT true,
    data_source        data_source_enum DEFAULT 'manual',
    created_at     TIMESTAMPTZ DEFAULT NOW(),
    updated_at     TIMESTAMPTZ DEFAULT NOW()
);

-- Portfolio positions/holdings (point-in-time snapshots)
CREATE TABLE portfolio_holdings
(
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id  UUID           NOT NULL REFERENCES portfolio_accounts (id) ON DELETE CASCADE,
    security_id UUID           NOT NULL REFERENCES security_master (id) ON DELETE CASCADE,
    quantity    DECIMAL(15, 6) NOT NULL, -- Can be negative for shorts
    cost_basis  DECIMAL(15, 4),          -- Average cost per share
    currency    CHAR(3)     DEFAULT 'USD',
    as_of_date  DATE           NOT NULL, -- Snapshot date
    data_source       data_source_enum DEFAULT 'manual',
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE (account_id, security_id, as_of_date)
);

-- Transaction history (buys, sells, dividends, etc.)
CREATE TABLE portfolio_transactions
(
    id                    UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id      UUID           NOT NULL REFERENCES portfolio_accounts (id) ON DELETE CASCADE,
    security_id     UUID           REFERENCES security_master (id) ON DELETE SET NULL,
    transaction_type      transaction_type_enum NOT NULL,
    transaction_subtype   transaction_subtype_enum,
    quantity        DECIMAL(15, 6),           -- Shares/units (positive for buys)
    price           DECIMAL(15, 4),           -- Price per share
    amount          DECIMAL(15, 2) NOT NULL,  -- Total transaction amount
    fees            DECIMAL(15, 2) DEFAULT 0, -- Transaction fees
    currency        CHAR(3)        DEFAULT 'USD',
    trade_date      DATE           NOT NULL,  -- Trade execution date
    settlement_date DATE,                     -- Settlement date
    description     TEXT,                     -- Transaction description
    data_source           data_source_enum DEFAULT 'manual',
    created_at      TIMESTAMPTZ    DEFAULT NOW(),
    updated_at      TIMESTAMPTZ    DEFAULT NOW()
);

-- =====================================================
-- CORPORATE ACTIONS
-- Stock splits, dividends, mergers affecting holdings
-- =====================================================

-- Corporate actions affecting securities
CREATE TABLE corporate_actions
(
    id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    security_id    UUID        NOT NULL REFERENCES security_master (id) ON DELETE CASCADE,
    action_type    VARCHAR(30) NOT NULL, -- 'split', 'dividend', 'merger', 'spinoff'
    ex_date        DATE        NOT NULL, -- Ex-dividend/action date
    effective_date DATE        NOT NULL, -- When action takes effect
    details        JSONB       NOT NULL, -- Action-specific details
    created_at     TIMESTAMPTZ      DEFAULT NOW()
);

-- Dividend payment tracking
CREATE TABLE corporate_dividends
(
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    security_id      UUID           NOT NULL REFERENCES security_master (id) ON DELETE CASCADE,
    ex_date          DATE           NOT NULL,
    pay_date         DATE           NOT NULL,
    amount_per_share DECIMAL(15, 6) NOT NULL,
    currency         CHAR(3)          DEFAULT 'USD',
    frequency        VARCHAR(20),                        -- 'quarterly', 'annual', 'monthly'
    dividend_type    VARCHAR(20)      DEFAULT 'regular', -- 'regular', 'special', 'liquidating'
    created_at       TIMESTAMPTZ      DEFAULT NOW()
);

-- =====================================================
-- ANALYTICS CORE
-- Performance metrics, risk analysis, exposure data
-- =====================================================

-- Account-level summary metrics (additive for portfolio totals)
CREATE TABLE analytics_summary
(
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id          UUID           NOT NULL REFERENCES portfolio_accounts (id) ON DELETE CASCADE,
    as_of_date          DATE           NOT NULL,

    -- Core portfolio values
    market_value        DECIMAL(15, 2) NOT NULL,  -- Current market value
    cost_basis          DECIMAL(15, 2) NOT NULL,  -- Total cost basis
    cash_balance        DECIMAL(15, 2) DEFAULT 0, -- Cash holdings
    unrealized_gain     DECIMAL(15, 2) NOT NULL,  -- Unrealized P&L
    realized_gain       DECIMAL(15, 2) DEFAULT 0, -- Realized P&L (YTD)

    -- Performance returns
    total_return        DECIMAL(10, 4),           -- Total return %
    daily_return        DECIMAL(10, 6),           -- 1-day return %
    weekly_return       DECIMAL(10, 4),           -- 1-week return %
    monthly_return      DECIMAL(10, 4),           -- 1-month return %
    quarterly_return    DECIMAL(10, 4),           -- 1-quarter return %
    ytd_return          DECIMAL(10, 4),           -- Year-to-date return %
    annual_return       DECIMAL(10, 4),           -- 1-year return %

    -- Asset allocation (for aggregation)
    equity_value        DECIMAL(15, 2) DEFAULT 0, -- Stock holdings value
    debt_value          DECIMAL(15, 2) DEFAULT 0, -- Bond holdings value
    fund_value          DECIMAL(15, 2) DEFAULT 0, -- Fund holdings value
    cash_value          DECIMAL(15, 2) DEFAULT 0, -- Cash & equivalents
    other_value         DECIMAL(15, 2) DEFAULT 0, -- Alternative investments

    -- Geographic allocation
    domestic_value      DECIMAL(15, 2) DEFAULT 0, -- Home country allocation
    international_value DECIMAL(15, 2) DEFAULT 0, -- International allocation

    -- Portfolio metadata
    currency            CHAR(3)        NOT NULL,
    holdings_count      INTEGER        DEFAULT 0, -- Number of positions
    last_price_date     DATE,                     -- Latest price update

    -- Time series data for charting
    value_time_series   JSONB,                    -- 30-day value history
    return_time_series  JSONB,                    -- 30-day return history

    created_at          TIMESTAMPTZ    DEFAULT NOW(),
    updated_at          TIMESTAMPTZ    DEFAULT NOW(),

    UNIQUE (account_id, as_of_date)
);

-- Performance analysis and benchmarking
CREATE TABLE analytics_performance
(
    id                 UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id        UUID          NOT NULL REFERENCES portfolio_accounts (id) ON DELETE CASCADE,
    as_of_date        DATE          NOT NULL,

    -- Benchmark comparison
    benchmark_symbol  VARCHAR(10)   NOT NULL, -- 'SPY', 'VTI', 'MSCI_WORLD'
    alpha             DECIMAL(8, 4),          -- Alpha vs benchmark
    beta              DECIMAL(8, 4),          -- Beta vs benchmark
    correlation       DECIMAL(6, 4),          -- Correlation coefficient
    tracking_error    DECIMAL(8, 4),          -- Standard deviation of alpha

    -- Risk-adjusted performance
    volatility        DECIMAL(10, 4),         -- Annualized volatility
    sharpe_ratio      DECIMAL(8, 4),          -- Risk-adjusted return
    sortino_ratio     DECIMAL(8, 4),          -- Downside risk-adjusted
    information_ratio DECIMAL(8, 4),          -- Alpha per unit tracking error
    calmar_ratio      DECIMAL(8, 4),          -- Return/max drawdown

    -- Drawdown analysis
    max_drawdown      DECIMAL(8, 4) NOT NULL, -- Maximum drawdown %
    current_drawdown  DECIMAL(8, 4) NOT NULL, -- Current drawdown %
    recovery_days     INTEGER,                -- Days to recover from max DD

    -- Performance distribution
    best_day_return   DECIMAL(8, 4),          -- Best single day return
    worst_day_return  DECIMAL(8, 4),          -- Worst single day return
    positive_days     INTEGER,                -- Number of positive return days
    negative_days     INTEGER,                -- Number of negative return days
    win_rate          DECIMAL(5, 2),          -- Percentage of positive days

    -- Time series performance data
    daily_returns     JSONB,                  -- 252-day daily returns
    benchmark_returns JSONB,                  -- Benchmark comparison data
    rolling_returns   JSONB,                  -- Rolling period returns

    created_at        TIMESTAMPTZ DEFAULT NOW(),
    updated_at        TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE (account_id, as_of_date)
);

-- Portfolio risk metrics and analysis
CREATE TABLE analytics_risk
(
    id                   UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id           UUID           NOT NULL REFERENCES portfolio_accounts (id) ON DELETE CASCADE,
    as_of_date           DATE           NOT NULL,

    -- Value at Risk metrics
    var_95_1d            DECIMAL(8, 4)  NOT NULL, -- 1-day VaR at 95% confidence
    var_99_1d            DECIMAL(8, 4)  NOT NULL, -- 1-day VaR at 99% confidence
    cvar_95_1d           DECIMAL(8, 4)  NOT NULL, -- Conditional VaR (Expected Shortfall)
    cvar_99_1d           DECIMAL(8, 4)  NOT NULL,

    -- Risk ratios and measures
    volatility           DECIMAL(10, 4) NOT NULL, -- Annualized volatility
    downside_deviation   DECIMAL(8, 4),           -- Downside volatility
    skewness             DECIMAL(8, 4),           -- Return distribution skewness
    kurtosis             DECIMAL(8, 4),           -- Return distribution kurtosis

    -- Concentration risk
    concentration_hhi    DECIMAL(6, 4),           -- Herfindahl-Hirschman Index
    effective_positions  DECIMAL(8, 2),           -- Number of effective positions
    largest_position_pct DECIMAL(5, 2),           -- Largest single position %
    top_5_concentration  DECIMAL(5, 2),           -- Top 5 holdings concentration %
    top_10_concentration DECIMAL(5, 2),           -- Top 10 holdings concentration %

    -- Tail risk measures
    tail_ratio           DECIMAL(8, 4),           -- Right tail / left tail ratio
    gain_loss_ratio      DECIMAL(8, 4),           -- Average gain / average loss

    -- Risk time series
    rolling_volatility   JSONB,                   -- 30-day rolling volatility
    rolling_var          JSONB,                   -- 30-day rolling VaR

    created_at           TIMESTAMPTZ      DEFAULT NOW(),
    updated_at           TIMESTAMPTZ      DEFAULT NOW(),

    UNIQUE (account_id, as_of_date)
);

-- Asset allocation and exposure analysis
CREATE TABLE analytics_exposure
(
    id                             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id                     UUID          NOT NULL REFERENCES portfolio_accounts (id) ON DELETE CASCADE,
    as_of_date                     DATE          NOT NULL,

    -- Asset type allocation
    allocation_by_security_type    JSONB         NOT NULL, -- {"equity": 70.5, "debt": 25.0, "cash": 4.5}
    allocation_by_security_subtype JSONB         NOT NULL, -- {"etf": 35.0, "common_stock": 35.5}

    -- Sector and industry exposure
    allocation_by_sector           JSONB         NOT NULL, -- {"technology": 25.3, "healthcare": 18.2}
    allocation_by_industry         JSONB         NOT NULL, -- {"software": 12.1, "semiconductors": 8.7}

    -- Geographic exposure
    allocation_by_country          JSONB         NOT NULL, -- {"US": 75.0, "UK": 10.0, "JP": 8.0}
    allocation_by_region           JSONB         NOT NULL, -- {"north_america": 75.0, "europe": 15.0}

    -- Currency exposure
    allocation_by_currency         JSONB         NOT NULL, -- {"USD": 80.0, "EUR": 12.0, "GBP": 8.0}

    -- Top holdings details
    top_holdings                   JSONB         NOT NULL, -- [{symbol, weight, value, name}, ...]

    -- Concentration metrics
    top_5_weight                   DECIMAL(5, 2) NOT NULL, -- Combined weight of top 5
    top_10_weight                  DECIMAL(5, 2) NOT NULL, -- Combined weight of top 10
    largest_position_weight        DECIMAL(5, 2) NOT NULL, -- Weight of largest position

    created_at                     TIMESTAMPTZ      DEFAULT NOW(),
    updated_at                     TIMESTAMPTZ      DEFAULT NOW(),

    UNIQUE (account_id, as_of_date)
);

-- =====================================================
-- BENCHMARK & MARKET DATA
-- Benchmark indices and performance data
-- =====================================================

-- Benchmark index definitions (S&P 500, FTSE 100, etc.)
CREATE TABLE benchmark_master
(
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol      VARCHAR(10) UNIQUE NOT NULL, -- 'SPY', 'VTI', 'EAFE'
    name        VARCHAR(255)       NOT NULL, -- 'SPDR S&P 500 ETF Trust'
    description TEXT,                        -- Benchmark description
    currency    CHAR(3)     DEFAULT 'USD',
    region      VARCHAR(50),                 -- 'US', 'International', 'Emerging'
    asset_class VARCHAR(50),                 -- 'Equity', 'Fixed Income', 'Commodity'
    is_active   BOOLEAN     DEFAULT true,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Daily benchmark prices and returns
CREATE TABLE benchmark_prices
(
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    benchmark_id     UUID           NOT NULL REFERENCES benchmark_master (id) ON DELETE CASCADE,
    price_date       DATE           NOT NULL,
    close_price      DECIMAL(15, 4) NOT NULL,
    total_return_1d  DECIMAL(8, 4), -- 1-day total return
    total_return_ytd DECIMAL(8, 4), -- Year-to-date return
    total_return_1y  DECIMAL(8, 4), -- 1-year total return
    created_at       TIMESTAMPTZ      DEFAULT NOW(),

    UNIQUE (benchmark_id, price_date)
);

-- =====================================================
-- MARKET DATA
-- FX rates, interest rates, market holidays
-- =====================================================

-- Foreign exchange and interest rates
CREATE TABLE market_rates
(
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    rate_type     VARCHAR(20)    NOT NULL, -- 'fx', 'risk_free', 'libor'
    from_currency CHAR(3)        NOT NULL, -- Base currency
    to_currency   CHAR(3)        NOT NULL, -- Quote currency
    rate          DECIMAL(12, 8) NOT NULL, -- Exchange/interest rate
    rate_date     DATE           NOT NULL,
    data_source   data_source_enum DEFAULT 'calculated',
    created_at    TIMESTAMPTZ      DEFAULT NOW(),

    UNIQUE (rate_type, from_currency, to_currency, rate_date)
);

-- Trading calendar and market holidays
CREATE TABLE market_holidays
(
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    exchange        VARCHAR(20)  NOT NULL,         -- 'NYSE', 'NASDAQ', 'LSE'
    country         CHAR(2)      NOT NULL,         -- 'US', 'UK', 'CA'
    holiday_date    DATE         NOT NULL,
    holiday_name    VARCHAR(100) NOT NULL,         -- 'Christmas Day', 'Independence Day'
    is_full_closure BOOLEAN          DEFAULT true, -- Full day vs partial closure
    created_at      TIMESTAMPTZ      DEFAULT NOW(),

    UNIQUE (exchange, holiday_date)
);

-- =====================================================
-- REFERENCE DATA
-- Master data for currencies, countries, exchanges
-- =====================================================

-- Currency reference data
CREATE TABLE reference_currencies
(
    id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    currency_code  CHAR(3) UNIQUE NOT NULL,    -- 'USD', 'EUR', 'GBP'
    name           VARCHAR(100)   NOT NULL,    -- 'US Dollar', 'Euro'
    symbol         VARCHAR(5),                 -- '$', '€', '£'
    decimal_places INTEGER          DEFAULT 2, -- Number of decimal places
    is_active      BOOLEAN          DEFAULT true,
    created_at     TIMESTAMPTZ      DEFAULT NOW()
);

-- Country reference data
CREATE TABLE reference_countries
(
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    country_code  CHAR(2) UNIQUE NOT NULL,       -- ISO 3166-1 alpha-2 ('US', 'UK')
    country_name  VARCHAR(100)   NOT NULL,       -- 'United States', 'United Kingdom'
    region        VARCHAR(50),                   -- 'North America', 'Europe'
    currency_code CHAR(3),                       -- Primary currency
    is_developed  BOOLEAN          DEFAULT true, -- Developed vs emerging market
    is_active     BOOLEAN          DEFAULT true,
    created_at    TIMESTAMPTZ      DEFAULT NOW()
);

-- Stock exchange reference data
CREATE TABLE reference_exchanges
(
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    exchange_code VARCHAR(10) UNIQUE NOT NULL, -- 'NYSE', 'NASDAQ', 'LSE'
    exchange_name VARCHAR(255)       NOT NULL, -- 'New York Stock Exchange'
    country_code  CHAR(2)            NOT NULL, -- 'US', 'UK', 'JP'
    currency_code CHAR(3)            NOT NULL, -- Primary trading currency
    timezone      VARCHAR(50)        NOT NULL, -- 'America/New_York'
    market_open   TIME,                        -- Local market open time
    market_close  TIME,                        -- Local market close time
    is_active     BOOLEAN          DEFAULT true,
    created_at    TIMESTAMPTZ      DEFAULT NOW()
);

-- =====================================================
-- SYSTEM OPERATIONS
-- Job processing, logging, health monitoring
-- =====================================================

-- Background job processing and status
CREATE TABLE system_jobs
(
    id                 UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id           UUID REFERENCES user_accounts (id) ON DELETE CASCADE,
    job_type          VARCHAR(50) NOT NULL,          -- 'data_import', 'analytics_calc'
    job_name          VARCHAR(255),                  -- Descriptive job name
    status            VARCHAR(20) DEFAULT 'pending', -- 'pending', 'running', 'completed', 'failed'
    priority          INTEGER     DEFAULT 50,        -- Job priority (higher = more urgent)
    total_records     INTEGER     DEFAULT 0,         -- Total records to process
    processed_records INTEGER     DEFAULT 0,         -- Records processed so far
    failed_records    INTEGER     DEFAULT 0,         -- Records that failed
    error_message      TEXT,
    metadata          JSONB,                         -- Job-specific data
    started_at         TIMESTAMPTZ,
    completed_at       TIMESTAMPTZ,
    created_at        TIMESTAMPTZ DEFAULT NOW()
);

-- System logging and error tracking
CREATE TABLE system_logs
(
    id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    log_level  VARCHAR(10) NOT NULL, -- 'info', 'warn', 'error', 'debug'
    message    TEXT        NOT NULL,
    context    JSONB,                -- Additional context data
    user_id    UUID        REFERENCES user_accounts (id) ON DELETE SET NULL,
    source     VARCHAR(100),         -- Component that generated log
    request_id VARCHAR(100),         -- Request tracking ID
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- System health and performance metrics
CREATE TABLE system_health
(
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metric_name  VARCHAR(100)   NOT NULL,               -- 'api_response_time', 'db_connections'
    metric_value DECIMAL(15, 4) NOT NULL,
    metric_unit  VARCHAR(20),                           -- 'ms', 'count', 'percent'
    component    VARCHAR(50),                           -- 'api', 'database', 'worker'
    environment  VARCHAR(20)      DEFAULT 'production', -- 'production', 'staging', 'dev'
    recorded_at  TIMESTAMPTZ    NOT NULL,
    created_at   TIMESTAMPTZ      DEFAULT NOW()
);

-- =====================================================
-- INDEXES FOR PERFORMANCE
-- Critical indexes for query performance at scale
-- =====================================================

-- User and authentication indexes
CREATE INDEX idx_user_accounts_email ON user_accounts (email);
CREATE INDEX idx_user_sessions_user_id ON user_sessions (user_id);
CREATE INDEX idx_user_sessions_refresh_token ON user_sessions (refresh_token);
CREATE INDEX idx_user_sessions_expires_at ON user_sessions (expires_at);

-- Provider integration indexes
CREATE INDEX idx_provider_connections_user_id ON provider_connections (user_id);
CREATE INDEX idx_provider_mappings_connection_entity ON provider_mappings (connection_id, entity_type);
CREATE INDEX idx_provider_mappings_internal_id ON provider_mappings (internal_id);

-- Security master indexes
CREATE INDEX idx_security_master_symbol ON security_master (symbol);
CREATE INDEX idx_security_identifiers_type_value ON security_identifiers (identifier_type, identifier_value);
CREATE INDEX idx_security_prices_security_date ON security_prices (security_id, price_date DESC);

-- Portfolio data indexes (critical for performance)
CREATE INDEX idx_portfolio_accounts_user_id ON portfolio_accounts (user_id);
CREATE INDEX idx_portfolio_holdings_account_security ON portfolio_holdings (account_id, security_id);
CREATE INDEX idx_portfolio_holdings_date ON portfolio_holdings (as_of_date DESC);
CREATE INDEX idx_portfolio_transactions_account ON portfolio_transactions (account_id);
CREATE INDEX idx_portfolio_transactions_date ON portfolio_transactions (trade_date DESC);
CREATE INDEX idx_portfolio_transactions_security ON portfolio_transactions (security_id);

-- Analytics indexes (most frequently queried)
CREATE INDEX idx_analytics_summary_account_date ON analytics_summary (account_id, as_of_date DESC);
CREATE INDEX idx_analytics_summary_user_date ON analytics_summary (account_id) INCLUDE (as_of_date, market_value);
CREATE INDEX idx_analytics_performance_account_date ON analytics_performance (account_id, as_of_date DESC);
CREATE INDEX idx_analytics_risk_account_date ON analytics_risk (account_id, as_of_date DESC);
CREATE INDEX idx_analytics_exposure_account_date ON analytics_exposure (account_id, as_of_date DESC);

-- Market data indexes
CREATE INDEX idx_benchmark_prices_benchmark_date ON benchmark_prices (benchmark_id, price_date DESC);
CREATE INDEX idx_market_rates_type_currencies_date ON market_rates (rate_type, from_currency, to_currency, rate_date DESC);

-- System operations indexes
CREATE INDEX idx_system_jobs_user_status ON system_jobs (user_id, status);
CREATE INDEX idx_system_jobs_created_at ON system_jobs (created_at DESC);
CREATE INDEX idx_system_logs_level_created ON system_logs (log_level, created_at DESC);
CREATE INDEX idx_system_logs_user_created ON system_logs (user_id, created_at DESC);

-- =====================================================
-- TRIGGERS FOR AUTOMATIC TIMESTAMP UPDATES
-- Auto-update timestamps on record changes
-- =====================================================

-- Generic trigger function to update updated_at column
CREATE
OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at
= NOW();
RETURN NEW;
END;
$$
language 'plpgsql';

-- Apply updated_at triggers to relevant tables
CREATE TRIGGER update_user_accounts_updated_at
    BEFORE UPDATE
    ON user_accounts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_user_subscriptions_updated_at
    BEFORE UPDATE
    ON user_subscriptions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_provider_institutions_updated_at
    BEFORE UPDATE
    ON provider_institutions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_provider_connections_updated_at
    BEFORE UPDATE
    ON provider_connections
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_security_master_updated_at
    BEFORE UPDATE
    ON security_master
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_portfolio_accounts_updated_at
    BEFORE UPDATE
    ON portfolio_accounts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_portfolio_holdings_updated_at
    BEFORE UPDATE
    ON portfolio_holdings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_portfolio_transactions_updated_at
    BEFORE UPDATE
    ON portfolio_transactions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_analytics_summary_updated_at
    BEFORE UPDATE
    ON analytics_summary
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_analytics_performance_updated_at
    BEFORE UPDATE
    ON analytics_performance
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_analytics_risk_updated_at
    BEFORE UPDATE
    ON analytics_risk
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_analytics_exposure_updated_at
    BEFORE UPDATE
    ON analytics_exposure
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- USER-LEVEL ANALYTICS VIEW
-- Aggregated portfolio analytics across all accounts
-- =====================================================

-- Aggregated user-level portfolio metrics (roll-up of all accounts)
CREATE VIEW user_portfolio_summary AS
SELECT pa.user_id,
       a.as_of_date,
       pa.currency,

       -- Aggregated portfolio values
       SUM(a.market_value)          as total_market_value,
       SUM(a.cost_basis)            as total_cost_basis,
       SUM(a.cash_balance)          as total_cash_balance,
       SUM(a.unrealized_gain)       as total_unrealized_gain,
       SUM(a.realized_gain)         as total_realized_gain,

       -- Weighted average returns
       CASE
           WHEN SUM(a.market_value) > 0 THEN
               SUM(a.daily_return * a.market_value) / SUM(a.market_value)
           ELSE 0 END               as weighted_daily_return,
       CASE
           WHEN SUM(a.market_value) > 0 THEN
               SUM(a.ytd_return * a.market_value) / SUM(a.market_value)
           ELSE 0 END               as weighted_ytd_return,

       -- Asset allocation totals
       SUM(a.equity_value)          as total_equity_value,
       SUM(a.debt_value)            as total_debt_value,
       SUM(a.fund_value)            as total_fund_value,
       SUM(a.cash_value)            as total_cash_value,
       SUM(a.other_value)           as total_other_value,

       -- Geographic allocation
       SUM(a.domestic_value)        as total_domestic_value,
       SUM(a.international_value)   as total_international_value,

       -- Portfolio metadata
       COUNT(DISTINCT a.account_id) as account_count,
       SUM(a.holdings_count)        as total_holdings_count,
       MAX(a.last_price_date)       as latest_price_date

FROM analytics_summary a
         JOIN portfolio_accounts pa ON a.account_id = pa.id
WHERE pa.is_active = true
GROUP BY pa.user_id, a.as_of_date, pa.currency;

COMMIT;
