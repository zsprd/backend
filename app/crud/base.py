from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete, func

from app.core.database import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        """
        CRUD object with default methods to Create, Read, Update, Delete (CRUD).
        Compatible with SQLAlchemy 2.0+ and Pydantic 2.0+
        
        **Parameters**
        * `model`: A SQLAlchemy model class
        """
        self.model = model

    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        """Get a single record by ID using SQLAlchemy 2.0 syntax."""
        stmt = select(self.model).where(self.model.id == id)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """Get multiple records with pagination using SQLAlchemy 2.0 syntax."""
        stmt = select(self.model).offset(skip).limit(limit)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def get_multi_with_filters(
        self, 
        db: Session, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[ModelType]:
        """Get multiple records with filters and pagination."""
        stmt = select(self.model)
        
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key) and value is not None:
                    stmt = stmt.where(getattr(self.model, key) == value)
        
        stmt = stmt.offset(skip).limit(limit)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        """Create a new record using Pydantic 2.0 model_dump."""
        obj_in_data = obj_in.model_dump(exclude_unset=True)
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def create_from_dict(self, db: Session, *, obj_in: Dict[str, Any]) -> ModelType:
        """Create a new record from dictionary."""
        db_obj = self.model(**obj_in)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """Update an existing record using Pydantic 2.0 model_dump."""
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update_by_id(
        self,
        db: Session,
        *,
        id: Any,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> Optional[ModelType]:
        """Update a record by ID using SQLAlchemy 2.0 syntax."""
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        
        stmt = (
            update(self.model)
            .where(self.model.id == id)
            .values(**update_data)
            .returning(self.model)
        )
        result = db.execute(stmt)
        db.commit()
        return result.scalar_one_or_none()

    def delete(self, db: Session, *, id: Any) -> Optional[ModelType]:
        """Delete a record by ID using SQLAlchemy 2.0 syntax."""
        obj = self.get(db, id=id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj

    def delete_by_id(self, db: Session, *, id: Any) -> bool:
        """Delete a record by ID using SQLAlchemy 2.0 delete statement."""
        stmt = delete(self.model).where(self.model.id == id)
        result = db.execute(stmt)
        db.commit()
        return result.rowcount > 0

    def count(self, db: Session, *, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count records with optional filters using SQLAlchemy 2.0 syntax."""
        stmt = select(func.count(self.model.id))
        
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key) and value is not None:
                    stmt = stmt.where(getattr(self.model, key) == value)
        
        result = db.execute(stmt)
        return result.scalar() or 0

    def exists(self, db: Session, *, id: Any) -> bool:
        """Check if a record exists by ID using SQLAlchemy 2.0 syntax."""
        stmt = select(func.count(self.model.id)).where(self.model.id == id)
        result = db.execute(stmt)
        return (result.scalar() or 0) > 0

    def get_by_field(
        self, 
        db: Session, 
        *, 
        field_name: str, 
        field_value: Any
    ) -> Optional[ModelType]:
        """Get a record by a specific field value using SQLAlchemy 2.0 syntax."""
        if hasattr(self.model, field_name):
            stmt = select(self.model).where(getattr(self.model, field_name) == field_value)
            result = db.execute(stmt)
            return result.scalar_one_or_none()
        return None

    def get_multi_by_field(
        self, 
        db: Session, 
        *, 
        field_name: str, 
        field_value: Any,
        skip: int = 0,
        limit: int = 100
    ) -> List[ModelType]:
        """Get multiple records by a specific field value using SQLAlchemy 2.0 syntax."""
        if hasattr(self.model, field_name):
            stmt = (
                select(self.model)
                .where(getattr(self.model, field_name) == field_value)
                .offset(skip)
                .limit(limit)
            )
            result = db.execute(stmt)
            return list(result.scalars().all())
        return []

    def bulk_create(self, db: Session, *, objs_in: List[CreateSchemaType]) -> List[ModelType]:
        """Bulk create multiple records efficiently."""
        db_objs = []
        for obj_in in objs_in:
            obj_in_data = obj_in.model_dump(exclude_unset=True)
            db_obj = self.model(**obj_in_data)
            db_objs.append(db_obj)
        
        db.add_all(db_objs)
        db.commit()
        for db_obj in db_objs:
            db.refresh(db_obj)
        return db_objs
    