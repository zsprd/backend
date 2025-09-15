-- =====================================================
-- ZSPRD Database Migration
-- =====================================================

BEGIN;

-- =====================================================
-- EXTENSIONS & FUNCTIONS
-- =====================================================

-- Enable UUID generation
CREATE
EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable cryptographic functions for sensitive data encryption
CREATE
EXTENSION IF NOT EXISTS "pgcrypto";

-- =====================================================
-- ENUMS - Data type definitions
-- =====================================================

-- Account classification
CREATE TYPE account_type_enum AS ENUM (
    'investment',    -- Brokerage, 401k, IRA accounts
    'depository',    -- Checking, savings, money market
    'credit',        -- Credit cards, lines of credit
    'loan',          -- Mortgages, student loans
    'other'          -- Catch-all for other account types
);

-- Detailed account subtypes
CREATE TYPE account_subtype_enum AS ENUM (
    'brokerage', 'ira', 'roth_ira', '401k', '403b',
    'checking', 'savings', 'money_market', 'cd',
    'credit_card', 'mortgage', 'student', 'personal',
    'cash_management', 'crypto_exchange'
);

-- Security types (broad categories)
CREATE TYPE security_type_enum AS ENUM (
    'equity',          -- Stocks
    'fund',            -- Mutual funds, ETFs
    'debt',            -- Bonds, bills, notes
    'option',          -- Options, warrants
	'future',          -- Index Futures
	'forward'          -- Currency forwards
	'swap'             -- CFDs, IRS
    'cash',            -- Cash equivalents
    'digital',         -- Digital assets
    'other'            -- Commodities, REITs, etc.
);

-- Security subtypes (specific classifications)
CREATE TYPE security_subtype_enum AS ENUM (
    'common_stock', 'preferred_stock', 'etf', 'mutual_fund', 
    'bond', 'bill', 'note', 'option', 'warrant',
    'cash', 'cryptocurrency'
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
    'transfer_in', 'transfer_out', 'cancel', 'adjustment'
);

-- Data source tracking (where data originated)
CREATE TYPE data_source_enum AS ENUM (
    'plaid',        -- Plaid API
    'manual',       -- User manual entry
    'bulk',         -- CSV/Excel upload
    'calculated',   -- Computed by our system
    'yfinance',     -- Yahoo Finance API
    'alphavantage'  -- Alpha Vantage API
);

-- =====================================================
-- USER MANAGEMENT
-- =====================================================

CREATE TABLE users
(
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email         VARCHAR(320) UNIQUE NOT NULL,
    password_hash VARCHAR(255), -- bcrypt hash from backend
    full_name     VARCHAR(255),
    timezone      VARCHAR(50)      DEFAULT 'UTC',
    base_currency CHAR(3)          DEFAULT 'USD',
    is_active     BOOLEAN          DEFAULT true,
    is_verified   BOOLEAN          DEFAULT false,
    last_login_at TIMESTAMPTZ,
    created_at    TIMESTAMPTZ      DEFAULT NOW(),
    updated_at    TIMESTAMPTZ      DEFAULT NOW()
);

CREATE TABLE user_sessions
(
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id       UUID                NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    refresh_token VARCHAR(500) UNIQUE NOT NULL,
    expires_at    TIMESTAMPTZ         NOT NULL,
    created_at    TIMESTAMPTZ      DEFAULT NOW(),
    last_used_at  TIMESTAMPTZ      DEFAULT NOW(),
    ip_address    INET,
    user_agent    VARCHAR(500),
    device_type   VARCHAR(50)
);

CREATE TABLE user_subscriptions
(
    id                     UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id                UUID        NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    plan_name              VARCHAR(50) NOT NULL, -- 'free', 'premium', 'professional'
    status                 VARCHAR(20) NOT NULL, -- 'active', 'cancelled', 'past_due'
    current_period_start   DATE        NOT NULL,
    current_period_end     DATE        NOT NULL,
    cancelled_at           DATE,
    trial_start            DATE,
    trial_end              DATE,
    stripe_subscription_id VARCHAR(255) UNIQUE,
    stripe_customer_id     VARCHAR(255),
    stripe_product_id      VARCHAR(255),
    stripe_price_id        VARCHAR(255),
    amount                 DECIMAL(10, 2),
    currency               CHAR(3)          DEFAULT 'USD',
    created_at             TIMESTAMPTZ      DEFAULT NOW(),
    updated_at             TIMESTAMPTZ      DEFAULT NOW()
);

