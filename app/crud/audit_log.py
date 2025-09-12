from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, and_, desc, func, extract
from datetime import datetime, timezone, date, timedelta
from decimal import Decimal

from app.crud.base import CRUDBase
from app.models.audit_log import AuditLog


class CRUDAuditLog(CRUDBase[AuditLog, None, None]):
    """CRUD operations for AuditLog model."""

    def create_log(
        self,
        db: Session,
        *,
        user_id: Optional[str],
        action: str,
        target_category: str,
        target_id: Optional[str] = None,
        description: Optional[str] = None,
        request_path: Optional[str] = None,
        request_method: Optional[str] = None,
        request_metadata: Optional[dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """Create a new audit log entry."""
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            target_category=target_category,
            target_id=target_id,
            description=description,
            request_path=request_path,
            request_method=request_method,
            request_metadata=request_metadata,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        db.add(audit_log)
        db.commit()
        db.refresh(audit_log)
        return audit_log

    def log_user_action(
        self,
        db: Session,
        *,
        user_id: str,
        action: str,
        description: str,
        target_category: str = "user",
        target_id: Optional[str] = None,
        metadata: Optional[dict] = None,
        ip_address: Optional[str] = None
    ) -> AuditLog:
        """Convenience method for logging user actions."""
        return self.create_log(
            db,
            user_id=user_id,
            action=action,
            target_category=target_category,
            target_id=target_id or user_id,
            description=description,
            request_metadata=metadata,
            ip_address=ip_address
        )

    def log_data_change(
        self,
        db: Session,
        *,
        user_id: Optional[str],
        action: str,
        target_category: str,
        target_id: str,
        old_values: Optional[dict] = None,
        new_values: Optional[dict] = None,
        ip_address: Optional[str] = None
    ) -> AuditLog:
        """Log data changes with before/after values."""
        metadata = {}
        if old_values:
            metadata["old_values"] = old_values
        if new_values:
            metadata["new_values"] = new_values
        
        description = f"{action.title()} {target_category} {target_id}"
        
        return self.create_log(
            db,
            user_id=user_id,
            action=action,
            target_category=target_category,
            target_id=target_id,
            description=description,
            request_metadata=metadata,
            ip_address=ip_address
        )

    def get_user_activity(
        self,
        db: Session,
        *,
        user_id: str,
        skip: int = 0,
        limit: int = 50,
        action_filter: Optional[str] = None,
        target_category_filter: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[AuditLog]:
        """Get user activity logs with filtering."""
        stmt = select(AuditLog).where(AuditLog.user_id == user_id)
        
        if action_filter:
            stmt = stmt.where(AuditLog.action == action_filter)
        
        if target_category_filter:
            stmt = stmt.where(AuditLog.target_category == target_category_filter)
        
        if start_date:
            stmt = stmt.where(AuditLog.created_at >= start_date)
        
        if end_date:
            stmt = stmt.where(AuditLog.created_at <= end_date)
        
        stmt = stmt.order_by(desc(AuditLog.created_at)).offset(skip).limit(limit)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def get_resource_history(
        self,
        db: Session,
        *,
        target_category: str,
        target_id: str,
        skip: int = 0,
        limit: int = 20,
        action_filter: Optional[str] = None
    ) -> List[AuditLog]:
        """Get history for a specific resource."""
        stmt = select(AuditLog).where(
            and_(
                AuditLog.target_category == target_category,
                AuditLog.target_id == target_id
            )
        )
        
        if action_filter:
            stmt = stmt.where(AuditLog.action == action_filter)
        
        stmt = stmt.order_by(desc(AuditLog.created_at)).offset(skip).limit(limit)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def get_system_activity(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        action_filter: Optional[str] = None,
        target_category_filter: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[AuditLog]:
        """Get system-wide activity logs."""
        stmt = select(AuditLog).options(joinedload(AuditLog.user))
        
        if action_filter:
            stmt = stmt.where(AuditLog.action == action_filter)
        
        if target_category_filter:
            stmt = stmt.where(AuditLog.target_category == target_category_filter)
        
        if start_date:
            stmt = stmt.where(AuditLog.created_at >= start_date)
        
        if end_date:
            stmt = stmt.where(AuditLog.created_at <= end_date)
        
        stmt = stmt.order_by(desc(AuditLog.created_at)).offset(skip).limit(limit)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def get_login_history(
        self,
        db: Session,
        *,
        user_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[AuditLog]:
        """Get login/logout history."""
        stmt = select(AuditLog).where(
            AuditLog.action.in_(['login', 'logout', 'login_failed'])
        )
        
        if user_id:
            stmt = stmt.where(AuditLog.user_id == user_id)
        
        if start_date:
            stmt = stmt.where(AuditLog.created_at >= start_date)
        
        if end_date:
            stmt = stmt.where(AuditLog.created_at <= end_date)
        
        stmt = stmt.order_by(desc(AuditLog.created_at)).offset(skip).limit(limit)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def get_security_events(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[AuditLog]:
        """Get security-related events."""
        security_actions = [
            'login_failed', 'password_reset', 'password_changed',
            'email_verified', 'account_locked', 'suspicious_activity'
        ]
        
        stmt = select(AuditLog).where(AuditLog.action.in_(security_actions))
        
        if start_date:
            stmt = stmt.where(AuditLog.created_at >= start_date)
        
        if end_date:
            stmt = stmt.where(AuditLog.created_at <= end_date)
        
        stmt = stmt.order_by(desc(AuditLog.created_at)).offset(skip).limit(limit)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def get_activity_statistics(
        self,
        db: Session,
        *,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get activity statistics."""
        base_stmt = select(AuditLog)
        
        if user_id:
            base_stmt = base_stmt.where(AuditLog.user_id == user_id)
        
        if start_date:
            base_stmt = base_stmt.where(AuditLog.created_at >= start_date)
        
        if end_date:
            base_stmt = base_stmt.where(AuditLog.created_at <= end_date)
        
        # Total events
        total_stmt = select(func.count(AuditLog.id)).select_from(base_stmt.subquery())
        total_result = db.execute(total_stmt)
        total_events = total_result.scalar() or 0
        
        # Events by action
        action_stmt = (
            select(AuditLog.action, func.count(AuditLog.id).label('count'))
            .select_from(base_stmt.subquery())
            .group_by(AuditLog.action)
            .order_by(desc('count'))
        )
        action_result = db.execute(action_stmt)
        by_action = dict(action_result.fetchall())
        
        # Events by target category
        category_stmt = (
            select(AuditLog.target_category, func.count(AuditLog.id).label('count'))
            .select_from(base_stmt.subquery())
            .group_by(AuditLog.target_category)
            .order_by(desc('count'))
        )
        category_result = db.execute(category_stmt)
        by_category = dict(category_result.fetchall())
        
        # Unique users (if not filtered by user)
        unique_users = 0
        if not user_id:
            users_stmt = select(func.count(func.distinct(AuditLog.user_id))).select_from(base_stmt.subquery())
            users_result = db.execute(users_stmt)
            unique_users = users_result.scalar() or 0
        
        return {
            "total_events": total_events,
            "unique_users": unique_users,
            "by_action": by_action,
            "by_target_category": by_category,
            "date_range": {
                "start": start_date.isoformat() if start_date else None,
                "end": end_date.isoformat() if end_date else None
            },
            "user_id": user_id
        }

    def get_daily_activity(
        self,
        db: Session,
        *,
        start_date: date,
        end_date: date,
        user_id: Optional[str] = None
    ) -> Dict[str, int]:
        """Get daily activity counts."""
        stmt = select(
            func.date(AuditLog.created_at).label('activity_date'),
            func.count(AuditLog.id).label('count')
        ).where(
            and_(
                func.date(AuditLog.created_at) >= start_date,
                func.date(AuditLog.created_at) <= end_date
            )
        )
        
        if user_id:
            stmt = stmt.where(AuditLog.user_id == user_id)
        
        stmt = stmt.group_by(func.date(AuditLog.created_at)).order_by('activity_date')
        
        result = db.execute(stmt)
        daily_counts = {}
        
        for row in result:
            daily_counts[row.activity_date.isoformat()] = row.count
        
        return daily_counts

    def cleanup_old_logs(
        self,
        db: Session,
        *,
        days_to_keep: int = 365
    ) -> int:
        """Clean up audit logs older than specified days."""
        from sqlalchemy import delete
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)
        
        # Count logs to be deleted
        count_stmt = select(func.count(AuditLog.id)).where(
            AuditLog.created_at < cutoff_date
        )
        count_result = db.execute(count_stmt)
        count_to_delete = count_result.scalar() or 0
        
        # Delete old logs
        delete_stmt = delete(AuditLog).where(AuditLog.created_at < cutoff_date)
        db.execute(delete_stmt)
        db.commit()
        
        return count_to_delete

    def search_logs(
        self,
        db: Session,
        *,
        search_term: str,
        skip: int = 0,
        limit: int = 50,
        user_id: Optional[str] = None
    ) -> List[AuditLog]:
        """Search audit logs by description or metadata."""
        from sqlalchemy import or_, text
        
        stmt = select(AuditLog).where(
            or_(
                AuditLog.description.ilike(f"%{search_term}%"),
                AuditLog.target_id.ilike(f"%{search_term}%"),
                AuditLog.request_path.ilike(f"%{search_term}%")
            )
        )
        
        if user_id:
            stmt = stmt.where(AuditLog.user_id == user_id)
        
        stmt = stmt.order_by(desc(AuditLog.created_at)).offset(skip).limit(limit)
        result = db.execute(stmt)
        return list(result.scalars().all())


# Create instance
audit_log_crud = CRUDAuditLog(AuditLog)
