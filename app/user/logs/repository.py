from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, delete, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.user.logs.model import UserLog


class UserLogRepository:
    """CRUD operations for user activity audit logging."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_log(
        self,
        user_id: Optional[str],
        action: str,
        target_category: str,
        target_id: Optional[str] = None,
        description: Optional[str] = None,
        request_path: Optional[str] = None,
        request_method: Optional[str] = None,
        request_metadata: Optional[dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        status: str = "success",
        error_message: Optional[str] = None,
    ) -> UserLog:
        """Create a new audit log entry."""
        audit_log = UserLog(
            user_id=user_id,
            action=action,
            target_category=target_category,
            target_id=target_id,
            description=description,
            request_path=request_path,
            request_method=request_method,
            request_metadata=request_metadata,
            ip_address=ip_address,
            user_agent=user_agent,
            status=status,
            error_message=error_message,
        )

        self.db.add(audit_log)
        await self.db.commit()
        await self.db.refresh(audit_log)
        return audit_log

    async def log_user_action(
        self,
        user_id: str,
        action: str,
        description: str,
        target_category: str = "users",
        target_id: Optional[str] = None,
        metadata: Optional[dict] = None,
        ip_address: Optional[str] = None,
        status: str = "success",
    ) -> UserLog:
        """Convenience method for logging user actions."""
        return await self.create_log(
            user_id=user_id,
            action=action,
            target_category=target_category,
            target_id=target_id or user_id,
            description=description,
            request_metadata=metadata,
            ip_address=ip_address,
            status=status,
        )

    async def log_data_change(
        self,
        user_id: Optional[str],
        action: str,
        target_category: str,
        target_id: str,
        old_values: Optional[dict] = None,
        new_values: Optional[dict] = None,
        ip_address: Optional[str] = None,
    ) -> UserLog:
        """Log data changes with before/after values."""
        metadata = {}
        if old_values:
            metadata["old_values"] = old_values
        if new_values:
            metadata["new_values"] = new_values

        description = f"{action.title()} {target_category} {target_id}"

        return await self.create_log(
            user_id=user_id,
            action=action,
            target_category=target_category,
            target_id=target_id,
            description=description,
            request_metadata=metadata,
            ip_address=ip_address,
        )

    async def get_user_activity(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 50,
        action_filter: Optional[str] = None,
        target_category_filter: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[UserLog]:
        """Get user activity logs with filtering."""
        stmt = select(UserLog).where(UserLog.user_id == user_id)

        if action_filter:
            stmt = stmt.where(UserLog.action == action_filter)

        if target_category_filter:
            stmt = stmt.where(UserLog.target_category == target_category_filter)

        if start_date:
            stmt = stmt.where(UserLog.created_at >= start_date)

        if end_date:
            stmt = stmt.where(UserLog.created_at <= end_date)

        stmt = stmt.order_by(desc(UserLog.created_at)).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_resource_history(
        self,
        target_category: str,
        target_id: str,
        skip: int = 0,
        limit: int = 20,
        action_filter: Optional[str] = None,
    ) -> List[UserLog]:
        """Get history for a specific resource."""
        stmt = select(UserLog).where(
            and_(
                UserLog.target_category == target_category,
                UserLog.target_id == target_id,
            )
        )

        if action_filter:
            stmt = stmt.where(UserLog.action == action_filter)

        stmt = stmt.order_by(desc(UserLog.created_at)).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_system_activity(
        self,
        skip: int = 0,
        limit: int = 100,
        action_filter: Optional[str] = None,
        target_category_filter: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[UserLog]:
        """Get system-wide activity logs."""
        stmt = select(UserLog).options(joinedload(UserLog.user))

        if action_filter:
            stmt = stmt.where(UserLog.action == action_filter)

        if target_category_filter:
            stmt = stmt.where(UserLog.target_category == target_category_filter)

        if start_date:
            stmt = stmt.where(UserLog.created_at >= start_date)

        if end_date:
            stmt = stmt.where(UserLog.created_at <= end_date)

        stmt = stmt.order_by(desc(UserLog.created_at)).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().unique().all())

    async def get_login_history(
        self,
        user_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[UserLog]:
        """Get login/logout history."""
        stmt = select(UserLog).where(UserLog.action.in_(["login", "logout", "login_failed"]))

        if user_id:
            stmt = stmt.where(UserLog.user_id == user_id)

        if start_date:
            stmt = stmt.where(UserLog.created_at >= start_date)

        if end_date:
            stmt = stmt.where(UserLog.created_at <= end_date)

        stmt = stmt.order_by(desc(UserLog.created_at)).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_security_events(
        self,
        skip: int = 0,
        limit: int = 100,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[UserLog]:
        """Get security-related events."""
        security_actions = [
            "login_failed",
            "password_reset",
            "password_changed",
            "email_verified",
            "account_locked",
            "account_unlocked",
            "permission_changed",
            "role_changed",
            "suspicious_activity",
            "mfa_enabled",
            "mfa_disabled",
        ]

        stmt = select(UserLog).where(UserLog.action.in_(security_actions))

        if start_date:
            stmt = stmt.where(UserLog.created_at >= start_date)

        if end_date:
            stmt = stmt.where(UserLog.created_at <= end_date)

        stmt = stmt.order_by(desc(UserLog.created_at)).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_failed_actions(
        self,
        user_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[UserLog]:
        """Get failed/error actions for security monitoring."""
        stmt = select(UserLog).where(UserLog.status.in_(["failure", "error"]))

        if user_id:
            stmt = stmt.where(UserLog.user_id == user_id)

        if start_date:
            stmt = stmt.where(UserLog.created_at >= start_date)

        if end_date:
            stmt = stmt.where(UserLog.created_at <= end_date)

        stmt = stmt.order_by(desc(UserLog.created_at)).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_activity_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get activity statistics."""
        base_stmt = select(UserLog)

        if user_id:
            base_stmt = base_stmt.where(UserLog.user_id == user_id)

        if start_date:
            base_stmt = base_stmt.where(UserLog.created_at >= start_date)

        if end_date:
            base_stmt = base_stmt.where(UserLog.created_at <= end_date)

        # Total events
        total_stmt = select(func.count()).select_from(base_stmt.subquery())
        total_result = await self.db.execute(total_stmt)
        total_events = total_result.scalar() or 0

        # Events by action
        action_stmt = (
            select(UserLog.action, func.count().label("count"))
            .select_from(base_stmt.subquery())
            .group_by(UserLog.action)
            .order_by(desc("count"))
        )
        action_result = await self.db.execute(action_stmt)
        by_action = dict(action_result.fetchall())

        # Events by target category
        category_stmt = (
            select(UserLog.target_category, func.count().label("count"))
            .select_from(base_stmt.subquery())
            .group_by(UserLog.target_category)
            .order_by(desc("count"))
        )
        category_result = await self.db.execute(category_stmt)
        by_category = dict(category_result.fetchall())

        # Events by status
        status_stmt = (
            select(UserLog.status, func.count().label("count"))
            .select_from(base_stmt.subquery())
            .group_by(UserLog.status)
            .order_by(desc("count"))
        )
        status_result = await self.db.execute(status_stmt)
        by_status = dict(status_result.fetchall())

        # Unique users (if not filtered by user)
        unique_users = 0
        if not user_id:
            users_stmt = select(func.count(func.distinct(UserLog.user_id))).select_from(
                base_stmt.subquery()
            )
            users_result = await self.db.execute(users_stmt)
            unique_users = users_result.scalar() or 0

        return {
            "total_events": total_events,
            "unique_users": unique_users,
            "by_action": by_action,
            "by_target_category": by_category,
            "by_status": by_status,
            "date_range": {
                "start": start_date.isoformat() if start_date else None,
                "end": end_date.isoformat() if end_date else None,
            },
            "user_id": user_id,
        }

    async def get_daily_activity(
        self,
        start_date: date,
        end_date: date,
        user_id: Optional[str] = None,
    ) -> Dict[str, int]:
        """Get daily activity counts."""
        stmt = select(
            func.date(UserLog.created_at).label("activity_date"),
            func.count().label("count"),
        ).where(
            and_(
                func.date(UserLog.created_at) >= start_date,
                func.date(UserLog.created_at) <= end_date,
            )
        )

        if user_id:
            stmt = stmt.where(UserLog.user_id == user_id)

        stmt = stmt.group_by(func.date(UserLog.created_at)).order_by("activity_date")

        result = await self.db.execute(stmt)
        daily_counts = {}

        for row in result:
            daily_counts[row.activity_date.isoformat()] = row.count

        return daily_counts

    async def cleanup_old_logs(self, days_to_keep: int = 365) -> int:
        """
        Clean up audit logs older than specified days.

        WARNING: Only use this if you don't have compliance requirements.
        Many regulations require 7+ years of audit log retention.
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)

        # Count logs to be deleted
        count_stmt = select(func.count()).where(UserLog.created_at < cutoff_date)
        count_result = await self.db.execute(count_stmt)
        count_to_delete = count_result.scalar() or 0

        # Delete old logs
        delete_stmt = delete(UserLog).where(UserLog.created_at < cutoff_date)
        await self.db.execute(delete_stmt)
        await self.db.commit()

        return count_to_delete

    async def search_logs(
        self,
        search_term: str,
        skip: int = 0,
        limit: int = 50,
        user_id: Optional[str] = None,
    ) -> List[UserLog]:
        """Search audit logs by description, target_id, or request path."""
        stmt = select(UserLog).where(
            or_(
                UserLog.description.ilike(f"%{search_term}%"),
                UserLog.target_id.ilike(f"%{search_term}%"),
                UserLog.request_path.ilike(f"%{search_term}%"),
            )
        )

        if user_id:
            stmt = stmt.where(UserLog.user_id == user_id)

        stmt = stmt.order_by(desc(UserLog.created_at)).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_suspicious_activity(
        self,
        hours_window: int = 24,
        failed_login_threshold: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Detect suspicious activity patterns.

        Returns users with unusual activity (multiple failed logins, etc.)
        """
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_window)

        # Find users with multiple failed login attempts
        stmt = (
            select(
                UserLog.user_id,
                UserLog.ip_address,
                func.count().label("failed_attempts"),
            )
            .where(
                and_(
                    UserLog.action == "login_failed",
                    UserLog.created_at >= cutoff_time,
                )
            )
            .group_by(UserLog.user_id, UserLog.ip_address)
            .having(func.count() >= failed_login_threshold)
            .order_by(desc("failed_attempts"))
        )

        result = await self.db.execute(stmt)

        return [
            {
                "user_id": str(row.user_id) if row.user_id else "unknown",
                "ip_address": row.ip_address,
                "failed_attempts": row.failed_attempts,
            }
            for row in result
        ]