CREATE TABLE user_notifications
(
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id           UUID         NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    alert_id          UUID,                  -- References monitoring_alerts
    notification_type VARCHAR(50)  NOT NULL, -- 'alert', 'system', 'import'
    title             VARCHAR(255) NOT NULL,
    message           TEXT         NOT NULL,
    is_read           BOOLEAN          DEFAULT false,
    read_at           TIMESTAMPTZ,
    created_at        TIMESTAMPTZ      DEFAULT NOW(),
    updated_at        TIMESTAMPTZ      DEFAULT NOW()
);

-- =====================================================
-- INTEGRATIONS & CONNECTIONS
-- =====================================================

CREATE TABLE financial_institutions
(
    id                   UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    plaid_institution_id VARCHAR(255) UNIQUE,
    name                 VARCHAR(255) NOT NULL,
    country              CHAR(2)          DEFAULT 'US',
    website_url          TEXT,
    logo_url             TEXT,
    primary_color        VARCHAR(7),
    created_at           TIMESTAMPTZ      DEFAULT NOW(),
    updated_at           TIMESTAMPTZ      DEFAULT NOW()
);

CREATE TABLE data_connections
(
    id                 UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id            UUID             NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    institution_id     UUID             REFERENCES financial_institutions (id) ON DELETE SET NULL,
    name               VARCHAR(255)     NOT NULL,
    data_source        data_source_enum NOT NULL,
    plaid_item_id      VARCHAR(255),
    plaid_access_token VARCHAR(500), -- Encrypt with pgcrypto
    status             VARCHAR(50)      DEFAULT 'active',
    error_message      TEXT,
    metadata           JSONB,
    last_sync_at       TIMESTAMPTZ,
    created_at         TIMESTAMPTZ      DEFAULT NOW(),
    updated_at         TIMESTAMPTZ      DEFAULT NOW()
);

-- =====================================================
-- PORTFOLIO DATA
-- =====================================================

CREATE TABLE portfolio_accounts
(
    id                 UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id            UUID              NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    institution_id     UUID              REFERENCES financial_institutions (id) ON DELETE SET NULL,
    data_connection_id UUID              REFERENCES data_connections (id) ON DELETE SET NULL,
    plaid_account_id   VARCHAR(255),
    name               VARCHAR(255)      NOT NULL,
    official_name      VARCHAR(255),
    mask               VARCHAR(10), -- Last 4 digits
    account_type       account_type_enum NOT NULL,
    account_subtype    account_subtype_enum,
    currency           CHAR(3)          DEFAULT 'USD',
    is_active          BOOLEAN          DEFAULT true,
    data_source        data_source_enum DEFAULT 'manual',
    created_at         TIMESTAMPTZ      DEFAULT NOW(),
    updated_at         TIMESTAMPTZ      DEFAULT NOW()
);

CREATE TABLE portfolio_holdings
(
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id        UUID           NOT NULL REFERENCES portfolio_accounts (id) ON DELETE CASCADE,
    security_id       UUID           NOT NULL REFERENCES security_reference (id) ON DELETE CASCADE,
    plaid_account_id  VARCHAR(255),
    quantity          DECIMAL(15, 6) NOT NULL,
    cost_basis        DECIMAL(15, 4),
    currency          CHAR(3)          DEFAULT 'USD',
    institution_price DECIMAL(15, 4),
    institution_value DECIMAL(15, 2),
    data_source       data_source_enum DEFAULT 'manual',
    as_of_date        DATE           NOT NULL,
    created_at        TIMESTAMPTZ      DEFAULT NOW(),
    updated_at        TIMESTAMPTZ      DEFAULT NOW(),

    UNIQUE (account_id, security_id, as_of_date)
);

CREATE TABLE portfolio_transactions
(
    id                    UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id            UUID                  NOT NULL REFERENCES portfolio_accounts (id) ON DELETE CASCADE,
    security_id           UUID                  REFERENCES security_reference (id) ON DELETE SET NULL,
    plaid_transaction_id  VARCHAR(255),
    plaid_account_id      VARCHAR(255),
    cancel_transaction_id VARCHAR(255),
    transaction_type      transaction_type_enum NOT NULL,
    transaction_subtype   transaction_subtype_enum,
    quantity              DECIMAL(15, 6),
    price                 DECIMAL(15, 4),
    amount                DECIMAL(15, 2)        NOT NULL,
    fees                  DECIMAL(15, 2)   DEFAULT 0,
    currency              CHAR(3)          DEFAULT 'USD',
    data_source           data_source_enum DEFAULT 'manual',
    as_of_date            DATE                  NOT NULL,
    trade_date            DATE,
    settlement_date       DATE,
    name                  TEXT,
    created_at            TIMESTAMPTZ      DEFAULT NOW(),
    updated_at            TIMESTAMPTZ      DEFAULT NOW()
);

