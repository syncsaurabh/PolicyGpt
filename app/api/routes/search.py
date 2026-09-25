from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.dependencies import get_db, get_optional_current_user
from app.models.user import User
from app.schemas.policy import PolicyRead
from app.schemas.scheme import SchemeRead
from app.schemas.search import PolicySearchResponse, SchemeSearchResponse
from app.services.search_service import SearchService

router = APIRouter(prefix="/search", tags=["Search"])


@router.get(
    "/policies",
    response_model=PolicySearchResponse,
    summary="Search policies with multi-field filters",
)
def search_policies(
    keyword: Optional[str] = Query(None, description="Free-text keyword to match title and description"),
    category: Optional[str] = Query(None, description="Filter by policy category"),
    state: Optional[str] = Query(None, description="Filter by state or central domain"),
    ministry: Optional[str] = Query(None, description="Filter by ministry name"),
    department: Optional[str] = Query(None, description="Filter by department name"),
    sector: Optional[str] = Query(None, description="Filter by economic or social sector"),
    publication_date: Optional[date] = Query(None, description="Filter by publication date (YYYY-MM-DD)"),
    status: Optional[str] = Query(None, description="Filter by policy status (DRAFT, PUBLISHED, etc.)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order ('asc' or 'desc')"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    """
    Search policies using keyword search and multiple filters simultaneously.
    Searches are recorded in search history.
    """
    results, total_count, total_pages = SearchService.search_policies(
        db=db,
        keyword=keyword,
        category=category,
        state=state,
        ministry=ministry,
        department=department,
        sector=sector,
        publication_date=publication_date,
        status_filter=status,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
        current_user=current_user,
    )
    return PolicySearchResponse(
        total_count=total_count,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        results=[PolicyRead.model_validate(p) for p in results],
    )


@router.get(
    "/schemes",
    response_model=SchemeSearchResponse,
    summary="Search public schemes with multi-field filters",
)
def search_schemes(
    keyword: Optional[str] = Query(None, description="Free-text keyword to match name and description"),
    category: Optional[str] = Query(None, description="Filter by scheme category"),
    state: Optional[str] = Query(None, description="Filter by state"),
    ministry: Optional[str] = Query(None, description="Filter by ministry name"),
    department: Optional[str] = Query(None, description="Filter by department name"),
    sector: Optional[str] = Query(None, description="Filter by sector"),
    publication_date: Optional[date] = Query(None, description="Filter by publication date (YYYY-MM-DD)"),
    status: Optional[str] = Query(None, description="Filter by operational status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order ('asc' or 'desc')"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    """
    Search schemes using keyword search and multiple filters simultaneously.
    Searches are recorded in search history.
    """
    results, total_count, total_pages = SearchService.search_schemes(
        db=db,
        keyword=keyword,
        category=category,
        state=state,
        ministry=ministry,
        department=department,
        sector=sector,
        publication_date=publication_date,
        status_filter=status,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
        current_user=current_user,
    )
    return SchemeSearchResponse(
        total_count=total_count,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        results=[SchemeRead.model_validate(s) for s in results],
    )
