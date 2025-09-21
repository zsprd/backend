-- =====================================================
-- ZSPRD Portfolio Analytics Database - Final Schema
-- =====================================================
-- Professional portfolio management for individuals & institutions
-- Clean separation of data providers, counterparties, and users
-- Organized by functional groups for modular development
-- =====================================================

BEGIN;

-- =====================================================
-- EXTENSIONS & FUNCTIONS
-- =====================================================

CREATE
EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE
EXTENSION IF NOT EXISTS "pgcrypto";

-- =====================================================
-- ENUMS - Standardized data classifications
-- =====================================================

CREATE TYPE plan_type_enum AS ENUM ('free', 'premium', 'professional', 'enterprise');

CREATE TYPE account_type_enum AS ENUM ('investment', 'depository', 'credit', 'loan', 'other');

CREATE TYPE account_subtype_enum AS ENUM (
    'brokerage', 'ira', 'roth', '401k', 'isa',
    'checking', 'savings', 'money market', 'cd',
    'credit card', 'mortgage', 'student', 'personal',
    'cash management', 'crypto', 'paypal', 'loan',
    'auto', 'business', 'commercial', 'line of credit', 'other'
);

CREATE TYPE security_type_enum AS ENUM ('equity', 'fund', 'debt', 'option', 'future', 'forward', 'swap', 'cash', 'digital', 'other');

CREATE TYPE security_subtype_enum AS ENUM (
    'common stock', 'preferred stock', 'etf', 'mutual fund',
    'index fund', 'bond', 'bill', 'note', 'option', 'warrant',
    'cash', 'cryptocurrency', 'reit', 'commodity'
);

CREATE TYPE transaction_type_enum AS ENUM ('buy', 'sell', 'cash', 'transfer', 'fee', 'dividend', 'interest', 'cancel', 'adjustment', 'split', 'merger', 'spinoff');

CREATE TYPE transaction_subtype_enum AS ENUM (
    'buy', 'sell', 'deposit', 'withdrawal', 'dividend', 'interest', 'fee',
    'transfer in', 'transfer out', 'cancel', 'adjustment', 'stock split', 'merger', 'spinoff'
);

CREATE TYPE data_source_enum AS ENUM (
    'bloomberg',      -- Bloomberg Terminal/API
    'refinitiv',      -- Refinitiv (formerly Reuters)
    'yfinance',       -- Yahoo Finance API
    'alphavantage',   -- Alpha Vantage API
    'plaid',          -- Plaid for account data
    'yodlee',         -- Yodlee for account aggregation
    'manual',         -- User manual entry
    'csv',            -- CSV/Excel upload
    'calculated'      -- System computed values
);

-- =====================================================
-- USER MANAGEMENT GROUP
-- Identity, authentication, billing, notifications
-- =====================================================

CREATE TABLE user_accounts
(
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email         VARCHAR(320) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    full_name     VARCHAR(255),
    timezone      VARCHAR(50)      DEFAULT 'UTC',
    base_currency CHAR(3) DEFAULT 'USD',
    is_active     BOOLEAN          DEFAULT true,
    is_verified   BOOLEAN DEFAULT false,
    last_login_at TIMESTAMPTZ,
    created_at    TIMESTAMPTZ      DEFAULT NOW(),
    updated_at    TIMESTAMPTZ      DEFAULT NOW()
);

CREATE TABLE user_sessions
(
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES user_accounts (id) ON DELETE CASCADE,
    refresh_token VARCHAR(500) UNIQUE NOT NULL,
    expires_at    TIMESTAMPTZ         NOT NULL,
    created_at    TIMESTAMPTZ      DEFAULT NOW(),
    last_used_at  TIMESTAMPTZ      DEFAULT NOW(),
    ip_address    INET,
    user_agent    VARCHAR(500)
);