-- =====================================================
-- SECURITY & MARKET DATA
-- =====================================================

CREATE TABLE security_reference
(
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    plaid_security_id       VARCHAR(255) UNIQUE,
    institution_id          UUID REFERENCES financial_institutions (id),
    institution_security_id VARCHAR(255),
    symbol                  VARCHAR(50),
    name                    VARCHAR(500)       NOT NULL,
    security_type           security_type_enum NOT NULL,
    security_subtype        security_subtype_enum,
    currency                CHAR(3)          DEFAULT 'USD',
    exchange                VARCHAR(20),
    country                 CHAR(2),
    sector                  VARCHAR(100),
    industry                VARCHAR(100),
    cusip                   VARCHAR(9),
    isin                    VARCHAR(12),
    sedol                   VARCHAR(7),
    is_cash_equivalent      BOOLEAN          DEFAULT false,
    data_source             data_source_enum DEFAULT 'manual',
    option_details          JSONB, -- Strike, expiry, underlying
    fixed_income_details    JSONB, -- Maturity, coupon, rating
    created_at              TIMESTAMPTZ      DEFAULT NOW(),
    updated_at              TIMESTAMPTZ      DEFAULT NOW()
);

CREATE TABLE security_price
(
    id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    security_id    UUID           NOT NULL REFERENCES security_reference (id) ON DELETE CASCADE,
    as_of_date     DATE           NOT NULL,
    open_price     DECIMAL(15, 4),
    high_price     DECIMAL(15, 4),
    low_price      DECIMAL(15, 4),
    close_price    DECIMAL(15, 4) NOT NULL,
    volume         BIGINT,
    adjusted_close DECIMAL(15, 4),
    data_source    data_source_enum DEFAULT 'calculated',
    created_at     TIMESTAMPTZ      DEFAULT NOW(),

    UNIQUE (security_id, as_of_date)
);

-- =====================================================
-- ANALYTICS
-- =====================================================

-- Main analytics table with account snapshots and additive metrics
CREATE TABLE analytics_summary
(
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id          UUID           NOT NULL REFERENCES portfolio_accounts (id) ON DELETE CASCADE,
    as_of_date          DATE           NOT NULL,

    -- Account balances
    available_balance   DECIMAL(15, 2),
    current_balance     DECIMAL(15, 2),
    balance_limit       DECIMAL(15, 2),

    -- Portfolio values
    market_value        DECIMAL(15, 2) NOT NULL,
    cost_basis          DECIMAL(15, 2) NOT NULL,
    cash_contributions  DECIMAL(15, 2) NOT NULL,    -- Total money deposited
    fees_paid           DECIMAL(15, 2)   DEFAULT 0, -- Total fees paid

    -- Performance metrics (1Y lookback)
    total_return        DECIMAL(10, 4),
    annualized_return   DECIMAL(10, 4),
    ytd_return          DECIMAL(10, 4),
    daily_return        DECIMAL(10, 6),

    -- Asset allocation (additive for users-level views)
    equity_value        DECIMAL(15, 2)   DEFAULT 0,
    debt_value          DECIMAL(15, 2)   DEFAULT 0,
    cash_value          DECIMAL(15, 2)   DEFAULT 0,
    alternatives_value  DECIMAL(15, 2)   DEFAULT 0,

    -- Geographic allocation (additive)
    domestic_value      DECIMAL(15, 2)   DEFAULT 0,
    international_value DECIMAL(15, 2)   DEFAULT 0,

    -- Metadata
    currency            CHAR(3)        NOT NULL,
    holdings_count      INTEGER          DEFAULT 0,
    data_quality        VARCHAR(20),
    last_price_date     DATE,

    created_at          TIMESTAMPTZ      DEFAULT NOW(),
    updated_at          TIMESTAMPTZ      DEFAULT NOW(),

    UNIQUE (account_id, as_of_date)
);

