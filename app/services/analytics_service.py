import logging
from datetime import date, datetime, timedelta
from typing import Dict, List

from sqlalchemy import and_, desc, select
from sqlalchemy.orm import Session

from app.models.analytics.exposure import AnalyticsExposure
from app.models.analytics.performance import AnalyticsPerformance
from app.models.analytics.risk import AnalyticsRisk
from app.models.analytics.summary import AnalyticsSummary
from app.models.portfolios.account import PortfolioAccount
from app.models.portfolios.holding import PortfolioHolding
from app.utils.exposure_calculations import ExposureCalculations
from app.utils.performance_calculations import PerformanceCalculations
from app.utils.risk_calculations import RiskCalculations

logger = logging.getLogger(__name__)


class AnalyticsCalculationService:
    """
    Service for orchestrating analytics calculations and storing results.
    All calculation logic is delegated to utility modules.
    """

    def __init__(self, db: Session):
        self.db = db

    async def calculate_daily_portfolio_values(
        self, account_id: str, calculation_date: date
    ) -> bool:
        """
        Calculate and store daily portfolios value for an account.
        Delegates calculation to utility function.
        """
        try:
            account = (
                self.db.query(PortfolioAccount).filter(PortfolioAccount.id == account_id).first()
            )
            if not account:
                logger.error(f"Account {account_id} not found")
                return False

            holdings = self._get_holdings_as_of_date(account_id, calculation_date)
            if not holdings:
                logger.warning(f"No holdings found for account {account_id} on {calculation_date}")
                return False

            # Delegate calculation to utility
            market_value, cost_basis, cash_value = (
                await PerformanceCalculations.calculate_portfolio_values(
                    holdings, calculation_date, account.currency, self.db
                )
            )

            daily_return = await PerformanceCalculations.calculate_daily_return(
                account_id, calculation_date, market_value, self.db
            )

            daily_value = AnalyticsSummary(
                account_id=account_id,
                value_date=calculation_date,
                market_value=market_value,
                cost_basis=cost_basis,
                cash_value=cash_value,
                daily_return=daily_return,
                unrealized_pnl=market_value - cost_basis,
                currency=account.currency,
                calculation_source="holdings",
            )

            existing = (
                self.db.query(AnalyticsSummary)
                .filter(
                    and_(
                        AnalyticsSummary.account_id == account_id,
                        AnalyticsSummary.value_date == calculation_date,
                    )
                )
                .first()
            )

            if existing:
                existing.market_value = market_value
                existing.cost_basis = cost_basis
                existing.cash_value = cash_value
                existing.daily_return = daily_return
                existing.unrealized_pnl = market_value - cost_basis
                existing.updated_at = datetime.now()
            else:
                self.db.add(daily_value)

            self.db.commit()
            logger.info(
                f"Calculated daily value for account {account_id} on {calculation_date}: ${market_value}"
            )
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error calculating daily portfolios value for {account_id}: {str(e)}")
            return False

    async def calculate_performance_analytics(
        self, account_id: str, calculation_date: date, period_days: int = 730
    ) -> bool:
        """
        Calculate comprehensive performance analytics using utility module.
        """
        try:
            daily_values = self._get_daily_values_series(account_id, calculation_date, period_days)
            if len(daily_values) < 30:
                logger.warning(
                    f"Insufficient data for performance analytics: {len(daily_values)} days"
                )
                return False

            # Delegate calculation to utility
            performance_result = PerformanceCalculations.calculate_performance_metrics(
                daily_values, calculation_date, period_days, self.db
            )
            if not performance_result or not performance_result.get("success", True):
                logger.warning(f"Performance calculation failed for account {account_id}")
                return False

            performance_record = AnalyticsPerformance(
                account_id=account_id,
                calculation_date=calculation_date,
                period_days=period_days,
                **performance_result["metrics"],
                calculation_status="completed",
                time_series_data=performance_result.get("time_series_data", {}),
            )

            existing = (
                self.db.query(AnalyticsPerformance)
                .filter(
                    and_(
                        AnalyticsPerformance.account_id == account_id,
                        AnalyticsPerformance.calculation_date == calculation_date,
                    )
                )
                .first()
            )

            if existing:
                for field, value in performance_record.__dict__.items():
                    if not field.startswith("_") and field != "id":
                        setattr(existing, field, value)
                existing.updated_at = datetime.now()
            else:
                self.db.add(performance_record)

            self.db.commit()
            logger.info(f"Calculated performance analytics for account {account_id}")
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error calculating performance analytics for {account_id}: {str(e)}")
            error_record = AnalyticsPerformance(
                account_id=account_id,
                calculation_date=calculation_date,
                calculation_status="error",
                error_message=str(e)[:500],
            )
            self.db.add(error_record)
            self.db.commit()
            return False

    async def calculate_risk_analytics(self, account_id: str, calculation_date: date) -> bool:
        """
        Calculate comprehensive risk analytics using utility module.
        """
        try:
            daily_values = self._get_daily_values_series(account_id, calculation_date, 730)
            if len(daily_values) < 60:
                logger.warning(f"Insufficient data for risk analytics: {len(daily_values)} days")
                return False

            # Delegate calculation to utility
            risk_result = RiskCalculations.calculate_risk_metrics(
                daily_values, calculation_date, self.db
            )
            if not risk_result or not risk_result.get("success", True):
                logger.warning(f"Risk calculation failed for account {account_id}")
                return False

            risk_record = AnalyticsRisk(
                account_id=account_id,
                calculation_date=calculation_date,
                **risk_result["metrics"],
                calculation_status="completed",
            )

            existing = (
                self.db.query(AnalyticsRisk)
                .filter(
                    and_(
                        AnalyticsRisk.account_id == account_id,
                        AnalyticsRisk.calculation_date == calculation_date,
                    )
                )
                .first()
            )

            if existing:
                for field, value in risk_record.__dict__.items():
                    if not field.startswith("_") and field != "id":
                        setattr(existing, field, value)
                existing.updated_at = datetime.now()
            else:
                self.db.add(risk_record)

            self.db.commit()
            logger.info(f"Calculated risk analytics for account {account_id}")
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error calculating risk analytics for {account_id}: {str(e)}")
            return False

    async def calculate_exposure_analytics(self, account_id: str, calculation_date: date) -> bool:
        """
        Calculate exposure and allocation analytics using utility module.
        """
        try:
            holdings_data = await self._get_holdings_with_security_data(
                account_id, calculation_date
            )
            if not holdings_data:
                logger.warning(f"No holdings data for exposure analytics: account {account_id}")
                return False

            # Delegate calculation to utility
            exposure_result = ExposureCalculations.calculate_exposure_metrics(
                holdings_data, calculation_date, self.db
            )
            if not exposure_result or not exposure_result.get("success", True):
                logger.warning(f"Exposure calculation failed for account {account_id}")
                return False

            exposure_record = AnalyticsExposure(
                account_id=account_id,
                calculation_date=calculation_date,
                **exposure_result["metrics"],
                calculation_status="completed",
            )

            existing = (
                self.db.query(AnalyticsExposure)
                .filter(
                    and_(
                        AnalyticsExposure.account_id == account_id,
                        AnalyticsExposure.calculation_date == calculation_date,
                    )
                )
                .first()
            )

            if existing:
                for field, value in exposure_record.__dict__.items():
                    if not field.startswith("_") and field != "id":
                        setattr(existing, field, value)
                existing.updated_at = datetime.now()
            else:
                self.db.add(exposure_record)

            self.db.commit()
            logger.info(f"Calculated exposure analytics for account {account_id}")
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error calculating exposure analytics for {account_id}: {str(e)}")
            return False

    # Helper methods (unchanged, only data fetching/structuring)
    def _get_holdings_as_of_date(self, account_id: str, as_of_date: date) -> List[PortfolioHolding]:
        stmt = (
            select(PortfolioHolding)
            .where(
                and_(
                    PortfolioHolding.account_id == account_id,
                    PortfolioHolding.as_of_date <= as_of_date,
                    PortfolioHolding.quantity > 0,
                )
            )
            .order_by(desc(PortfolioHolding.as_of_date))
        )
        result = self.db.execute(stmt)
        holdings = list(result.scalars().all())
        latest_holdings = {}
        for holding in holdings:
            key = holding.security_id
            if key not in latest_holdings or holding.as_of_date > latest_holdings[key].as_of_date:
                latest_holdings[key] = holding
        return list(latest_holdings.values())

    def _get_daily_values_series(
        self, account_id: str, end_date: date, days_back: int
    ) -> List[AnalyticsSummary]:
        start_date = end_date - timedelta(days=days_back)
        stmt = (
            select(AnalyticsSummary)
            .where(
                and_(
                    AnalyticsSummary.account_id == account_id,
                    AnalyticsSummary.value_date >= start_date,
                    AnalyticsSummary.value_date <= end_date,
                )
            )
            .order_by(AnalyticsSummary.value_date)
        )
        result = self.db.execute(stmt)
        return list(result.scalars().all())

    async def _get_holdings_with_security_data(
        self, account_id: str, calculation_date: date
    ) -> List[Dict]:
        holdings = self._get_holdings_as_of_date(account_id, calculation_date)
        holdings_data = []
        for holding in holdings:
            if holding.security:
                holdings_data.append(
                    {
                        "symbol": holding.security.symbol,
                        "name": holding.security.name,
                        "security_type": holding.security.security_type,
                        "sector": holding.security.sector,
                        "industry": holding.security.industry,
                        "country": holding.security.country,
                        "currency": holding.security.currency,
                        "market_value": float(holding.market_value or 0),
                        "cost_basis": float(holding.cost_basis_total or 0),
                        "quantity": float(holding.quantity),
                    }
                )
        return holdings_data