CREATE TABLE user_subscriptions
(
    id                     UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id                UUID        NOT NULL REFERENCES user_accounts (id) ON DELETE CASCADE,
    plan_name              plan_type_enum NOT NULL,
    status                 VARCHAR(20) NOT NULL,
    current_period_start   DATE           NOT NULL,
    current_period_end     DATE           NOT NULL,
    cancelled_at           DATE,
    stripe_subscription_id VARCHAR(255) UNIQUE,
    stripe_customer_id     VARCHAR(255),
    amount                 DECIMAL(10, 2),
    currency               CHAR(3)          DEFAULT 'USD',
    created_at             TIMESTAMPTZ      DEFAULT NOW(),
    updated_at             TIMESTAMPTZ      DEFAULT NOW()
);

CREATE TABLE user_notifications
(
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id           UUID        NOT NULL REFERENCES user_accounts (id) ON DELETE CASCADE,
    notification_type VARCHAR(50) NOT NULL,
    title             VARCHAR(255) NOT NULL,
    message           TEXT         NOT NULL,
    is_read           BOOLEAN          DEFAULT false,
    read_at           TIMESTAMPTZ,
    created_at        TIMESTAMPTZ      DEFAULT NOW()
);

-- =====================================================
-- DATA PROVIDER GROUP
-- External data source management and connections
-- =====================================================