-- Performance analytics (benchmarking and return attribution)
CREATE TABLE analytics_performance
(
    id                 UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id         UUID        NOT NULL REFERENCES portfolio_accounts (id) ON DELETE CASCADE,
    as_of_date         DATE        NOT NULL,

    -- Benchmark comparison
    benchmark_symbol   VARCHAR(10) NOT NULL,
    alpha              DECIMAL(8, 4),
    beta               DECIMAL(8, 4),
    correlation        DECIMAL(6, 4),

    -- Performance distribution
    best_day           DECIMAL(8, 4),
    worst_day          DECIMAL(8, 4),
    positive_periods   INTEGER,
    negative_periods   INTEGER,
    win_rate           DECIMAL(5, 2),

    -- Time series data
    time_series_data   JSONB,

    calculation_status VARCHAR(20) NOT NULL,
    error_message      VARCHAR(500),
    created_at         TIMESTAMPTZ      DEFAULT NOW(),
    updated_at         TIMESTAMPTZ      DEFAULT NOW(),

    UNIQUE (account_id, as_of_date)
);

-- Exposure analytics (detailed allocation breakdowns)
CREATE TABLE analytics_exposure
(
    id                             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id                     UUID          NOT NULL REFERENCES portfolio_accounts (id) ON DELETE CASCADE,
    as_of_date                     DATE          NOT NULL,

    -- Allocation breakdowns
    allocation_by_asset_class      JSONB         NOT NULL, -- {"equity": 60, "debt": 40}
    allocation_by_security_type    JSONB         NOT NULL, -- {"etf": 50, "stock": 30}
    allocation_by_security_subtype JSONB         NOT NULL, -- {"common_stock": 25}
    allocation_by_sector           JSONB         NOT NULL, -- {"technology": 25}
    allocation_by_industry         JSONB         NOT NULL, -- {"software": 12}
    allocation_by_region           JSONB         NOT NULL, -- {"north_america": 70}
    allocation_by_country          JSONB         NOT NULL, -- {"US": 70, "UK": 10}
    allocation_by_currency         JSONB         NOT NULL, -- {"USD": 80, "EUR": 20}
    allocation_by_equity_style     JSONB,                  -- {"large_growth": 30}
    allocation_by_debt_style       JSONB,                  -- {"government": 40}

    -- Concentration metrics
    top_5_weight                   DECIMAL(5, 2) NOT NULL,
    top_10_weight                  DECIMAL(5, 2) NOT NULL,
    largest_position_weight        DECIMAL(5, 2) NOT NULL,
    top_holdings                   JSONB         NOT NULL,

    calculation_status             VARCHAR(20)   NOT NULL,
    error_message                  VARCHAR(500),
    created_at                     TIMESTAMPTZ      DEFAULT NOW(),
    updated_at                     TIMESTAMPTZ      DEFAULT NOW(),

    UNIQUE (account_id, as_of_date)
);

-- Risk analytics (comprehensive risk measures)
CREATE TABLE analytics_risk
(
    id                    UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id            UUID           NOT NULL REFERENCES portfolio_accounts (id) ON DELETE CASCADE,
    as_of_date            DATE           NOT NULL,

    -- Risk-adjusted return ratios
    volatility            DECIMAL(10, 4) NOT NULL,
    sharpe_ratio          DECIMAL(8, 4),
    sortino_ratio         DECIMAL(8, 4),
    calmar_ratio          DECIMAL(8, 4),
    omega_ratio           DECIMAL(8, 4),

    -- Drawdown metrics
    max_drawdown          DECIMAL(8, 4)  NOT NULL,
    current_drawdown      DECIMAL(8, 4)  NOT NULL,
    average_drawdown      DECIMAL(8, 4),
    max_drawdown_duration INTEGER,       -- Days underwater
    recovery_time         INTEGER,       -- Days to recover

    -- Value at Risk
    var_95                DECIMAL(8, 4)  NOT NULL,
    var_99                DECIMAL(8, 4)  NOT NULL,
    var_99_9              DECIMAL(8, 4),
    cvar_95               DECIMAL(8, 4)  NOT NULL,
    cvar_99               DECIMAL(8, 4),

    -- Distribution metrics
    downside_deviation    DECIMAL(8, 4)  NOT NULL,
    skewness              DECIMAL(8, 4),
    kurtosis              DECIMAL(8, 4),
    gain_loss_ratio       DECIMAL(8, 4),
    tail_ratio            DECIMAL(8, 4),

    -- Leverage metrics
    gross_leverage        DECIMAL(8, 4), -- (Long + Short) / NAV
    net_leverage          DECIMAL(8, 4), -- (Long - Short) / NAV
    long_exposure         DECIMAL(8, 4), -- Long positions / NAV
    short_exposure        DECIMAL(8, 4), -- Short positions / NAV
    margin_utilization    DECIMAL(5, 2), -- Margin used / available (%)

    -- Capture ratios (vs benchmark)
    up_capture_ratio      DECIMAL(8, 4),
    down_capture_ratio    DECIMAL(8, 4),

    -- Time series data
    time_series_data      JSONB,         -- Rolling metrics

    calculation_status    VARCHAR(20)    NOT NULL,
    error_message         VARCHAR(500),
    created_at            TIMESTAMPTZ      DEFAULT NOW(),
    updated_at            TIMESTAMPTZ      DEFAULT NOW(),

    UNIQUE (account_id, as_of_date)
);

