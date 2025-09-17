# GitHub Copilot Instructions for ZSPRD Portfolio Analytics Backend

## 🏢 Project Overview

**Domain**: Professional portfolio analytics platform for high-net-worth individuals
**Purpose**: Institutional-grade portfolio analytics with performance, risk, and allocation analysis
**Target Users**: HNWIs ($1M+), self-directed investors, small family offices
**Core Value**: Democratizing sophisticated financial analytics with transparent pricing and educational explanations

### Business Context

- **Asset Classes**: Equities (US & international), ETFs, Cash (USD/EUR/GBP), Crypto (BTC, ETH)
- **Core Features**: Portfolio tracking, performance analytics, risk analysis, asset allocation, transaction management
- **No Investment Advice**: We provide data and analytics only - never investment recommendations
- **Educational Focus**: All metrics explained in plain language with tooltips and help sections

## 🏗️ Technical Architecture

### Stack & Technologies

- **Backend**: FastAPI (Python 3.13+), SQLAlchemy 2.0+ ORM, Alembic migrations
- **Database**: PostgreSQL with UUID primary keys
- **Authentication**: JWT tokens with refresh mechanism
- **External APIs**: Alpha Vantage (market data), future integrations (Plaid, IBKR)
- **Analytics Libraries**: pandas, numpy, scipy, empyrical-reloaded, pyfolio-reloaded, scikit-learn
- **Development**: black, isort, flake8, pytest, mypy

### Feature-Based Architecture

```
app/
├── core/                   # Infrastructure (config, database, security)
├── shared/                 # Common utilities and schemas
├── auth/                   # Authentication & authorization
├── user/                   # User management domain
│   └── accounts/          # User profiles & settings
├── portfolio/             # Portfolio management domain
│   ├── accounts/          # Investment accounts
│   ├── holdings/          # Portfolio holdings
│   ├── transactions/      # Buy/sell transactions
│   └── aggregation/       # Cross-account calculations
├── analytics/             # Financial analytics domain
│   ├── summary/           # Portfolio summaries
│   ├── performance/       # Performance metrics
│   ├── risk/             # Risk analysis
│   ├── exposure/         # Asset allocation
│   └── benchmarks/       # Benchmark comparisons
├── security/             # Securities master data domain
│   ├── master/           # Security information
│   ├── prices/           # Market price data
│   └── identifiers/      # Security identifiers
└── provider/             # Data provider integrations
    ├── connections/      # Provider connections
    ├── institutions/     # Financial institutions
    └── integrations/     # API integrations
```

## 🎯 Development Patterns & Conventions

### Module Structure (Consistent across all features)

Each feature module follows this exact pattern:

```
feature_name/
├── __init__.py
├── model.py              # SQLAlchemy models
├── schema.py             # Pydantic schemas (input/output)
├── crud.py               # Database operations
├── service.py            # Business logic
├── router.py             # FastAPI endpoints
├── dependencies.py       # Feature-specific dependencies (optional)
└── enums.py              # Feature-specific enums (optional)
```

### Code Quality Standards

#### Python Style

- **Formatting**: Use `black` with default settings (88 char line length)
- **Import Sorting**: Use `isort` with black-compatible profile
- **Linting**: Use `flake8` with reasonable complexity limits
- **Type Hints**: Use type hints for all function parameters and return values
- **Docstrings**: Google-style docstrings for classes and public methods

#### Naming Conventions

- **Models**: PascalCase (e.g., `PortfolioAccount`, `AnalyticsSummary`)
- **Functions/Variables**: snake_case (e.g., `calculate_returns`, `user_id`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `MAX_HOLDINGS_PER_ACCOUNT`)
- **Enums**: Database values always lowercase, Python enum names uppercase
- **Files**: snake_case (e.g., `analytics_service.py`, `portfolio_account.py`)

### Database Patterns

#### Model Conventions

```
# Always inherit from BaseModel
class PortfolioAccount(BaseModel):
    __tablename__ = "portfolio_accounts"
    
    # UUID primary keys
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Foreign keys with proper constraints
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("user_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to the account owner"
    )
    
    # Enums for controlled vocabularies
    account_type: Mapped[str] = mapped_column(
        ACCOUNT_TYPE_ENUM, nullable=False, index=True
    )
    
    # Decimal for financial values
    market_value: Mapped[Decimal] = mapped_column(
        DECIMAL(15, 2), nullable=False
    )
```

#### CRUD Pattern

```
class CRUDPortfolioAccount(CRUDBase[PortfolioAccount, PortfolioAccountCreate, PortfolioAccountUpdate]):
    def get_by_user(self, db: Session, *, user_id: UUID) -> List[PortfolioAccount]:
        return db.query(self.model).filter(self.model.user_id == user_id).all()
    
    def get_active_by_user(self, db: Session, *, user_id: UUID) -> List[PortfolioAccount]:
        return db.query(self.model).filter(
            and_(self.model.user_id == user_id, self.model.is_active == True)
        ).all()

portfolio_account_crud = CRUDPortfolioAccount(PortfolioAccount)
```