CREATE TABLE data_providers
(
    id                   UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    provider_code        VARCHAR(50) UNIQUE NOT NULL, -- 'bloomberg', 'refinitiv', 'yfinance'
    name                 VARCHAR(255)       NOT NULL, -- 'Bloomberg L.P.', 'Yahoo Finance'
    provider_type        VARCHAR(50)        NOT NULL, -- 'market_data', 'fundamental_data', 'account_data'
    supported_data_types JSONB              NOT NULL, -- ['security_prices', 'corporate_actions', 'account_data']
    api_base_url         VARCHAR(500),
    rate_limit_per_day   INTEGER,
    cost_per_request     DECIMAL(10, 4),
    is_active            BOOLEAN     DEFAULT true,
    created_at           TIMESTAMPTZ DEFAULT NOW(),
    updated_at           TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE data_connections
(
    id                 UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    provider_id        UUID         NOT NULL REFERENCES data_providers (id) ON DELETE CASCADE,
    connection_name    VARCHAR(255) NOT NULL,        -- 'Bloomberg Terminal', 'Yahoo Finance API'
    provider_name      VARCHAR(50)  NOT NULL,        -- 'bloomberg', 'yfinance'
    data_source        data_source_enum NOT NULL,
    access_credentials TEXT,                         -- Encrypted API keys, tokens
    status             VARCHAR(50) DEFAULT 'active', -- 'active', 'error', 'suspended'
    error_message      TEXT,
    last_sync_at       TIMESTAMPTZ,
    sync_frequency INTERVAL,                         -- How often to sync
    created_at         TIMESTAMPTZ DEFAULT NOW(),
    updated_at         TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE data_mappings
(
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    connection_id UUID        NOT NULL REFERENCES data_connections (id) ON DELETE CASCADE,
    entity_type   VARCHAR(50) NOT NULL,  -- 'security', 'benchmark', 'account'
    internal_id   UUID         NOT NULL, -- Our internal ID
    external_id   VARCHAR(255) NOT NULL, -- Provider's ID
    created_at    TIMESTAMPTZ      DEFAULT NOW(),

    UNIQUE (connection_id, entity_type, external_id)
);

-- =====================================================
-- COUNTERPARTY GROUP
-- Financial institutions and custody relationships
-- =====================================================

CREATE TABLE counterparty_master
(
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    counterparty_code VARCHAR(50) UNIQUE NOT NULL, -- 'schwab', 'fidelity', 'chase'
    name              VARCHAR(255)       NOT NULL, -- 'Charles Schwab Corporation'
    counterparty_type VARCHAR(50)        NOT NULL, -- 'broker', 'bank', 'custodian', 'prime_broker'
    country_code      CHAR(2),
    regulatory_id     VARCHAR(100),                -- LEI, FDIC number, etc.
    is_active         BOOLEAN          DEFAULT true,
    created_at        TIMESTAMPTZ      DEFAULT NOW(),
    updated_at        TIMESTAMPTZ      DEFAULT NOW()
);

-- =====================================================
-- SECURITY GROUP
-- Security reference data and market prices
-- =====================================================

CREATE TABLE security_master
(
    id                       UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol                   VARCHAR(50),
    name                     VARCHAR(500)       NOT NULL,
    security_type            security_type_enum NOT NULL,
    security_subtype         security_subtype_enum,
    currency                 CHAR(3)          DEFAULT 'USD',
    exchange                 VARCHAR(20),
    country                  CHAR(2),
    sector                   VARCHAR(100),
    industry                 VARCHAR(100),
    is_cash_equivalent       BOOLEAN          DEFAULT false,
    option_details           JSONB,
    bond_details             JSONB,

    -- Data provider relationships
    primary_data_provider_id UUID REFERENCES data_providers (id),
    data_source              data_source_enum DEFAULT 'manual',

    created_at               TIMESTAMPTZ      DEFAULT NOW(),
    updated_at               TIMESTAMPTZ      DEFAULT NOW()
);

CREATE TABLE security_prices
(
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    security_id      UUID           NOT NULL REFERENCES security_master (id) ON DELETE CASCADE,
    price_date       DATE           NOT NULL,
    close_price      DECIMAL(15, 4) NOT NULL,
    volume           BIGINT,

    -- Provider tracking
    data_provider_id UUID REFERENCES data_providers (id),
    data_source      data_source_enum DEFAULT 'calculated',

    created_at       TIMESTAMPTZ      DEFAULT NOW(),

    UNIQUE (security_id, price_date)
);

CREATE TABLE security_identifiers
(
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    security_id     UUID        NOT NULL REFERENCES security_master (id) ON DELETE CASCADE,
    identifier_type VARCHAR(20) NOT NULL, -- 'cusip', 'isin', 'bloomberg_id', 'symbol'
    identifier_value VARCHAR(50) NOT NULL,
    is_primary      BOOLEAN DEFAULT false,
    created_at       TIMESTAMPTZ      DEFAULT NOW(),

    UNIQUE (identifier_type, identifier_value)
);

-- =====================================================
-- BENCHMARK GROUP
-- Benchmark indices and performance data
-- =====================================================

CREATE TABLE benchmark_master
(
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol           VARCHAR(10) UNIQUE NOT NULL,
    name             VARCHAR(255)       NOT NULL,
    description      TEXT,
    currency         CHAR(3)          DEFAULT 'USD',
    region           VARCHAR(50),
    asset_class      VARCHAR(50),

    -- Provider relationship
    data_provider_id UUID REFERENCES data_providers (id),

    is_active        BOOLEAN          DEFAULT true,
    created_at       TIMESTAMPTZ      DEFAULT NOW()
);

CREATE TABLE benchmark_prices
(
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    benchmark_id     UUID           NOT NULL REFERENCES benchmark_master (id) ON DELETE CASCADE,
    price_date       DATE           NOT NULL,
    close_price      DECIMAL(15, 4) NOT NULL,
    total_return_1d  DECIMAL(8, 4),
    total_return_ytd DECIMAL(8, 4),
    total_return_1y  DECIMAL(8, 4),

    -- Provider tracking
    data_provider_id UUID REFERENCES data_providers (id),

    created_at       TIMESTAMPTZ      DEFAULT NOW(),

    UNIQUE (benchmark_id, price_date)
);

-- =====================================================
-- PORTFOLIO GROUP
-- User investment accounts, holdings, transactions
-- =====================================================

CREATE TABLE portfolio_accounts
(
    id                 UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id            UUID         NOT NULL REFERENCES user_accounts (id) ON DELETE CASCADE,

    name               VARCHAR(255) NOT NULL,
    account_number     VARCHAR(100), -- Masked/encrypted account number
    account_type       account_type_enum NOT NULL,
    account_subtype    account_subtype_enum,
    currency           CHAR(3)     DEFAULT 'USD',

    -- Data sourcing (how we get account data) - optional
    data_connection_id UUID         REFERENCES data_connections (id) ON DELETE SET NULL,
    data_source        data_source_enum DEFAULT 'manual',

    is_active          BOOLEAN     DEFAULT true,
    created_at         TIMESTAMPTZ DEFAULT NOW(),
    updated_at         TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE portfolio_holdings
(
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id      UUID           NOT NULL REFERENCES portfolio_accounts (id) ON DELETE CASCADE,
    security_id     UUID           NOT NULL REFERENCES security_master (id) ON DELETE CASCADE,

    -- Counterparty relationship (where holding is custodied)
    counterparty_id UUID           REFERENCES counterparty_master (id) ON DELETE SET NULL,

    quantity        DECIMAL(15, 6) NOT NULL,
    cost_basis      DECIMAL(15, 4),
    currency        CHAR(3)          DEFAULT 'USD',
    as_of_date      DATE           NOT NULL,
    data_source     data_source_enum DEFAULT 'manual',
    created_at      TIMESTAMPTZ      DEFAULT NOW(),
    updated_at      TIMESTAMPTZ      DEFAULT NOW(),

    UNIQUE (account_id, security_id, as_of_date)
);

CREATE TABLE portfolio_transactions
(
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id          UUID                  NOT NULL REFERENCES portfolio_accounts (id) ON DELETE CASCADE,
    security_id         UUID                  REFERENCES security_master (id) ON DELETE SET NULL,

    -- Counterparty relationship (where transaction was executed)
    counterparty_id     UUID                  REFERENCES counterparty_master (id) ON DELETE SET NULL,

    transaction_type    transaction_type_enum NOT NULL,
    transaction_subtype transaction_subtype_enum,
    quantity            DECIMAL(15, 6),
    price               DECIMAL(15, 4),
    amount              DECIMAL(15, 2)        NOT NULL,
    fees                DECIMAL(15, 2)   DEFAULT 0,
    currency            CHAR(3)          DEFAULT 'USD',
    trade_date          DATE                  NOT NULL,
    settlement_date     DATE,
    description         TEXT,
    data_source         data_source_enum DEFAULT 'manual',
    created_at          TIMESTAMPTZ      DEFAULT NOW(),
    updated_at          TIMESTAMPTZ      DEFAULT NOW()
);

-- =====================================================
-- ANALYTICS GROUP
-- Performance metrics, risk analysis, exposure data
-- =====================================================

CREATE TABLE analytics_summary
(
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id          UUID           NOT NULL REFERENCES portfolio_accounts (id) ON DELETE CASCADE,
    as_of_date          DATE           NOT NULL,
    market_value        DECIMAL(15, 2) NOT NULL,
    cost_basis          DECIMAL(15, 2) NOT NULL,
    cash_balance        DECIMAL(15, 2) DEFAULT 0,
    unrealized_gain     DECIMAL(15, 2) NOT NULL,
    realized_gain       DECIMAL(15, 2) DEFAULT 0,
    total_return        DECIMAL(10, 4),
    daily_return        DECIMAL(10, 6),
    weekly_return       DECIMAL(10, 4),
    monthly_return      DECIMAL(10, 4),
    quarterly_return    DECIMAL(10, 4),
    ytd_return          DECIMAL(10, 4),
    annual_return       DECIMAL(10, 4),
    equity_value        DECIMAL(15, 2) DEFAULT 0,
    debt_value          DECIMAL(15, 2) DEFAULT 0,
    fund_value          DECIMAL(15, 2) DEFAULT 0,
    cash_value          DECIMAL(15, 2) DEFAULT 0,
    other_value         DECIMAL(15, 2) DEFAULT 0,
    domestic_value      DECIMAL(15, 2) DEFAULT 0,
    international_value DECIMAL(15, 2) DEFAULT 0,
    currency            CHAR(3)        NOT NULL,
    holdings_count      INTEGER        DEFAULT 0,
    last_price_date     DATE,
    value_time_series   JSONB,
    return_time_series  JSONB,
    created_at          TIMESTAMPTZ    DEFAULT NOW(),
    updated_at          TIMESTAMPTZ    DEFAULT NOW(),

    UNIQUE (account_id, as_of_date)
);

CREATE TABLE analytics_performance
(
    id                 UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id        UUID          NOT NULL REFERENCES portfolio_accounts (id) ON DELETE CASCADE,
    as_of_date        DATE          NOT NULL,
    benchmark_symbol  VARCHAR(10)   NOT NULL,
    alpha             DECIMAL(8, 4),
    beta              DECIMAL(8, 4),
    correlation       DECIMAL(6, 4),
    tracking_error    DECIMAL(8, 4),
    volatility        DECIMAL(10, 4),
    sharpe_ratio      DECIMAL(8, 4),
    sortino_ratio     DECIMAL(8, 4),
    information_ratio DECIMAL(8, 4),
    calmar_ratio      DECIMAL(8, 4),
    max_drawdown      DECIMAL(8, 4) NOT NULL,
    current_drawdown  DECIMAL(8, 4) NOT NULL,
    recovery_days     INTEGER,
    best_day_return   DECIMAL(8, 4),
    worst_day_return  DECIMAL(8, 4),
    positive_days     INTEGER,
    negative_days     INTEGER,
    win_rate          DECIMAL(5, 2),
    daily_returns     JSONB,
    benchmark_returns JSONB,
    rolling_returns   JSONB,
    created_at        TIMESTAMPTZ DEFAULT NOW(),
    updated_at        TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE (account_id, as_of_date)
);

CREATE TABLE analytics_risk
(
    id                   UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id           UUID           NOT NULL REFERENCES portfolio_accounts (id) ON DELETE CASCADE,
    as_of_date           DATE           NOT NULL,
    var_95_1d            DECIMAL(8, 4)  NOT NULL,
    var_99_1d            DECIMAL(8, 4)  NOT NULL,
    cvar_95_1d           DECIMAL(8, 4)  NOT NULL,
    cvar_99_1d           DECIMAL(8, 4)  NOT NULL,
    volatility           DECIMAL(10, 4) NOT NULL,
    downside_deviation   DECIMAL(8, 4),
    skewness             DECIMAL(8, 4),
    kurtosis             DECIMAL(8, 4),
    concentration_hhi    DECIMAL(6, 4),
    effective_positions  DECIMAL(8, 2),
    largest_position_pct DECIMAL(5, 2),
    top_5_concentration  DECIMAL(5, 2),
    top_10_concentration DECIMAL(5, 2),
    tail_ratio           DECIMAL(8, 4),
    gain_loss_ratio      DECIMAL(8, 4),
    rolling_volatility   JSONB,
    rolling_var          JSONB,
    created_at           TIMESTAMPTZ      DEFAULT NOW(),
    updated_at           TIMESTAMPTZ      DEFAULT NOW(),

    UNIQUE (account_id, as_of_date)
);

CREATE TABLE analytics_exposure
(
    id                             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id                     UUID          NOT NULL REFERENCES portfolio_accounts (id) ON DELETE CASCADE,
    as_of_date                     DATE          NOT NULL,
    allocation_by_security_type    JSONB         NOT NULL,
    allocation_by_security_subtype JSONB         NOT NULL,
    allocation_by_sector           JSONB         NOT NULL,
    allocation_by_industry         JSONB         NOT NULL,
    allocation_by_country          JSONB         NOT NULL,
    allocation_by_region           JSONB         NOT NULL,
    allocation_by_currency         JSONB         NOT NULL,
    top_holdings                   JSONB         NOT NULL,
    top_5_weight                   DECIMAL(5, 2) NOT NULL,
    top_10_weight                  DECIMAL(5, 2) NOT NULL,
    largest_position_weight        DECIMAL(5, 2) NOT NULL,
    created_at                     TIMESTAMPTZ      DEFAULT NOW(),
    updated_at                     TIMESTAMPTZ      DEFAULT NOW(),

    UNIQUE (account_id, as_of_date)
);

-- =====================================================
-- MARKET GROUP
-- FX rates, interest rates, market holidays
-- =====================================================

CREATE TABLE market_rates
(
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    rate_type     VARCHAR(20)    NOT NULL,
    from_currency CHAR(3)        NOT NULL,
    to_currency   CHAR(3)        NOT NULL,
    rate          DECIMAL(12, 8) NOT NULL,
    rate_date     DATE           NOT NULL,
    data_source   data_source_enum DEFAULT 'calculated',
    created_at    TIMESTAMPTZ      DEFAULT NOW(),

    UNIQUE (rate_type, from_currency, to_currency, rate_date)
);

CREATE TABLE market_holidays
(
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    exchange        VARCHAR(20)  NOT NULL,
    country         CHAR(2)      NOT NULL,
    holiday_date    DATE         NOT NULL,
    holiday_name    VARCHAR(100) NOT NULL,
    is_full_closure BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ      DEFAULT NOW(),

    UNIQUE (exchange, holiday_date)
);

-- =====================================================
-- REFERENCE GROUP
-- Master data for currencies, countries, exchanges
-- =====================================================

CREATE TABLE reference_currencies
(
    id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    currency_code  CHAR(3) UNIQUE NOT NULL,
    name           VARCHAR(100)   NOT NULL,
    symbol         VARCHAR(5),
    decimal_places INTEGER DEFAULT 2,
    is_active      BOOLEAN          DEFAULT true,
    created_at     TIMESTAMPTZ      DEFAULT NOW()
);

CREATE TABLE reference_countries
(
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    country_code  CHAR(2) UNIQUE NOT NULL,
    country_name  VARCHAR(100)   NOT NULL,
    region        VARCHAR(50),
    currency_code CHAR(3),
    is_developed  BOOLEAN DEFAULT true,
    is_active     BOOLEAN          DEFAULT true,
    created_at    TIMESTAMPTZ      DEFAULT NOW()
);

CREATE TABLE reference_exchanges
(
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    exchange_code VARCHAR(10) UNIQUE NOT NULL,
    exchange_name VARCHAR(255)       NOT NULL,
    country_code  CHAR(2)            NOT NULL,
    currency_code CHAR(3)            NOT NULL,
    timezone      VARCHAR(50)        NOT NULL,
    market_open   TIME,
    market_close  TIME,
    is_active     BOOLEAN          DEFAULT true,
    created_at    TIMESTAMPTZ      DEFAULT NOW()
);

-- =====================================================
-- SYSTEM GROUP
-- Job processing, logging, health monitoring
-- =====================================================

CREATE TABLE system_jobs
(
    id                 UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id           UUID REFERENCES user_accounts (id) ON DELETE CASCADE,
    job_type          VARCHAR(50) NOT NULL,
    job_name          VARCHAR(255),
    status            VARCHAR(20) DEFAULT 'pending',
    priority          INTEGER     DEFAULT 50,
    total_records     INTEGER     DEFAULT 0,
    processed_records INTEGER     DEFAULT 0,
    failed_records    INTEGER     DEFAULT 0,
    error_message      TEXT,
    metadata          JSONB,
    started_at         TIMESTAMPTZ,
    completed_at       TIMESTAMPTZ,
    created_at        TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE system_logs
(
    id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    log_level  VARCHAR(10) NOT NULL,
    message    TEXT        NOT NULL,
    context    JSONB,
    user_id    UUID        REFERENCES user_accounts (id) ON DELETE SET NULL,
    source     VARCHAR(100),
    request_id VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE system_health
(
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15, 4) NOT NULL,
    metric_unit VARCHAR(20),
    component   VARCHAR(50),
    environment VARCHAR(20) DEFAULT 'production',
    recorded_at  TIMESTAMPTZ    NOT NULL,
    created_at   TIMESTAMPTZ      DEFAULT NOW()
);

-- =====================================================
-- CORPORATE ACTIONS (standalone group)
-- Stock splits, dividends, mergers affecting holdings
-- =====================================================

CREATE TABLE corporate_actions
(
    id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    security_id    UUID        NOT NULL REFERENCES security_master (id) ON DELETE CASCADE,
    action_type    VARCHAR(30) NOT NULL,
    ex_date        DATE        NOT NULL,
    effective_date DATE        NOT NULL,
    details        JSONB       NOT NULL,
    created_at     TIMESTAMPTZ      DEFAULT NOW()
);

CREATE TABLE corporate_dividends
(
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    security_id      UUID           NOT NULL REFERENCES security_master (id) ON DELETE CASCADE,
    ex_date          DATE           NOT NULL,
    pay_date         DATE           NOT NULL,
    amount_per_share DECIMAL(15, 6) NOT NULL,
    currency         CHAR(3)          DEFAULT 'USD',
    frequency        VARCHAR(20),
    dividend_type    VARCHAR(20)      DEFAULT 'regular',
    created_at       TIMESTAMPTZ      DEFAULT NOW()
);

-- =====================================================
-- INDEXES FOR PERFORMANCE
-- Organized by functional group
-- =====================================================

-- User management indexes
CREATE INDEX idx_user_accounts_email ON user_accounts (email);
CREATE INDEX idx_user_sessions_user_id ON user_sessions (user_id);
CREATE INDEX idx_user_sessions_refresh_token ON user_sessions (refresh_token);
CREATE INDEX idx_user_sessions_expires_at ON user_sessions (expires_at);

-- Data provider indexes
CREATE INDEX idx_data_providers_code ON data_providers (provider_code);
CREATE INDEX idx_data_providers_type ON data_providers (provider_type);
CREATE INDEX idx_data_connections_provider ON data_connections (provider_id);
CREATE INDEX idx_data_connections_status ON data_connections (status);
CREATE INDEX idx_data_mappings_connection_entity ON data_mappings (connection_id, entity_type);
CREATE INDEX idx_data_mappings_internal_id ON data_mappings (internal_id);

-- Counterparty indexes
CREATE INDEX idx_counterparty_master_code ON counterparty_master (counterparty_code);
CREATE INDEX idx_counterparty_master_type ON counterparty_master (counterparty_type);

-- Security indexes
CREATE INDEX idx_security_master_symbol ON security_master (symbol);
CREATE INDEX idx_security_master_provider ON security_master (primary_data_provider_id);
CREATE INDEX idx_security_identifiers_type_value ON security_identifiers (identifier_type, identifier_value);
CREATE INDEX idx_security_prices_security_date ON security_prices (security_id, price_date DESC);
CREATE INDEX idx_security_prices_provider ON security_prices (data_provider_id);

-- Benchmark indexes
CREATE INDEX idx_benchmark_master_symbol ON benchmark_master (symbol);
CREATE INDEX idx_benchmark_master_provider ON benchmark_master (data_provider_id);
CREATE INDEX idx_benchmark_prices_benchmark_date ON benchmark_prices (benchmark_id, price_date DESC);
CREATE INDEX idx_benchmark_prices_provider ON benchmark_prices (data_provider_id);

-- Portfolio indexes
CREATE INDEX idx_portfolio_accounts_user_id ON portfolio_accounts (user_id);
CREATE INDEX idx_portfolio_accounts_data_connection ON portfolio_accounts (data_connection_id);
CREATE INDEX idx_portfolio_holdings_account_security ON portfolio_holdings (account_id, security_id);
CREATE INDEX idx_portfolio_holdings_date ON portfolio_holdings (as_of_date DESC);
CREATE INDEX idx_portfolio_holdings_counterparty ON portfolio_holdings (counterparty_id);
CREATE INDEX idx_portfolio_transactions_account ON portfolio_transactions (account_id);
CREATE INDEX idx_portfolio_transactions_date ON portfolio_transactions (trade_date DESC);
CREATE INDEX idx_portfolio_transactions_security ON portfolio_transactions (security_id);
CREATE INDEX idx_portfolio_transactions_counterparty ON portfolio_transactions (counterparty_id);

-- Analytics indexes
CREATE INDEX idx_analytics_summary_account_date ON analytics_summary (account_id, as_of_date DESC);
CREATE INDEX idx_analytics_summary_user_date ON analytics_summary (account_id) INCLUDE (as_of_date, market_value);
CREATE INDEX idx_analytics_performance_account_date ON analytics_performance (account_id, as_of_date DESC);
CREATE INDEX idx_analytics_risk_account_date ON analytics_risk (account_id, as_of_date DESC);
CREATE INDEX idx_analytics_exposure_account_date ON analytics_exposure (account_id, as_of_date DESC);

-- Market data indexes
CREATE INDEX idx_market_rates_type_currencies_date ON market_rates (rate_type, from_currency, to_currency, rate_date DESC);

-- System indexes
CREATE INDEX idx_system_jobs_user_status ON system_jobs (user_id, status);
CREATE INDEX idx_system_jobs_created_at ON system_jobs (created_at DESC);
CREATE INDEX idx_system_logs_level_created ON system_logs (log_level, created_at DESC);
CREATE INDEX idx_system_logs_user_created ON system_logs (user_id, created_at DESC);

-- =====================================================
-- TRIGGERS FOR AUTOMATIC TIMESTAMP UPDATES
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

-- User management triggers
CREATE TRIGGER update_user_accounts_updated_at
    BEFORE UPDATE
    ON user_accounts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_subscriptions_updated_at
    BEFORE UPDATE
    ON user_subscriptions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Data provider triggers
CREATE TRIGGER update_data_providers_updated_at
    BEFORE UPDATE
    ON data_providers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_data_connections_updated_at
    BEFORE UPDATE
    ON data_connections
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Counterparty triggers
CREATE TRIGGER update_counterparty_master_updated_at
    BEFORE UPDATE
    ON counterparty_master
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Security triggers
CREATE TRIGGER update_security_master_updated_at
    BEFORE UPDATE
    ON security_master
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Portfolio triggers
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

-- Analytics triggers
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
-- =====================================================

CREATE VIEW user_portfolio_summary AS
SELECT pa.user_id,
       a.as_of_date,
       pa.currency,
       SUM(a.market_value)          as total_market_value,
       SUM(a.cost_basis)            as total_cost_basis,
       SUM(a.cash_balance)          as total_cash_balance,
       SUM(a.unrealized_gain)       as total_unrealized_gain,
       SUM(a.realized_gain)         as total_realized_gain,
       CASE
           WHEN SUM(a.market_value) > 0 THEN
               SUM(a.daily_return * a.market_value) / SUM(a.market_value)
           ELSE 0 END               as weighted_daily_return,
       CASE
           WHEN SUM(a.market_value) > 0 THEN
               SUM(a.ytd_return * a.market_value) / SUM(a.market_value)
           ELSE 0 END               as weighted_ytd_return,
       SUM(a.equity_value)          as total_equity_value,
       SUM(a.debt_value)            as total_debt_value,
       SUM(a.fund_value)            as total_fund_value,
       SUM(a.cash_value)            as total_cash_value,
       SUM(a.other_value)           as total_other_value,
       SUM(a.domestic_value)        as total_domestic_value,
       SUM(a.international_value)   as total_international_value,
       COUNT(DISTINCT a.account_id) as account_count,
       SUM(a.holdings_count)        as total_holdings_count,
       MAX(a.last_price_date)       as latest_price_date
FROM analytics_summary a
         JOIN portfolio_accounts pa ON a.account_id = pa.id
WHERE pa.is_active = true
GROUP BY pa.user_id, a.as_of_date, pa.currency;

COMMIT;