-- =====================================================
-- MONITORING & ALERTS
-- =====================================================

CREATE TABLE monitoring_alerts
(
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id           UUID        NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    alert_type        VARCHAR(50) NOT NULL, -- 'price_change', 'portfolio_value'
    description       TEXT,
    conditions        JSONB,                -- Alert thresholds and rules
    is_active         BOOLEAN          DEFAULT true,
    last_triggered_at TIMESTAMPTZ,
    trigger_count     INTEGER          DEFAULT 0,
    created_at        TIMESTAMPTZ      DEFAULT NOW(),
    updated_at        TIMESTAMPTZ      DEFAULT NOW()
);

-- Add foreign key for notifications after alerts table is created
ALTER TABLE user_notifications
    ADD CONSTRAINT fk_notifications_alert
        FOREIGN KEY (alert_id) REFERENCES monitoring_alerts (id) ON DELETE SET NULL;

-- =====================================================
-- SYSTEM LOGS
-- =====================================================

CREATE TABLE import_jobs
(
    id                 UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id            UUID        NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    data_connection_id UUID REFERENCES data_connections (id) ON DELETE CASCADE,
    job_type           VARCHAR(50) NOT NULL,               -- 'accounts', 'transactions', 'holdings'
    status             VARCHAR(20)      DEFAULT 'pending', -- 'pending', 'running', 'completed', 'failed'
    filename           VARCHAR(255),
    file_size          BIGINT,
    total_records      INTEGER          DEFAULT 0,
    processed_records  INTEGER          DEFAULT 0,
    failed_records     INTEGER          DEFAULT 0,
    error_message      TEXT,
    metadata           JSONB,
    started_at         TIMESTAMPTZ,
    completed_at       TIMESTAMPTZ,
    created_at         TIMESTAMPTZ      DEFAULT NOW()
);

CREATE TABLE audit_logs
(
    id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id        UUID        REFERENCES users (id) ON DELETE SET NULL,
    action         VARCHAR(50) NOT NULL, -- 'create', 'update', 'delete', 'login'
    table_name     VARCHAR(50),          -- Which table was affected
    record_id      VARCHAR(255),         -- Which record was affected
    old_values     JSONB,                -- Previous values
    new_values     JSONB,                -- New values
    ip_address     INET,
    user_agent     TEXT,
    request_path   VARCHAR(500),
    request_method VARCHAR(10),
    created_at     TIMESTAMPTZ      DEFAULT NOW()
);

-- =====================================================
-- USER ANALYTICS VIEW
-- =====================================================

-- Aggregated users-level metrics from account analytics
CREATE VIEW user_analytics AS
SELECT a.user_id,
       aa.as_of_date,
       aa.currency,

       -- Additive values
       SUM(aa.market_value)                           as total_market_value,
       SUM(aa.cost_basis)                             as total_cost_basis,
       SUM(aa.cash_contributions)                     as total_cash_contributions,
       SUM(aa.fees_paid)                              as total_fees_paid,

       -- Asset allocation
       SUM(aa.equity_value)                           as total_equity_value,
       SUM(aa.debt_value)                             as total_debt_value,
       SUM(aa.cash_value)                             as total_cash_value,
       SUM(aa.alternatives_value)                     as total_alternatives_value,

       -- Geographic allocation
       SUM(aa.domestic_value)                         as total_domestic_value,
       SUM(aa.international_value)                    as total_international_value,

       -- Calculated percentages
       CASE
           WHEN SUM(aa.market_value) > 0 THEN
               SUM(aa.equity_value) / SUM(aa.market_value) * 100
           ELSE 0 END                                 as equity_percentage,
       CASE
           WHEN SUM(aa.market_value) > 0 THEN
               SUM(aa.debt_value) / SUM(aa.market_value) * 100
           ELSE 0 END                                 as debt_percentage,
       CASE
           WHEN SUM(aa.market_value) > 0 THEN
               SUM(aa.domestic_value) / SUM(aa.market_value) * 100
           ELSE 0 END                                 as domestic_percentage,

       -- Account metadata
       COUNT(DISTINCT aa.account_id)                  as account_count,
       STRING_AGG(DISTINCT a.account_type::text, ',') as account_types

