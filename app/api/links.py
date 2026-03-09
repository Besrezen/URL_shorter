from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_optional_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.expired_link import ExpiredLink
from app.models.link import Link
from app.models.project import Project
from app.models.user import User
from app.schemas.link import ExpiredLinkOut, LinkCreate, LinkOut, LinkStats, LinkUpdate
from app.services.cache import delete_pattern, get_json, set_json
from app.utils.codegen import generate_short_code

router = APIRouter(tags=['links'])


def _is_expired(expires_at: Optional[datetime]) -> bool:
    return bool(expires_at and expires_at <= datetime.utcnow())


def _parse_cached_datetime(value: object) -> Optional[datetime]:
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None
    return None


def archive_and_delete(db: Session, link: Link) -> None:
    archived = ExpiredLink(
        short_code=link.short_code,
        original_url=link.original_url,
        created_at=link.created_at,
        expired_at=datetime.utcnow(),
        last_accessed_at=link.last_accessed_at,
        click_count=link.click_count,
    )
    db.add(archived)
    db.delete(link)
    db.commit()
    delete_pattern(f'link:{link.short_code}')
    delete_pattern(f'stats:{link.short_code}')
    delete_pattern('search:')


def ensure_project_access(db: Session, project_id: Optional[int], user: Optional[User]) -> Optional[int]:
    if project_id is None:
        return None
    if not user:
        raise HTTPException(status_code=401, detail='Project assignment requires authentication')
    project = db.get(Project, project_id)
    if not project or project.owner_id != user.id:
        raise HTTPException(status_code=404, detail='Project not found')
    return project_id


