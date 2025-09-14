from typing import Any, Dict, List

import numpy as np
import pandas as pd


class ExposureCalculations:
    """
    Provides exposure and allocation analytics for a portfolios, including asset class, sector, country, region, currency, and position concentration metrics.
    Accepts a DataFrame or list of holdings with columns: symbol, name, security_type, sector, industry, country, currency, market_value, cost_basis, quantity.
    """

    def __init__(self, holdings_data: List[Dict[str, Any]]):
        self.df = pd.DataFrame(holdings_data)
        if self.df.empty:
            self.total_market_value = 0.0
        else:
            self.total_market_value = self.df["market_value"].sum()

    def allocation_by_asset_class(self) -> Dict[str, float]:
        if self.df.empty:
            return {}
        by_asset_class = self.df.groupby("security_type")["market_value"].sum()
        return {
            k: round((v / self.total_market_value) * 100, 2)
            for k, v in by_asset_class.to_dict().items()
        }

    def allocation_by_sector(self) -> Dict[str, float]:
        if self.df.empty:
            return {}
        equity_df = self.df[self.df["security_type"].isin(["equity", "etf"])]
        if equity_df.empty:
            return {}
        by_sector = equity_df.groupby("sector")["market_value"].sum()
        return {
            k: round((v / self.total_market_value) * 100, 2)
            for k, v in by_sector.to_dict().items()
            if k and pd.notna(k)
        }

    def allocation_by_country(self) -> Dict[str, float]:
        if self.df.empty:
            return {}
        by_country = self.df.groupby("country")["market_value"].sum()
        return {
            k: round((v / self.total_market_value) * 100, 2)
            for k, v in by_country.to_dict().items()
            if k and pd.notna(k)
        }

    def allocation_by_region(self) -> Dict[str, float]:
        if self.df.empty:
            return {}
        region_mapping = {
            "US": "North America",
            "CA": "North America",
            "MX": "North America",
            "GB": "Europe",
            "DE": "Europe",
            "FR": "Europe",
            "IT": "Europe",
            "JP": "Asia Pacific",
            "AU": "Asia Pacific",
            "SG": "Asia Pacific",
            "CN": "Asia Pacific",
            "HK": "Asia Pacific",
        }
        self.df["region"] = self.df["country"].map(region_mapping).fillna("Other")
        by_region = self.df.groupby("region")["market_value"].sum()
        return {
            k: round((v / self.total_market_value) * 100, 2) for k, v in by_region.to_dict().items()
        }

    def allocation_by_currency(self) -> Dict[str, float]:
        if self.df.empty:
            return {}
        by_currency = self.df.groupby("currency")["market_value"].sum()
        return {
            k: round((v / self.total_market_value) * 100, 2)
            for k, v in by_currency.to_dict().items()
        }

    def concentration_metrics(self) -> Dict[str, float]:
        if self.df.empty or self.total_market_value == 0:
            return {
                "top_5_weight": 0.0,
                "top_10_weight": 0.0,
                "largest_position_weight": 0.0,
                "herfindahl_index": 0.0,
                "effective_positions": 0.0,
            }
        weights = (self.df["market_value"] / self.total_market_value).sort_values(ascending=False)
        herfindahl = float(np.sum(weights**2))
        effective_positions = float(1 / herfindahl) if herfindahl > 0 else 0.0
        return {
            "top_5_weight": float(np.sum(weights[:5]) * 100),
            "top_10_weight": float(np.sum(weights[:10]) * 100),
            "largest_position_weight": float(weights.iloc[0] * 100),
            "herfindahl_index": herfindahl,
            "effective_positions": effective_positions,
        }

    def top_holdings_table(self, n: int = 10) -> List[Dict[str, Any]]:
        if self.df.empty:
            return []
        df_sorted = self.df.sort_values("market_value", ascending=False).head(n)
        return [
            {
                "symbol": row["symbol"],
                "name": row["name"],
                "weight": (
                    round((row["market_value"] / self.total_market_value) * 100, 2)
                    if self.total_market_value > 0
                    else 0.0
                ),
                "market_value": float(row["market_value"]),
                "sector": row["sector"],
                "country": row["country"],
            }
            for _, row in df_sorted.iterrows()
        ]

    def all_exposure_analytics(self) -> Dict[str, Any]:
        return {
            "allocation_by_asset_class": self.allocation_by_asset_class(),
            "allocation_by_sector": self.allocation_by_sector(),
            "allocation_by_country": self.allocation_by_country(),
            "allocation_by_region": self.allocation_by_region(),
            "allocation_by_currency": self.allocation_by_currency(),
            "concentration_metrics": self.concentration_metrics(),
            "top_holdings": self.top_holdings_table(),
        }
