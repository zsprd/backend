# app/models/account.py
from sqlalchemy import Column, String, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
from app.models.enums import account_category, account_subtype_category


class Institution(BaseModel):
    __tablename__ = "institutions"
    
    name = Column(String(255), nullable=False)
    country = Column(String(2), nullable=False)  # ISO country code
    url = Column(String(255))
    logo = Column(String(500))  # URL to logo
    primary_color = Column(String(7))  # Hex color code
    
    # Plaid integration
    plaid_institution_id = Column(String(255), unique=True)
    supports_investments = Column(Boolean, default=False, nullable=False)
    supports_transactions = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    accounts = relationship("Account", back_populates="institution")
    
    def __repr__(self):
        return f"<Institution(id={self.id}, name={self.name})>"


class Account(BaseModel):
    __tablename__ = "accounts"
    
    # Foreign Keys
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    institution_id = Column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Account Details
    name = Column(String(255), nullable=False)
    official_name = Column(String(255))  # Official name from institution
    category = Column(account_category, nullable=False)  # Fixed: use account_category
    subtype = Column(account_subtype_category)  # Fixed: match database column name
    mask = Column(String(4))  # Last 4 digits of account number
    currency = Column(String(3), default="USD", nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # External Integration
    plaid_account_id = Column(String(255))  # Plaid account ID
    
    # Relationships
    user = relationship("User", back_populates="accounts")
    institution = relationship("Institution", back_populates="accounts")
    holdings = relationship("Holding", back_populates="account", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="account", cascade="all, delete-orphan")
    cash_transactions = relationship("CashTransaction", back_populates="account", cascade="all, delete-orphan")
    positions = relationship("Position", back_populates="account", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Account(id={self.id}, name={self.name}, category={self.category})>"