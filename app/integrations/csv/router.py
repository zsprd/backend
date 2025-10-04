"""
CSV Import Router

Provides endpoints for CSV template downloads and import information.
"""

import io
from typing import Literal

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/csv", tags=["CSV Import"])


@router.get("/templates/{template_type}")
async def download_csv_template(
    template_type: Literal["transactions", "holdings"],
) -> StreamingResponse:
    """
    Download CSV template for transactions or holdings import.

    Args:
        template_type: Type of template to download

    Returns:
        CSV file download
    """

    if template_type == "transactions":
        csv_content = """date,type,symbol,quantity,price,fees,currency,description
2024-01-15,buy,AAPL,100,150.00,9.99,USD,Apple stock purchase
2024-01-20,sell,MSFT,50,380.00,9.99,USD,Microsoft partial sale
2024-02-01,dividend,AAPL,0,75.00,0,USD,Q1 2024 dividend
2024-02-15,deposit,,,10000.00,0,USD,Monthly contribution
2024-03-01,buy,SPY,25,450.00,4.99,USD,S&P 500 ETF purchase
2024-03-10,fee,,,50.00,0,USD,Account maintenance fee"""
        filename = "transactions_template.csv"

    else:  # holdings
        csv_content = """date,symbol,quantity,cost_basis,currency
2024-01-01,AAPL,100,145.00,USD
2024-01-01,MSFT,75,350.00,USD
2024-01-01,SPY,50,425.00,USD
2024-01-01,QQQ,30,380.00,USD
2024-01-01,CASH,15000.00,,USD"""
        filename = "holdings_template.csv"

    # Create file-like object
    output = io.StringIO()
    output.write(csv_content)
    output.seek(0)

    # Return as downloadable file
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/template-info/{template_type}")
async def get_template_info(template_type: Literal["transactions", "holdings"]) -> dict:
    """
    Get information about CSV template structure and requirements.

    Args:
        template_type: Type of template

    Returns:
        Template documentation
    """

    if template_type == "transactions":
        return {
            "template_type": "transactions",
            "description": "Import transaction history for a account account",
            "required_columns": ["date", "type"],
            "optional_columns": ["symbol", "quantity", "price", "fees", "currency", "description"],
            "valid_transaction_types": [
                "buy",
                "sell",
                "dividend",
                "interest",
                "fee",
                "deposit",
                "withdrawal",
                "transfer_in",
                "transfer_out",
                "split",
                "spinoff",
            ],
            "date_formats": [
                "YYYY-MM-DD (preferred)",
                "MM/DD/YYYY",
                "DD/MM/YYYY",
                "MM-DD-YYYY",
                "DD-MM-YYYY",
            ],
            "notes": [
                "Symbol is required for buy/sell/dividend transactions",
                "Quantity and price should be positive numbers",
                "Currency defaults to account currency if not specified",
                "System will attempt to match or create securities automatically",
            ],
            "example_rows": [
                {
                    "date": "2024-01-15",
                    "type": "buy",
                    "symbol": "AAPL",
                    "quantity": "100",
                    "price": "150.00",
                    "fees": "9.99",
                    "currency": "USD",
                    "description": "Apple stock purchase",
                },
                {
                    "date": "2024-02-01",
                    "type": "dividend",
                    "symbol": "AAPL",
                    "quantity": "0",
                    "price": "75.00",
                    "fees": "0",
                    "currency": "USD",
                    "description": "Q1 2024 dividend",
                },
            ],
        }

    else:  # holdings
        return {
            "template_type": "holdings",
            "description": "Import current account holdings/positions",
            "required_columns": ["date", "symbol", "quantity"],
            "optional_columns": ["cost_basis", "currency"],
            "date_formats": [
                "YYYY-MM-DD (preferred)",
                "MM/DD/YYYY",
                "DD/MM/YYYY",
                "MM-DD-YYYY",
                "DD-MM-YYYY",
            ],
            "notes": [
                "All holdings should have positive quantities",
                "Cost basis is the per-share/unit cost",
                "Currency defaults to account currency if not specified",
                "Use 'CASH' as symbol for cash positions",
                "System will attempt to match or create securities automatically",
            ],
            "example_rows": [
                {
                    "date": "2024-01-01",
                    "symbol": "AAPL",
                    "quantity": "100",
                    "cost_basis": "145.00",
                    "currency": "USD",
                },
                {
                    "date": "2024-01-01",
                    "symbol": "CASH",
                    "quantity": "15000.00",
                    "cost_basis": "",
                    "currency": "USD",
                },
            ],
        }


@router.get("/supported-formats")
async def get_supported_formats() -> dict:
    """
    Get list of supported CSV formats and transaction types.

    Returns:
        Supported formats documentation
    """

    return {
        "file_requirements": {
            "format": "CSV (Comma-Separated Values)",
            "encoding": "UTF-8",
            "max_size_mb": 10,
            "max_rows": 10000,
        },
        "transaction_types": {
            "buy": "Purchase of securities",
            "sell": "Sale of securities",
            "dividend": "Dividend payment received",
            "interest": "Interest payment received",
            "fee": "Account or transaction fees",
            "deposit": "Cash deposit into account",
            "withdrawal": "Cash withdrawal from account",
            "transfer_in": "Securities transferred into account",
            "transfer_out": "Securities transferred out of account",
            "split": "Stock split",
            "spinoff": "Corporate spinoff",
        },
        "supported_currencies": [
            "USD",
            "EUR",
            "GBP",
            "JPY",
            "CAD",
            "AUD",
            "CHF",
            "CNY",
            "HKD",
            "SGD",
            "NZD",
            "SEK",
            "NOK",
            "DKK",
        ],
        "security_types": {
            "equity": "Stocks and shares",
            "fund": "ETFs and mutual funds",
            "crypto": "Cryptocurrencies",
            "cash": "Cash and money market",
            "bond": "Bonds and fixed income",
        },
        "tips": [
            "Always validate your CSV before importing",
            "Use standard ticker symbols for best matching",
            "Import transactions in chronological order",
            "Keep backups of your original files",
            "Start with small test imports first",
        ],
    }
