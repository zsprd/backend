import csv
import io
from difflib import get_close_matches
from typing import Any, Callable, Dict, List, Optional

import pandas as pd

# --- Common column mapping for fallback parser ---
COMMON_FIELD_MAP = {
    "date": ["date", "transaction date", "trade date", "settlement date"],
    "type": ["type", "transaction type", "activity", "description"],
    "symbol": ["symbol", "investment", "asset", "securities", "ticker", "code", "asset code"],
    "quantity": ["quantity", "no. shares", "units", "shares", "qty"],
    "price": [
        "price",
        "share price",
        "unit price",
        "price per share",
        "share price (£)",
        "price (£)",
    ],
    "amount": ["amount", "total value", "value", "total", "total value (£)", "amount (£)"],
    "currency": ["currency", "ccy"],
}


# --- Helper: Fuzzy column matching ---
def find_column(header: List[str], candidates: List[str]) -> Optional[str]:
    header_lower = [h.lower().strip() for h in header]
    for candidate in candidates:
        matches = get_close_matches(candidate.lower(), header_lower, n=1, cutoff=0.8)
        if matches:
            return header[header_lower.index(matches[0])]
    # Try substring match
    for candidate in candidates:
        for h in header:
            if candidate.lower() in h.lower():
                return h
    return None


# --- Fallback normalization function ---
def normalize_row(row: Dict[str, Any], header: List[str]) -> Dict[str, Any]:
    norm = {}
    for field, candidates in COMMON_FIELD_MAP.items():
        col = find_column(header, candidates)
        value = row.get(col) if col else None
        if value is not None:
            value = value.strip()
        norm[field] = value
    # Parse date
    try:
        norm["date"] = (
            pd.to_datetime(norm["date"], dayfirst=True, errors="coerce").date()
            if norm["date"]
            else None
        )
    except Exception:
        norm["date"] = None
    # Parse numbers
    for num_field in ["quantity", "price", "amount"]:
        try:
            norm[num_field] = float(norm[num_field].replace(",", "")) if norm[num_field] else 0.0
        except Exception:
            norm[num_field] = 0.0
    # Normalize type
    if norm["type"]:
        t = norm["type"].lower()
        if "buy" in t or "purchase" in t:
            norm["type"] = "buy"
        elif "sell" in t or "sale" in t:
            norm["type"] = "sell"
        elif "dividend" in t:
            norm["type"] = "dividend"
        elif "fee" in t:
            norm["type"] = "fee"
        elif "interest" in t:
            norm["type"] = "interest"
        elif "deposit" in t:
            norm["type"] = "deposit"
        elif "withdraw" in t:
            norm["type"] = "withdrawal"
        else:
            norm["type"] = t
    norm["raw"] = row
    return norm


# --- Fallback parser for unknown formats ---
def fallback_csv_parser(csv_content: str) -> List[Dict[str, Any]]:
    reader = csv.DictReader(io.StringIO(csv_content))
    header = reader.fieldnames or []
    transactions = []
    for row in reader:
        norm = normalize_row(row, header)
        if norm["date"] is not None:
            transactions.append(norm)
    return transactions


# --- Format detection ---
def detect_format(header: List[str]) -> Optional[str]:
    header_lower = [h.lower().strip() for h in header]
    if "no. shares" in header_lower and "share price (£)" in header_lower:
        return "pension_investment_activity"
    if "pot" in header_lower and "amount (£)" in header_lower:
        return "pension_transfers_and_contributions"
    # Add more known format detections here
    return None


def parse_pension_investment_activity(csv_content: str) -> List[Dict[str, Any]]:
    """
    Parse CSV content from Pension-Investment-Activity.csv into a list of normalized transaction dicts.
    """
    transactions = []
    reader = csv.DictReader(io.StringIO(csv_content))
    for row in reader:
        t_type = row["Description"].strip().lower()
        symbol = row["Investment"].strip() if row["Investment"] != "CASH" else "CASH"
        # Normalize transaction type
        if t_type == "purchase":
            type_ = "buy"
        elif t_type == "sale":
            type_ = "sell"
        elif t_type == "fee":
            type_ = "fee"
        elif t_type == "interest":
            type_ = "interest"
        elif t_type == "dividend":
            type_ = "dividend"
        else:
            type_ = t_type
        # Parse date
        date = pd.to_datetime(row["Date"], dayfirst=False).date()
        # Parse quantity and amount
        qty = float(row["No. Shares"]) if row["No. Shares"] else 0.0
        price = float(row["Share Price (£)"]) if row["Share Price (£)"] else 0.0
        amount = float(row["Total Value (£)"]) if row["Total Value (£)"] else 0.0
        transactions.append(
            {
                "date": date,
                "symbol": symbol,
                "quantity": qty,
                "price": price,
                "amount": amount,
                "type": type_,
                "raw": row,
            }
        )
    return transactions


def parse_pension_transfers_and_contributions(csv_content: str) -> List[Dict[str, Any]]:
    """
    Parse CSV content from Pension-Transfers-and-Contributions.csv into a list of normalized cashflow transaction dicts.
    """
    transactions = []
    reader = csv.DictReader(io.StringIO(csv_content))
    for row in reader:
        # Only process rows for the main pension pot (ignore Unallocated Cash as it's just a transfer)
        pot = row["Pot"].strip()
        if pot != "My Pension":
            continue
        date = pd.to_datetime(row["Date"], dayfirst=True).date()
        amount = float(row["Amount (£)"])
        transactions.append(
            {
                "date": date,
                "symbol": "CASH",
                "quantity": 0.0,
                "price": 0.0,
                "amount": amount,
                "type": "deposit",
                "raw": row,
            }
        )
    return transactions


def parse_csv(csv_content: str, format_hint: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Dispatch to the correct parser based on format_hint, header detection, or fallback to a generic parser.
    """
    # Try format hint first
    if format_hint and format_hint in CSV_PARSERS:
        return CSV_PARSERS[format_hint](csv_content)
    # Try header detection
    reader = csv.DictReader(io.StringIO(csv_content))
    header = reader.fieldnames or []
    detected = detect_format(header)
    if detected and detected in CSV_PARSERS:
        return CSV_PARSERS[detected](csv_content)
    # Fallback to generic parser
    return fallback_csv_parser(csv_content)


# Registry for provider/format to parser function
CSV_PARSERS: Dict[str, Callable[[str], List[Dict[str, Any]]]] = {
    "pension_investment_activity": parse_pension_investment_activity,
    "pension_transfers_and_contributions": parse_pension_transfers_and_contributions,
}