### API Patterns

#### Authentication

- **JWT Required**: All endpoints except health checks require valid JWT
- **User Context**: Extract user_id from JWT `sub` claim
- **Dependencies**: Use `get_current_active_user` for authenticated endpoints

#### Request/Response

```
@router.get("/accounts/", response_model=List[PortfolioAccountResponse])
async def list_accounts(
    current_user: Annotated[UserAccount, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
) -> List[PortfolioAccountResponse]:
    """List user's portfolio accounts with pagination."""
    accounts = portfolio_account_crud.get_multi_by_user(
        db, user_id=current_user.id, skip=skip, limit=limit
    )
    return [PortfolioAccountResponse.model_validate(account) for account in accounts]
```

#### Error Handling

```
# Use HTTPException with clear messages
if not account:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Account with ID {account_id} not found"
    )

# For business logic errors
if account.user_id != current_user.id:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access denied to this account"
    )
```

### Service Layer Patterns

#### Business Logic Organization

```
class AnalyticsService:
    """Analytics business logic with dependency injection."""
    
    def __init__(self):
        self.portfolio_crud = portfolio_account_crud
        self.holdings_crud = portfolio_holdings_crud
        self.price_service = SecurityPriceService()
    
    async def calculate_portfolio_performance(
        self, db: Session, account_id: UUID, user_id: UUID
    ) -> PerformanceAnalytics:
        """Calculate comprehensive performance metrics."""
        # Validate ownership
        account = self.portfolio_crud.get(db, id=account_id)
        if not account or account.user_id != user_id:
            raise ValueError("Account not found or access denied")
        
        # Get holdings and transactions
        holdings = self.holdings_crud.get_by_account(db, account_id=account_id)
        
        # Perform calculations
        returns = self._calculate_returns(holdings)
        performance = PerformanceCalculations(returns)
        
        return PerformanceAnalytics(
            total_return=performance.total_return(),
            annualized_return=performance.annualized_return(),
            sharpe_ratio=performance.sharpe_ratio(),
            # ... other metrics
        )
```

## 💰 Financial Domain Knowledge

### Core Financial Concepts

#### Performance Metrics

```
# Returns calculation
daily_return = (current_value - previous_value) / previous_value
total_return = (final_value - initial_value) / initial_value
cagr = (final_value / initial_value) ** (1/years) - 1

# Risk-adjusted returns
sharpe_ratio = (portfolio_return - risk_free_rate) / portfolio_volatility
sortino_ratio = (portfolio_return - risk_free_rate) / downside_deviation
```

#### Risk Metrics

```
# Value at Risk (VaR) - 5% chance of losing more than this amount
var_95 = np.percentile(returns, 5)

# Conditional VaR (Expected Shortfall) - average loss when VaR is exceeded
cvar_95 = returns[returns <= var_95].mean()

# Maximum Drawdown - worst peak-to-trough decline
drawdown = (cumulative_returns / cumulative_returns.expanding().max()) - 1
max_drawdown = drawdown.min()
```

#### Portfolio Calculations

- **NAV Calculation**: Market value of holdings + cash - liabilities
- **Currency Conversion**: Always convert to user's base currency using FX rates
- **Cost Basis Tracking**: FIFO, LIFO, or average cost methods
- **Realized vs Unrealized**: Track gains/losses separately

### Asset Classes & Market Data

- **Equities**: Stocks, ETFs, ADRs with proper sector/region classification
- **Fixed Income**: Government bonds, corporate bonds, CDs
- **Alternatives**: REITs, commodities, crypto (limited scope)
- **Cash**: Money market funds, bank deposits in various currencies

## 🔒 Security & Authentication

### JWT Token Management

```
# Token structure
{
    "sub": "user_id_uuid",           # User ID
    "exp": timestamp,                # Expiration
    "iat": timestamp,                # Issued at
    "token_type": "access|refresh",  # Token type
    "session_id": "session_uuid"     # Session tracking
}

# Token validation
def verify_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except JWTError:
        return None
```

### User Context

```
# Always validate user ownership of resources
def validate_resource_ownership(resource: BaseModel, user_id: UUID) -> None:
    if hasattr(resource, 'user_id') and resource.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this resource"
        )
```

### Rate Limiting & Security

- **Auth Endpoints**: 5 attempts per 15 minutes for login
- **General API**: 100 requests per minute per user
- **Password Requirements**: 8+ chars, mixed case, numbers, special chars
- **Session Management**: Refresh token rotation, session revocation

## 📊 Performance & Optimization

### Database Optimization

```
# Use indexes for frequently queried columns
CREATE INDEX idx_portfolio_accounts_user_id ON portfolio_accounts (user_id);
CREATE INDEX idx_analytics_summary_account_date ON analytics_summary (account_id, as_of_date DESC);

# Optimize queries with proper joins
def get_portfolio_summary(db: Session, user_id: UUID):
    return db.query(PortfolioAccount)\
        .options(joinedload(PortfolioAccount.holdings))\
        .filter(PortfolioAccount.user_id == user_id)\
        .all()
```

