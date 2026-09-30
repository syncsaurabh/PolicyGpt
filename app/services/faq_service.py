from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.models.faq import FAQ
from app.models.user import User
from app.schemas.faq import FAQCreate, FAQUpdate
from app.services.audit_service import AuditService


class FAQService:
    @staticmethod
    def create_faq(db: Session, faq_in: FAQCreate, current_user: User) -> FAQ:
        """Create a new FAQ entry."""
        faq = FAQ(**faq_in.model_dump())
        db.add(faq)
        db.flush()

        AuditService.log(
            db=db,
            action="FAQ_CREATED",
            entity_type="FAQ",
            entity_id=str(faq.id),
            user_id=current_user.id,
            details=f"Created FAQ: '{faq.question[:50]}...'",
        )
        db.commit()
        db.refresh(faq)
        return faq

    @staticmethod
    def get_faq(db: Session, faq_id: int) -> FAQ:
        """Retrieve a specific FAQ."""
        faq = db.query(FAQ).filter(FAQ.id == faq_id).first()
        if not faq:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"FAQ with ID {faq_id} not found",
            )
        return faq

    @staticmethod
    def list_faqs(
        db: Session,
        category: Optional[str] = None,
        keyword: Optional[str] = None,
        is_active_only: bool = True,
        page: int = 1,
        page_size: int = 50,
    ) -> Tuple[List[FAQ], int, int]:
        """List FAQs with optional category and search query filters and pagination."""
        query = db.query(FAQ)
        if is_active_only:
            query = query.filter(FAQ.is_active == True)
        if category:
            query = query.filter(FAQ.category.ilike(f"%{category.strip()}%"))
        if keyword:
            kw = f"%{keyword.strip()}%"
            query = query.filter(or_(FAQ.question.ilike(kw), FAQ.answer.ilike(kw)))

        total_count = query.count()
        total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 1
        offset = (page - 1) * page_size
        results = query.order_by(FAQ.display_order.asc(), FAQ.created_at.desc()).offset(offset).limit(page_size).all()

        return results, total_count, total_pages

    @staticmethod
    def update_faq(db: Session, faq_id: int, faq_update: FAQUpdate, current_user: User) -> FAQ:
        """Update FAQ details."""
        faq = db.query(FAQ).filter(FAQ.id == faq_id).first()
        if not faq:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"FAQ with ID {faq_id} not found",
            )

        update_data = faq_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(faq, key, value)

        AuditService.log(
            db=db,
            action="FAQ_UPDATED",
            entity_type="FAQ",
            entity_id=str(faq.id),
            user_id=current_user.id,
            details=f"Updated FAQ ID {faq_id}",
        )
        db.commit()
        db.refresh(faq)
        return faq

    @staticmethod
    def delete_faq(db: Session, faq_id: int, current_user: User) -> bool:
        """Delete an FAQ entry."""
        faq = db.query(FAQ).filter(FAQ.id == faq_id).first()
        if not faq:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"FAQ with ID {faq_id} not found",
            )

        db.delete(faq)
        AuditService.log(
            db=db,
            action="FAQ_DELETED",
            entity_type="FAQ",
            entity_id=str(faq_id),
            user_id=current_user.id,
            details=f"Deleted FAQ '{faq.question[:50]}...'",
        )
        db.commit()
        return True
