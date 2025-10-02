import traceback
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, delete, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.system.logs.model import SystemLog


class SystemLogRepository:
    """CRUD operations for system logging (errors, debugging, monitoring)."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_log(
        self,
        log_level: str,
        message: str,
        source: Optional[str] = None,
        category: Optional[str] = None,
        exception_type: Optional[str] = None,
        stack_trace: Optional[str] = None,
        context: Optional[dict] = None,
        request_id: Optional[str] = None,
        request_path: Optional[str] = None,
        request_method: Optional[str] = None,
        duration_ms: Optional[int] = None,
        environment: Optional[str] = None,
    ) -> SystemLog:
        """Create a new system log entry."""
        log = SystemLog(
            log_level=log_level.lower(),
            message=message,
            source=source,
            category=category,
            exception_type=exception_type,
            stack_trace=stack_trace,
            context=context,
            request_id=request_id,
            request_path=request_path,
            request_method=request_method,
            duration_ms=duration_ms,
            environment=environment,
        )

        self.db.add(log)
        await self.db.commit()
        await self.db.refresh(log)
        return log

    async def log_debug(
        self,
        message: str,
        source: Optional[str] = None,
        context: Optional[dict] = None,
        **kwargs,
    ) -> SystemLog:
        """Log debug information."""
        return await self.create_log(
            log_level="debug",
            message=message,
            source=source,
            context=context,
            **kwargs,
        )

    async def log_info(
        self,
        message: str,
        source: Optional[str] = None,
        context: Optional[dict] = None,
        **kwargs,
    ) -> SystemLog:
        """Log informational messages."""
        return await self.create_log(
            log_level="info",
            message=message,
            source=source,
            context=context,
            **kwargs,
        )

    async def log_warning(
        self,
        message: str,
        source: Optional[str] = None,
        context: Optional[dict] = None,
        **kwargs,
    ) -> SystemLog:
        """Log warnings."""
        return await self.create_log(
            log_level="warning",
            message=message,
            source=source,
            context=context,
            **kwargs,
        )

    async def log_error(
        self,
        message: str,
        exception: Optional[Exception] = None,
        source: Optional[str] = None,
        context: Optional[dict] = None,
        **kwargs,
    ) -> SystemLog:
        """Log errors with optional exception details."""
        exception_type = None
        stack_trace = None

        if exception:
            exception_type = type(exception).__name__
            stack_trace = traceback.format_exc()

            # Add exception details to context
            if context is None:
                context = {}
            context["exception_message"] = str(exception)

        return await self.create_log(
            log_level="error",
            message=message,
            source=source,
            exception_type=exception_type,
            stack_trace=stack_trace,
            context=context,
            **kwargs,
        )

    async def log_critical(
        self,
        message: str,
        exception: Optional[Exception] = None,
        source: Optional[str] = None,
        context: Optional[dict] = None,
        **kwargs,
    ) -> SystemLog:
        """Log critical errors."""
        exception_type = None
        stack_trace = None

        if exception:
            exception_type = type(exception).__name__
            stack_trace = traceback.format_exc()

            if context is None:
                context = {}
            context["exception_message"] = str(exception)

        return await self.create_log(
            log_level="critical",
            message=message,
            source=source,
            exception_type=exception_type,
            stack_trace=stack_trace,
            context=context,
            **kwargs,
        )

    async def log_performance(
        self,
        message: str,
        duration_ms: int,
        source: Optional[str] = None,
        context: Optional[dict] = None,
        **kwargs,
    ) -> SystemLog:
        """Log performance metrics."""
        return await self.create_log(
            log_level="info",
            message=message,
            source=source,
            category="performance",
            duration_ms=duration_ms,
            context=context,
            **kwargs,
        )

    async def get_logs(
        self,
        skip: int = 0,
        limit: int = 100,
        log_level: Optional[str] = None,
        source: Optional[str] = None,
        category: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> List[SystemLog]:
        """Get system logs with filtering."""
        stmt = select(SystemLog)

        if log_level:
            stmt = stmt.where(SystemLog.log_level == log_level.lower())

        if source:
            stmt = stmt.where(SystemLog.source == source)

        if category:
            stmt = stmt.where(SystemLog.category == category)

        if user_id:
            stmt = stmt.where(SystemLog.user_id == user_id)

        if request_id:
            stmt = stmt.where(SystemLog.request_id == request_id)

        if start_date:
            stmt = stmt.where(SystemLog.created_at >= start_date)

        if end_date:
            stmt = stmt.where(SystemLog.created_at <= end_date)

        stmt = stmt.order_by(desc(SystemLog.created_at)).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_errors(
        self,
        skip: int = 0,
        limit: int = 100,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        source: Optional[str] = None,
    ) -> List[SystemLog]:
        """Get error and critical logs."""
        stmt = select(SystemLog).where(SystemLog.log_level.in_(["error", "critical"]))

        if source:
            stmt = stmt.where(SystemLog.source == source)

        if start_date:
            stmt = stmt.where(SystemLog.created_at >= start_date)

        if end_date:
            stmt = stmt.where(SystemLog.created_at <= end_date)

        stmt = stmt.order_by(desc(SystemLog.created_at)).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_request_id(self, request_id: str) -> List[SystemLog]:
        """Get all logs for a specific request (for tracing)."""
        stmt = (
            select(SystemLog)
            .where(SystemLog.request_id == request_id)
            .order_by(SystemLog.created_at)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_recent_errors_by_source(
        self,
        hours: int = 24,
        min_count: int = 5,
    ) -> List[Dict[str, Any]]:
        """Get sources with frequent errors (for alerting)."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)

        stmt = (
            select(
                SystemLog.source,
                SystemLog.exception_type,
                func.count().label("error_count"),
            )
            .where(
                and_(
                    SystemLog.log_level.in_(["error", "critical"]),
                    SystemLog.created_at >= cutoff_time,
                )
            )
            .group_by(SystemLog.source, SystemLog.exception_type)
            .having(func.count() >= min_count)
            .order_by(desc("error_count"))
        )

        result = await self.db.execute(stmt)

        return [
            {
                "source": row.source or "unknown",
                "exception_type": row.exception_type or "unknown",
                "error_count": row.error_count,
            }
            for row in result
        ]

    async def get_slow_operations(
        self,
        threshold_ms: int = 1000,
        skip: int = 0,
        limit: int = 50,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[SystemLog]:
        """Get operations slower than threshold (performance monitoring)."""
        stmt = select(SystemLog).where(
            and_(
                SystemLog.duration_ms.isnot(None),
                SystemLog.duration_ms >= threshold_ms,
            )
        )

        if start_date:
            stmt = stmt.where(SystemLog.created_at >= start_date)

        if end_date:
            stmt = stmt.where(SystemLog.created_at <= end_date)

        stmt = stmt.order_by(desc(SystemLog.duration_ms)).offset(skip).limit(limit)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get system log statistics."""
        base_stmt = select(SystemLog)

        if start_date:
            base_stmt = base_stmt.where(SystemLog.created_at >= start_date)

        if end_date:
            base_stmt = base_stmt.where(SystemLog.created_at <= end_date)

        # Total logs
        total_stmt = select(func.count()).select_from(base_stmt.subquery())
        total_result = await self.db.execute(total_stmt)
        total_logs = total_result.scalar() or 0

        # Logs by level
        level_stmt = (
            select(SystemLog.log_level, func.count().label("count"))
            .select_from(base_stmt.subquery())
            .group_by(SystemLog.log_level)
            .order_by(desc("count"))
        )
        level_result = await self.db.execute(level_stmt)
        by_level = dict(level_result.fetchall())

        # Logs by source
        source_stmt = (
            select(SystemLog.source, func.count().label("count"))
            .select_from(base_stmt.subquery())
            .group_by(SystemLog.source)
            .order_by(desc("count"))
            .limit(10)
        )
        source_result = await self.db.execute(source_stmt)
        top_sources = dict(source_result.fetchall())

        # Logs by category
        category_stmt = (
            select(SystemLog.category, func.count().label("count"))
            .select_from(base_stmt.subquery())
            .group_by(SystemLog.category)
            .order_by(desc("count"))
        )
        category_result = await self.db.execute(category_stmt)
        by_category = dict(category_result.fetchall())

        # Error rate
        error_stmt = (
            select(func.count())
            .select_from(base_stmt.subquery())
            .where(SystemLog.log_level.in_(["error", "critical"]))
        )
        error_result = await self.db.execute(error_stmt)
        error_count = error_result.scalar() or 0
        error_rate = (error_count / total_logs * 100) if total_logs > 0 else 0

        return {
            "total_logs": total_logs,
            "error_count": error_count,
            "error_rate_percent": round(error_rate, 2),
            "by_level": by_level,
            "top_sources": top_sources,
            "by_category": by_category,
            "date_range": {
                "start": start_date.isoformat() if start_date else None,
                "end": end_date.isoformat() if end_date else None,
            },
        }

    async def search_logs(
        self,
        search_term: str,
        skip: int = 0,
        limit: int = 50,
    ) -> List[SystemLog]:
        """Search logs by message, source, or exception type."""
        stmt = select(SystemLog).where(
            or_(
                SystemLog.message.ilike(f"%{search_term}%"),
                SystemLog.source.ilike(f"%{search_term}%"),
                SystemLog.exception_type.ilike(f"%{search_term}%"),
            )
        )

        stmt = stmt.order_by(desc(SystemLog.created_at)).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def cleanup_old_logs(self, days_to_keep: int = 90) -> int:
        """
        Clean up system logs older than specified days.

        System logs can be cleaned more aggressively than user audit logs
        since they're primarily for debugging.
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)

        # Count logs to be deleted
        count_stmt = select(func.count()).where(SystemLog.created_at < cutoff_date)
        count_result = await self.db.execute(count_stmt)
        count_to_delete = count_result.scalar() or 0

        # Delete old logs
        delete_stmt = delete(SystemLog).where(SystemLog.created_at < cutoff_date)
        await self.db.execute(delete_stmt)
        await self.db.commit()

        return count_to_delete

    async def cleanup_debug_logs(self, days_to_keep: int = 7) -> int:
        """Clean up debug logs more aggressively (they accumulate quickly)."""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)

        count_stmt = select(func.count()).where(
            and_(
                SystemLog.log_level == "debug",
                SystemLog.created_at < cutoff_date,
            )
        )
        count_result = await self.db.execute(count_stmt)
        count_to_delete = count_result.scalar() or 0

        delete_stmt = delete(SystemLog).where(
            and_(
                SystemLog.log_level == "debug",
                SystemLog.created_at < cutoff_date,
            )
        )
        await self.db.execute(delete_stmt)
        await self.db.commit()

        return count_to_delete