@router.post('/links/shorten', response_model=LinkOut)
def create_link(payload: LinkCreate, db: Session = Depends(get_db), user: Optional[User] = Depends(get_optional_current_user)):
    if payload.expires_at and payload.expires_at <= datetime.utcnow():
        raise HTTPException(status_code=400, detail='expires_at must be in the future')

    short_code = payload.custom_alias or generate_short_code()
    while db.query(Link).filter(Link.short_code == short_code).first():
        if payload.custom_alias:
            raise HTTPException(status_code=400, detail='custom_alias already exists')
        short_code = generate_short_code()

    project_id = ensure_project_access(db, payload.project_id, user)
    link = Link(
        short_code=short_code,
        original_url=str(payload.original_url),
        owner_id=user.id if user else None,
        expires_at=payload.expires_at,
        project_id=project_id,
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    return LinkOut(
        short_code=link.short_code,
        original_url=link.original_url,
        short_url=f"{settings.BASE_SHORT_URL}/{link.short_code}",
        created_at=link.created_at,
        expires_at=link.expires_at,
        owner_id=link.owner_id,
        project_id=link.project_id,
    )


@router.get('/links/search', response_model=Optional[LinkOut])
def search_link(original_url: str = Query(...), db: Session = Depends(get_db)):
    cache_key = f'search:{original_url}'
    cached = get_json(cache_key)
    if cached:
        cached_expires_at = _parse_cached_datetime(cached.get('expires_at'))
        if not _is_expired(cached_expires_at):
            return cached
        delete_pattern(cache_key)
    link = db.query(Link).filter(
        Link.original_url == original_url,
        or_(Link.expires_at.is_(None), Link.expires_at > datetime.utcnow()),
    ).order_by(Link.created_at.desc()).first()
    if not link:
        return None

    data = LinkOut(
        short_code=link.short_code,
        original_url=link.original_url,
        short_url=f"{settings.BASE_SHORT_URL}/{link.short_code}",
        created_at=link.created_at,
        expires_at=link.expires_at,
        owner_id=link.owner_id,
        project_id=link.project_id,
    ).model_dump()
    set_json(cache_key, data, ex=600)
    return data


@router.get('/links/{short_code}/stats', response_model=LinkStats)
def get_stats(short_code: str, db: Session = Depends(get_db)):
    cache_key = f'stats:{short_code}'
    cached = get_json(cache_key)
    if cached:
        cached_expires_at = _parse_cached_datetime(cached.get('expires_at'))
        if not _is_expired(cached_expires_at):
            return cached
        delete_pattern(cache_key)
    link = db.query(Link).filter(Link.short_code == short_code).first()
    if not link:
        raise HTTPException(status_code=404, detail='Link not found')
    if _is_expired(link.expires_at):
        archive_and_delete(db, link)
        raise HTTPException(status_code=404, detail='Link expired')
    data = LinkStats(
        short_code=link.short_code,
        original_url=link.original_url,
        created_at=link.created_at,
        click_count=link.click_count,
        last_accessed_at=link.last_accessed_at,
        expires_at=link.expires_at,
    ).model_dump()
    set_json(cache_key, data, ex=300)
    return data


@router.put('/links/{short_code}', response_model=LinkOut)
def update_link(short_code: str, payload: LinkUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    link = db.query(Link).filter(Link.short_code == short_code).first()
    if not link:
        raise HTTPException(status_code=404, detail='Link not found')
    if link.owner_id != user.id:
        raise HTTPException(status_code=403, detail='Only owner can update link')
    if payload.new_alias and payload.new_alias != short_code:
        if db.query(Link).filter(Link.short_code == payload.new_alias).first():
            raise HTTPException(status_code=400, detail='Alias already exists')
        link.short_code = payload.new_alias
    if payload.original_url:
        link.original_url = str(payload.original_url)
    if payload.expires_at is not None:
        if payload.expires_at <= datetime.utcnow():
            raise HTTPException(status_code=400, detail='expires_at must be in the future')
        link.expires_at = payload.expires_at
    db.commit()
    db.refresh(link)
    delete_pattern(f'link:{short_code}')
    delete_pattern(f'link:{link.short_code}')
    delete_pattern(f'stats:{short_code}')
    delete_pattern(f'stats:{link.short_code}')
    delete_pattern('search:')
    return LinkOut(
        short_code=link.short_code,
        original_url=link.original_url,
        short_url=f"{settings.BASE_SHORT_URL}/{link.short_code}",
        created_at=link.created_at,
        expires_at=link.expires_at,
        owner_id=link.owner_id,
        project_id=link.project_id,
    )


@router.delete('/links/{short_code}')
def delete_link(short_code: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    link = db.query(Link).filter(Link.short_code == short_code).first()
    if not link:
        raise HTTPException(status_code=404, detail='Link not found')
    if link.owner_id != user.id:
        raise HTTPException(status_code=403, detail='Only owner can delete link')
    db.delete(link)
    db.commit()
    delete_pattern(f'link:{short_code}')
    delete_pattern(f'stats:{short_code}')
    delete_pattern('search:')
    return {'message': 'Link deleted'}


@router.get('/expired-links', response_model=list[ExpiredLinkOut])
def expired_links(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(ExpiredLink).order_by(ExpiredLink.expired_at.desc()).all()


@router.delete('/admin/cleanup-unused')
def cleanup_unused(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    threshold = datetime.utcnow().timestamp() - settings.UNUSED_LINKS_RETENTION_DAYS * 24 * 3600
    removed = 0
    for link in db.query(Link).all():
        last_seen = link.last_accessed_at.timestamp() if link.last_accessed_at else link.created_at.timestamp()
        if last_seen < threshold:
            archive_and_delete(db, link)
            removed += 1
    return {'removed_links': removed, 'retention_days': settings.UNUSED_LINKS_RETENTION_DAYS}


@router.get('/{short_code}')
def redirect_to_original(short_code: str, db: Session = Depends(get_db)):
    cache_key = f'link:{short_code}'
    cached = get_json(cache_key)
    if cached:
        now = datetime.utcnow()
        updated = db.query(Link).filter(
            Link.short_code == short_code,
            or_(Link.expires_at.is_(None), Link.expires_at > now),
        ).update(
            {Link.click_count: Link.click_count + 1, Link.last_accessed_at: now},
            synchronize_session=False,
        )
        if updated:
            db.commit()
            delete_pattern(f'stats:{short_code}')
            return RedirectResponse(url=cached['original_url'], status_code=status.HTTP_307_TEMPORARY_REDIRECT)
        db.rollback()

    link = db.query(Link).filter(Link.short_code == short_code).first()
    if not link:
        delete_pattern(cache_key)
        raise HTTPException(status_code=404, detail='Link not found')
    if _is_expired(link.expires_at):
        archive_and_delete(db, link)
        raise HTTPException(status_code=404, detail='Link expired')

    link.click_count += 1
    link.last_accessed_at = datetime.utcnow()
    db.commit()
    set_json(cache_key, {'original_url': link.original_url}, ex=3600)
    delete_pattern(f'stats:{short_code}')
    return RedirectResponse(url=link.original_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
