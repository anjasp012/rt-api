import math
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from app.db.session import get_db
from app.models.persona import Persona
from app.models.zone import Zone
from app.models.innovation import Innovation
from app.models.suggestion import ResearchSuggestion
from app.models.telemetry import TelemetryLog
from app.models.setting import AppSetting
from app.schemas.persona import PersonaResponse
from app.schemas.zone import ZoneResponse
from app.schemas.innovation import (
    InnovationResponse, 
    InnovationExploreCard,
    InnovationExplorePaginatedResponse
)
from app.schemas.suggestion import SuggestionCreate, SuggestionResponse
from app.schemas.stats import TelemetryEventCreate

router = APIRouter()


def _get_explore_cards(
    db: Session,
    persona_id: Optional[int] = None,
    persona_slug: Optional[str] = None,
    zone_id: Optional[int] = None,
    zone_slug: Optional[str] = None,
    category: Optional[str] = None
) -> List[dict]:
    """Helper internal untuk mengambil & menghitung skor relevansi inovasi"""
    resolved_persona_id = persona_id
    resolved_zone_id = zone_id

    if not resolved_persona_id and persona_slug:
        p = db.query(Persona.id).filter(Persona.slug == persona_slug).first()
        if p:
            resolved_persona_id = p[0]

    if not resolved_zone_id and zone_slug:
        z = db.query(Zone.id).filter(Zone.slug == zone_slug).first()
        if z:
            resolved_zone_id = z[0]

    query = db.query(Innovation).options(
        joinedload(Innovation.zone),
        joinedload(Innovation.research_center),
        joinedload(Innovation.persona_relevances)
    ).filter(Innovation.is_active == True)

    if resolved_zone_id:
        query = query.filter(Innovation.zone_id == resolved_zone_id)

    if category:
        query = query.filter(Innovation.category_tag.ilike(f"%{category}%"))

    # Batas kuota display dari setting CMS
    limit_setting = db.query(AppSetting).filter(AppSetting.key == "frontend_display_limit").first()
    limit_val = int(limit_setting.value) if limit_setting and str(limit_setting.value).isdigit() else 50

    innovations = query.limit(limit_val).all()

    cards = []
    for item in innovations:
        relevance_score = item.order_priority
        if resolved_persona_id:
            rel = next((r for r in item.persona_relevances if r.persona_id == resolved_persona_id), None)
            if rel:
                relevance_score += rel.relevance_score
            else:
                relevance_score += 10

        cards.append({
            "id": item.id,
            "title": item.title,
            "slug": item.slug,
            "category_tag": item.category_tag,
            "trl": item.trl,
            "short_description": item.short_description,
            "summary": item.summary,
            "impact": item.impact,
            "thumbnail_url": item.thumbnail_url,
            "download_url": item.download_url or f"https://brin.go.id/riset/{item.slug}/brochure.pdf",
            "qr_code_data": item.qr_code_data or f"https://brin.go.id/riset/{item.slug}",
            "zone_name": item.zone.name if item.zone else "Umum",
            "zone_number": item.zone.zone_number if item.zone else 0,
            "research_center_name": item.research_center.name if item.research_center else "Pusat Riset BRIN",
            "relevance_score": relevance_score
        })

    # Urutkan berdasarkan relevansi persona tertinggi lalu TRL
    cards.sort(key=lambda x: (x["relevance_score"], x["trl"]), reverse=True)
    return cards


@router.get("/personas", response_model=List[PersonaResponse])
def get_active_personas(db: Session = Depends(get_db)):
    """[Slot 1] Mengambil daftar 8 Modul Pengguna (Persona)"""
    return db.query(Persona).filter(Persona.is_active == True).order_by(Persona.order_index.asc()).all()


@router.get("/zones", response_model=List[ZoneResponse])
def get_active_zones(db: Session = Depends(get_db)):
    """[Slot 2] Mengambil daftar 9 Token Tantangan (Zona Riset BRIN)"""
    return db.query(Zone).filter(Zone.is_active == True).order_by(Zone.zone_number.asc()).all()