FROM analytics_summary aa
         JOIN portfolio_accounts a ON aa.account_id = a.id
WHERE a.is_active = true
GROUP BY a.user_id, aa.as_of_date, aa.currency;

-- =====================================================
-- INDEXES
-- =====================================================

-- Users and sessions
CREATE INDEX idx_users_email ON users (email);
CREATE INDEX idx_user_sessions_user_id ON user_sessions (user_id);
CREATE INDEX idx_user_sessions_refresh_token ON user_sessions (refresh_token);
CREATE INDEX idx_user_sessions_expires_at ON user_sessions (expires_at);
CREATE INDEX idx_user_subscriptions_user_id ON user_subscriptions (user_id);

-- Core data
CREATE INDEX idx_data_connections_user_id ON data_connections (user_id);
CREATE INDEX idx_portfolio_accounts_user_id ON portfolio_accounts (user_id);
CREATE INDEX idx_portfolio_accounts_data_connection ON portfolio_accounts (data_connection_id);

-- Securities
CREATE INDEX idx_security_reference_symbol ON security_reference (symbol);
CREATE INDEX idx_security_reference_identifiers ON security_reference (cusip, isin, sedol);
CREATE INDEX idx_security_reference_plaid_id ON security_reference (plaid_security_id);

-- Time-series data
CREATE INDEX idx_portfolio_holdings_account_security ON portfolio_holdings (account_id, security_id);
CREATE INDEX idx_portfolio_holdings_date ON portfolio_holdings (as_of_date DESC);
CREATE INDEX idx_portfolio_transactions_account ON portfolio_transactions (account_id);
CREATE INDEX idx_portfolio_transactions_date ON portfolio_transactions (as_of_date DESC);
CREATE INDEX idx_market_data_security_date ON security_price (security_id, as_of_date DESC);

-- Analytics
CREATE INDEX idx_analytics_summary_account_date ON analytics_summary (account_id, as_of_date DESC);
CREATE INDEX idx_analytics_summary_date ON analytics_summary (as_of_date DESC);
CREATE INDEX idx_analytics_performance_account ON analytics_performance (account_id, as_of_date DESC);
CREATE INDEX idx_analytics_exposure_account ON analytics_exposure (account_id, as_of_date DESC);
CREATE INDEX idx_analytics_risk_account ON analytics_risk (account_id, as_of_date DESC);

-- Monitoring and audit
CREATE INDEX idx_monitoring_alerts_user_id ON monitoring_alerts (user_id);
CREATE INDEX idx_user_notifications_user_id ON user_notifications (user_id);
CREATE INDEX idx_audit_logs_user_id ON audit_logs (user_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs (created_at DESC);

-- =====================================================
-- TRIGGERS
-- =====================================================

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

-- Apply to tables with updated_at columns
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE
    ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_subscriptions_updated_at
    BEFORE UPDATE
    ON user_subscriptions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_notifications_updated_at
    BEFORE UPDATE
    ON user_notifications
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_financial_institutions_updated_at
    BEFORE UPDATE
    ON financial_institutions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_data_connections_updated_at
    BEFORE UPDATE
    ON data_connections
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_portfolio_accounts_updated_at
    BEFORE UPDATE
    ON portfolio_accounts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_security_reference_updated_at
    BEFORE UPDATE
    ON security_reference
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

CREATE TRIGGER update_analytics_exposure_updated_at
    BEFORE UPDATE
    ON analytics_exposure
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_analytics_risk_updated_at
    BEFORE UPDATE
    ON analytics_risk
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_monitoring_alerts_updated_at
    BEFORE UPDATE
    ON monitoring_alerts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMIT;