### Caching Strategy

- **Market Data**: Cache price data for 1 hour during market hours
- **Analytics**: Cache complex calculations for 5 minutes
- **User Data**: Cache user profile for session duration
- **Static Data**: Cache security master data for 24 hours

### Performance Requirements

- **API Response**: <500ms p95 for dashboard queries
- **Analytics Calculation**: <2 seconds for portfolio up to 5k transactions
- **Data Import**: Handle CSV files up to 100MB
- **Concurrent Users**: Support 1000+ simultaneous users

## 🧪 Testing Patterns

### Unit Testing

```
@pytest.fixture
def sample_portfolio_account(db: Session) -> PortfolioAccount:
    account = PortfolioAccount(
        user_id=uuid4(),
        name="Test Account",
        account_type="investment",
        currency="USD"
    )
    db.add(account)
    db.commit()
    return account

def test_calculate_portfolio_value(db: Session, sample_portfolio_account):
    """Test portfolio value calculation."""
    # Test implementation with known data
    assert calculated_value == expected_value
```

### API Testing

```
def test_get_accounts_authenticated(client: TestClient, auth_headers: Dict[str, str]):
    """Test authenticated account retrieval."""
    response = client.get("/api/v1/portfolios/accounts/", headers=auth_headers)
    assert response.status_code == 200
    assert "accounts" in response.json()
```

## 🔄 Migration & Deployment

### Database Migrations

```
# Always use Alembic for schema changes
alembic revision --autogenerate -m "Add analytics summary table"
alembic upgrade head

# Include data migrations when needed
def upgrade():
    # Schema changes
    op.create_table(...)
    
    # Data migration
    connection = op.get_bind()
    connection.execute(text("UPDATE ..."))
```

### Environment Configuration

```
# Use environment-specific settings
class Settings(BaseSettings):
    # Required settings (no defaults)
    SECRET_KEY: str
    DATABASE_URL: str
    ALPHA_VANTAGE_API_KEY: str
    
    # Optional with defaults
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
    class Config:
        env_file = ".env"
```

## 📚 Common Patterns & Examples

### Financial Calculations

```
# Use empyrical library for standard metrics
import empyrical as ep

def calculate_performance_metrics(returns: pd.Series) -> Dict[str, float]:
    return {
        "total_return": ep.cum_returns_final(returns) * 100,
        "annual_return": ep.annual_return(returns) * 100,
        "volatility": ep.annual_volatility(returns) * 100,
        "sharpe_ratio": ep.sharpe_ratio(returns),
        "max_drawdown": ep.max_drawdown(returns) * 100,
        "calmar_ratio": ep.calmar_ratio(returns)
    }
```

### Data Import/Export

```
# Handle CSV imports with validation
def import_transactions_csv(file: UploadFile, user_id: UUID) -> ImportResult:
    df = pd.read_csv(file.file)
    
    # Validate required columns
    required_columns = ["symbol", "quantity", "price", "trade_date"]
    missing = set(required_columns) - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    
    # Process and validate data
    validated_transactions = []
    for _, row in df.iterrows():
        transaction = TransactionCreate(**row.to_dict())
        validated_transactions.append(transaction)
    
    return ImportResult(
        success=True,
        imported_count=len(validated_transactions),
        transactions=validated_transactions
    )
```

### Error Handling

```
# Custom exceptions for business logic
class InsufficientFundsError(Exception):
    """Raised when transaction would create negative cash balance."""
    pass

class InvalidSecurityError(Exception):
    """Raised when security symbol is not found or invalid."""
    pass

# Usage in services
def execute_trade(account_id: UUID, trade: TradeRequest) -> Trade:
    if trade.side == "sell" and current_position < trade.quantity:
        raise InsufficientFundsError("Insufficient shares for sale")
    
    security = get_security(trade.symbol)
    if not security:
        raise InvalidSecurityError(f"Security {trade.symbol} not found")
```

## 🎯 Key Development Guidelines

1. **Financial Accuracy**: Always validate calculations against known benchmarks
2. **Data Integrity**: Use database constraints and application validation
3. **Performance**: Cache expensive calculations, use database indexes
4. **Security**: Validate user ownership, sanitize inputs, use rate limiting
5. **Maintainability**: Follow consistent patterns, comprehensive testing
6. **User Experience**: Clear error messages, fast response times
7. **Documentation**: Explain financial concepts in plain language
8. **Compliance**: No investment advice, clear disclaimers

## 🚨 Important Notes

- **No Investment Advice**: We never provide recommendations, only data and analytics
- **Currency Consistency**: Always convert to user's base currency for display
- **Decimal Precision**: Use Decimal type for all financial calculations
- **Time Zones**: Store all timestamps in UTC, convert for display
- **Data Privacy**: User data isolation, proper access controls
- **Error Handling**: Graceful degradation, informative error messages
- **Rate Limits**: Respect external API limits, implement internal limits

---

This comprehensive guide ensures consistent, high-quality development practices across the ZSPRD portfolio analytics
platform. Always refer to existing code patterns and maintain consistency with established conventions.