@router.get("/explore", response_model=List[InnovationExploreCard])
def explore_innovations(
    persona_id: Optional[int] = None,
    persona_slug: Optional[str] = None,
    zone_id: Optional[int] = None,
    zone_slug: Optional[str] = None,
    category: Optional[str] = None,
    page: Optional[int] = None,
    page_size: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    [Daftar Penelitian] Mengambil inovasi BRIN berdasarkan kombinasi Slot 1 & Slot 2.
    """
    cards = _get_explore_cards(
        db=db,
        persona_id=persona_id,
        persona_slug=persona_slug,
        zone_id=zone_id,
        zone_slug=zone_slug,
        category=category
    )

    if page is not None and page_size is not None and page >= 1 and page_size >= 1:
        start = (page - 1) * page_size
        end = start + page_size
        return cards[start:end]

    return cards


@router.get("/explore/paginated", response_model=InnovationExplorePaginatedResponse)
def explore_innovations_paginated(
    persona_id: Optional[int] = Query(None, description="ID Persona (Slot 1)"),
    zone_id: Optional[int] = Query(None, description="ID Zona Riset (Slot 2)"),
    page: int = Query(1, ge=1, description="Nomor halaman (mulai 1)"),
    page_size: int = Query(3, ge=1, le=50, description="Jumlah kartu per halaman (default 3 sesuai PDF)"),
    category: Optional[str] = Query(None, description="Filter Kategori"),
    db: Session = Depends(get_db)
):
    """
    [Daftar Penelitian Paginated - Halaman 32 & 37 PDF]:
    Mengembalikan `items`, `total`, `page`, `page_size`, dan `total_pages` (contoh: Menampilkan 1 - 3 dari 24 penelitian).
    """
    all_cards = _get_explore_cards(
        db=db,
        persona_id=persona_id,
        zone_id=zone_id,
        category=category
    )

    total = len(all_cards)
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    start = (page - 1) * page_size
    end = start + page_size
    items = all_cards[start:end]

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }


@router.get("/innovations/{identifier}", response_model=InnovationResponse)
def get_innovation_detail(identifier: str, db: Session = Depends(get_db)):
    """
    [Modal Detail Inovasi - Halaman 33 PDF]
    """
    query = db.query(Innovation).options(
        joinedload(Innovation.zone),
        joinedload(Innovation.research_center)
    )
    if identifier.isdigit():
        innovation = query.filter(Innovation.id == int(identifier)).first()
    else:
        innovation = query.filter(Innovation.slug == identifier).first()

    if not innovation:
        raise HTTPException(status_code=404, detail="Inovasi tidak ditemukan")
    return innovation


@router.post("/suggestions", response_model=SuggestionResponse, status_code=status.HTTP_201_CREATED)
def submit_research_suggestion(payload: SuggestionCreate, db: Session = Depends(get_db)):
    """
    [Form Usulkan Topik Riset - Halaman 34 PDF] Pengunjung mengirim usulan riset baru.
    """
    if not payload.topic_wanted or len(payload.topic_wanted.strip()) == 0:
        raise HTTPException(status_code=400, detail="Topik yang dicari wajib diisi")

    suggestion = ResearchSuggestion(
        visitor_name=payload.visitor_name,
        age_range=payload.age_range,
        topic_wanted=payload.topic_wanted.strip(),
        feedback=payload.feedback.strip() if payload.feedback else None,
        persona_id=payload.persona_id,
        zone_id=payload.zone_id,
        screen_context=payload.screen_context or "Explore",
        status="NEW"
    )
    db.add(suggestion)
    db.commit()
    db.refresh(suggestion)

    return {
        "id": suggestion.id,
        "visitor_name": suggestion.visitor_name,
        "age_range": suggestion.age_range,
        "topic_wanted": suggestion.topic_wanted,
        "feedback": suggestion.feedback,
        "persona_id": suggestion.persona_id,
        "persona_name": suggestion.persona.name if suggestion.persona else None,
        "zone_id": suggestion.zone_id,
        "zone_name": suggestion.zone.name if suggestion.zone else None,
        "screen_context": suggestion.screen_context,
        "status": suggestion.status,
        "admin_notes": suggestion.admin_notes,
        "created_at": suggestion.created_at,
        "updated_at": suggestion.created_at
    }


@router.post("/telemetry", status_code=status.HTTP_201_CREATED)
def log_telemetry_event(payload: TelemetryEventCreate, db: Session = Depends(get_db)):
    """Pencatatan log interaksi layar sentuh"""
    log_entry = TelemetryLog(
        event_type=payload.event_type,
        persona_slug=payload.persona_slug,
        zone_slug=payload.zone_slug,
        innovation_slug=payload.innovation_slug,
        metadata_payload=payload.metadata_payload or {}
    )
    db.add(log_entry)
    db.commit()
    return {"status": "success", "event": payload.event_type}
