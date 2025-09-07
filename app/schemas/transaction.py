from typing import Optional, List
from pydantic import BaseModel, Field, UUID4
from datetime import datetime, date
from decimal import Decimal
from app.models.enums import TransactionType, TransactionSide, CashTransactionType


# Basic security info for nested responses
class SecurityBasicInfo(BaseModel):
    id: UUID4
    symbol: str
    name: str
    type: str
    currency: str
    
    class Config:
        from_attributes = True


# Transaction Schemas
class TransactionBase(BaseModel):
    type: TransactionType = Field(..., description="Transaction type")
    side: Optional[TransactionSide] = Field(None, description="Buy or sell side")
    quantity: Optional[Decimal] = Field(None, description="Quantity of securities")
    price: Optional[Decimal] = Field(None, description="Price per unit")
    amount: Decimal = Field(..., description="Total transaction amount")
    fees: Optional[Decimal] = Field(None, description="Transaction fees")
    tax: Optional[Decimal] = Field(None, description="Tax amount")
    trade_date: date = Field(..., description="Trade execution date")
    settlement_date: Optional[date] = Field(None, description="Settlement date")
    transaction_currency: str = Field(..., max_length=3, description="Transaction currency")
    fx_rate: Optional[Decimal] = Field(None, description="FX rate if currency conversion")
    description: Optional[str] = Field(None, description="Transaction description")
    memo: Optional[str] = Field(None, description="Additional notes")
    category: Optional[str] = Field(None, description="Transaction category")
    subcategory: Optional[str] = Field(None, description="Transaction subcategory")


class TransactionCreate(TransactionBase):
    account_id: UUID4 = Field(..., description="Account ID")
    security_id: Optional[UUID4] = Field(None, description="Security ID (if applicable)")
    plaid_transaction_id: Optional[str] = Field(None, description="Plaid transaction ID")
    source: str = Field("manual", description="Data source")


class TransactionUpdate(BaseModel):
    type: Optional[TransactionType] = None
    side: Optional[TransactionSide] = None
    quantity: Optional[Decimal] = None
    price: Optional[Decimal] = None
    amount: Optional[Decimal] = None
    fees: Optional[Decimal] = None
    tax: Optional[Decimal] = None
    trade_date: Optional[date] = None
    settlement_date: Optional[date] = None
    transaction_currency: Optional[str] = None
    fx_rate: Optional[Decimal] = None
    description: Optional[str] = None
    memo: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None


class Transaction(TransactionBase):
    id: UUID4
    account_id: UUID4
    security_id: Optional[UUID4]
    plaid_transaction_id: Optional[str]
    source: str
    created_at: datetime
    updated_at: datetime
    
    # Nested relationships
    security: Optional[SecurityBasicInfo] = None
    
    class Config:
        from_attributes = True


class TransactionWithMetrics(Transaction):
    """Transaction with calculated metrics"""
    realized_gain_loss: Optional[float] = Field(None, description="Realized gain/loss")
    portfolio_impact: Optional[float] = Field(None, description="Impact on portfolio value")
    amount_base_currency: Optional[float] = Field(None, description="Amount in base currency")


# Cash Transaction Schemas
class CashTransactionBase(BaseModel):
    type: CashTransactionType = Field(..., description="Cash transaction type")
    amount: Decimal = Field(..., description="Transaction amount")
    description: Optional[str] = Field(None, description="Transaction description")
    category: Optional[str] = Field(None, description="Transaction category")
    merchant_name: Optional[str] = Field(None, description="Merchant name")
    date: date = Field(..., description="Transaction date")
    pending: bool = Field(False, description="Is transaction pending")


class CashTransactionCreate(CashTransactionBase):
    account_id: UUID4 = Field(..., description="Account ID")
    plaid_transaction_id: Optional[str] = Field(None, description="Plaid transaction ID")
    plaid_category: Optional[List[str]] = Field(None, description="Plaid categories")


class CashTransactionUpdate(BaseModel):
    type: Optional[CashTransactionType] = None
    amount: Optional[Decimal] = None
    description: Optional[str] = None
    category: Optional[str] = None
    merchant_name: Optional[str] = None
    date: Optional[date] = None
    pending: Optional[bool] = None


class CashTransaction(CashTransactionBase):
    id: UUID4
    account_id: UUID4
    plaid_transaction_id: Optional[str]
    plaid_category: Optional[List[str]]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Bulk Operations
class BulkTransactionCreate(BaseModel):
    """Schema for bulk transaction creation"""
    transactions: List[TransactionCreate] = Field(..., description="List of transactions to create")
    validate_balances: bool = Field(True, description="Validate account balances")


class BulkTransactionResponse(BaseModel):
    """Response for bulk transaction operations"""
    created_count: int
    error_count: int
    errors: List[str] = []
    transactions: List[Transaction] = []


# Transaction Analysis
class TransactionsSummary(BaseModel):
    """Summary of transactions for a period"""
    total_transactions: int
    total_invested: float
    total_withdrawn: float
    net_flow: float
    total_fees: float
    total_dividends: float
    realized_gains: float
    realized_losses: float
    base_currency: str
    period_start: date
    period_end: date
    
    by_type: dict = Field(default_factory=dict, description="Breakdown by transaction type")
    by_month: dict = Field(default_factory=dict, description="Monthly breakdown")
    by_security: dict = Field(default_factory=dict, description="Breakdown by security")


# Transaction Filters
class TransactionFilter(BaseModel):
    """Filter parameters for transaction queries"""
    account_ids: Optional[List[UUID4]] = None
    security_ids: Optional[List[UUID4]] = None
    transaction_types: Optional[List[TransactionType]] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    currencies: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    search_text: Optional[str] = None


class TransactionsList(BaseModel):
    """Paginated transactions list response"""
    transactions: List[TransactionWithMetrics]
    total: int
    skip: int
    limit: int
    summary: TransactionsSummary


# CSV Import/Export
class TransactionImportRow(BaseModel):
    """Schema for CSV transaction import"""
    account_name: str
    trade_date: str  # Will be parsed to date
    symbol: Optional[str] = None
    transaction_type: str
    side: Optional[str] = None
    quantity: Optional[str] = None
    price: Optional[str] = None
    amount: str
    fees: Optional[str] = None
    currency: str = "USD"
    description: Optional[str] = None


class TransactionImportResult(BaseModel):
    """Result of transaction import operation"""
    total_rows: int
    successful_imports: int
    failed_imports: int
    errors: List[dict] = []
    imported_transactions: List[Transaction] = []


# Performance Metrics
class SecurityPerformance(BaseModel):
    """Performance metrics for a specific security"""
    security_id: UUID4
    symbol: str
    name: str
    total_invested: float
    current_value: float
    realized_gain_loss: float
    unrealized_gain_loss: float
    total_return: float
    total_return_percent: float
    holding_period_days: int
    annualized_return: Optional[float] = None


class PortfolioPerformance(BaseModel):
    """Overall portfolio performance from transactions"""
    total_invested: float
    total_withdrawn: float
    net_contributions: float
    current_value: float
    total_return: float
    total_return_percent: float
    annualized_return: Optional[float] = None
    time_weighted_return: Optional[float] = None
    money_weighted_return: Optional[float] = None
    
    securities: List[SecurityPerformance] = []