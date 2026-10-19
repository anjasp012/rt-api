import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, func
from app.db.session import get_db
from app.models.persona import Persona
from app.models.challenge import Challenge, Zone
from app.models.solution import Solution, Innovation
from app.models.suggestion import ResearchSuggestion
from app.schemas.persona import PersonaResponse
from app.schemas.challenge import ChallengeResponse, ZoneResponse
from app.schemas.solution import (
    SolutionResponse, 
    SolutionExploreCard,
    InnovationResponse,
    InnovationExploreCard
)
from app.schemas.suggestion import SuggestionCreate, SuggestionResponse
from app.core.helpers import build_full_url

router = APIRouter()


def _get_explore_cards(
    db: Session,
    persona_id: Optional[uuid.UUID] = None,
    persona_slug: Optional[str] = None,
    challenge_id: Optional[uuid.UUID] = None,
    challenge_slug: Optional[str] = None,
    aspect: Optional[str] = None,
    search: Optional[str] = None
) -> List[dict]:
    """
    Helper internal untuk mengambil, memfilter, & menghitung skor relevansi solusi riset.
    """
    resolved_persona_id = persona_id if isinstance(persona_id, uuid.UUID) else None
    if not resolved_persona_id and isinstance(persona_slug, str) and persona_slug.strip():
        p = db.query(Persona.id).filter(Persona.slug == persona_slug.strip()).first()
        if p:
            resolved_persona_id = p[0]

    resolved_challenge_id = challenge_id if isinstance(challenge_id, uuid.UUID) else None
    if not resolved_challenge_id and isinstance(challenge_slug, str) and challenge_slug.strip():
        c = db.query(Challenge.id).filter(Challenge.slug == challenge_slug.strip()).first()
        if c:
            resolved_challenge_id = c[0]

    query = db.query(Solution).options(
        joinedload(Solution.challenge),
        joinedload(Solution.relevant_challenges),
        joinedload(Solution.personas),
        joinedload(Solution.persona_relevances)
    ).filter(Solution.is_active == True)

    # Filter berdasarkan Tantangan / Bidang (Utama atau Tantangan Relevan M2M)
    if resolved_challenge_id:
        query = query.filter(
            (Solution.challenge_id == resolved_challenge_id) |
            (Solution.relevant_challenges.any(Challenge.id == resolved_challenge_id))
        )

    # Filter berdasarkan Aspek riset
    if isinstance(aspect, str) and aspect.strip():
        query = query.filter(Solution.aspect.ilike(f"%{aspect.strip()}%"))

    # Filter pencarian keyword bebas (Judul, Aspek, ID Publikasi, Pertanyaan, Ringkasan, Tahukah Kamu)
    if isinstance(search, str) and search.strip():
        q_term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Solution.title.ilike(q_term),
                Solution.aspect.ilike(q_term),
                Solution.publication_id.ilike(q_term),
                Solution.question.ilike(q_term),
                Solution.summary.ilike(q_term),
                Solution.fun_fact.ilike(q_term),
                Solution.research_center.ilike(q_term)
            )
        )

    solutions = query.limit(200).all()

    scored_items = []
    for item in solutions:
        relevance_score = 0
        is_matched_persona = False

        if resolved_persona_id:
            # Cek jika persona ada di daftar Kategori Peran (M2M) atau primary persona_id
            is_matched_persona = any(p.id == resolved_persona_id for p in item.personas) or (item.persona_id == resolved_persona_id)
            if is_matched_persona:
                relevance_score += 80
            
            # Cek jika ada custom weight di relevance mappings
            rel = next((r for r in item.persona_relevances if r.persona_id == resolved_persona_id), None)
            if rel:
                relevance_score += rel.relevance_score
            elif not is_matched_persona:
                relevance_score += 10

        # Jika kedua modul (Peran & Tantangan) cocok dengan solusi ini, berikan bonus sinergi
        if resolved_persona_id and resolved_challenge_id and is_matched_persona:
            is_matched_challenge = (item.challenge_id == resolved_challenge_id) or any(c.id == resolved_challenge_id for c in item.relevant_challenges)
            if is_matched_challenge:
                relevance_score += 50

        scored_items.append((relevance_score, item))

    # Urutkan berdasarkan relevansi tertinggi, lalu tahun terbaru, lalu TRL tertinggi
    scored_items.sort(
        key=lambda x: (
            x[0],
            x[1].year or 0,
            x[1].trl or 0
        ),
        reverse=True
    )

    cards = [
        {
            "id": it.id,
            "slug": it.slug,
            "judul_asli": it.title,
            "ringkasan": it.summary,
            "aspek": it.aspect,
            "tahun": it.year
        }
        for _, it in scored_items
    ]
    return cards


# =========================================================================
# 👑 1. MASTER MODUL INTERAKTIF (PERAN & TANTANGAN)
# =========================================================================

@router.get("/personas", response_model=List[PersonaResponse], summary="Daftar Modul Peran (Slot 1)")
def get_personas(db: Session = Depends(get_db)):
    """Mengambil seluruh daftar Modul Peran (Slot 1) yang aktif di meja interaktif"""
    return db.query(Persona).filter(Persona.is_active == True).order_by(Persona.created_at.asc()).all()


@router.get("/challanges", response_model=List[ChallengeResponse], summary="Daftar Modul Tantangan (Slot 2)")
@router.get("/challenges", response_model=List[ChallengeResponse], include_in_schema=False)
@router.get("/zones", response_model=List[ChallengeResponse], include_in_schema=False)
def get_challenges(db: Session = Depends(get_db)):
    """Mengambil seluruh daftar Modul Tantangan (Slot 2) yang aktif"""
    return db.query(Challenge).filter(Challenge.is_active == True).order_by(Challenge.created_at.asc()).all()


# =========================================================================
# 🔬 2. KATALOG & DETAIL SOLUSI RISET
# =========================================================================

@router.get("/solutions", response_model=List[SolutionExploreCard], summary="Daftar Solusi Riset")
@router.get("/explore", response_model=List[SolutionExploreCard], include_in_schema=False)
def get_solutions(
    persona_id: Optional[uuid.UUID] = Query(None, description="ID Peran (Slot 1)"),
    persona_slug: Optional[str] = Query(None, description="Slug Peran"),
    challenge_id: Optional[uuid.UUID] = Query(None, description="ID Tantangan (Slot 2)"),
    challenge_slug: Optional[str] = Query(None, description="Slug Tantangan"),
    challange_id: Optional[uuid.UUID] = Query(None, description="Alias ID Tantangan (Slot 2)"),
    challange_slug: Optional[str] = Query(None, description="Alias Slug Tantangan"),
    zone_id: Optional[uuid.UUID] = Query(None, description="Legacy ID Tantangan"),
    zone_slug: Optional[str] = Query(None, description="Legacy Slug Tantangan"),
    aspect: Optional[str] = Query(None, description="Filter nama aspek riset"),
    search: Optional[str] = Query(None, description="Pencarian kata kunci"),
    limit: Optional[int] = Query(None, ge=1, le=200, description="Batas jumlah hasil"),
    db: Session = Depends(get_db)
):
    """
    Mengambil daftar kartu solusi riset BRIN berdasarkan kombinasi Slot 1 (Peran) dan Slot 2 (Tantangan).
    Hanya mengembalikan 6 field utama: id, slug, judul_asli, ringkasan, aspek, tahun.
    """
    effective_challenge_id = challenge_id or challange_id or zone_id
    effective_challenge_slug = challenge_slug or challange_slug or zone_slug

    cards = _get_explore_cards(
        db=db,
        persona_id=persona_id,
        persona_slug=persona_slug,
        challenge_id=effective_challenge_id,
        challenge_slug=effective_challenge_slug,
        aspect=aspect,
        search=search
    )

    if limit is not None and isinstance(limit, int):
        return cards[:limit]

    return cards


@router.get("/solution/{identifier}", response_model=SolutionResponse, summary="Detail Lengkap Solusi Riset")
@router.get("/solutions/{identifier}", response_model=SolutionResponse, include_in_schema=False)
@router.get("/innovations/{identifier}", response_model=SolutionResponse, include_in_schema=False)
def get_solution_detail(identifier: str, db: Session = Depends(get_db)):
    """
    Mengambil detail lengkap solusi riset spesifik berdasarkan UUID, ID Publikasi (misal P10212), atau Slug.
    """
    query = db.query(Solution).options(
        joinedload(Solution.challenge),
        joinedload(Solution.relevant_challenges),
        joinedload(Solution.personas),
        joinedload(Solution.persona_relevances)
    )

    solution = None
    # 1. Coba sebagai UUID
    try:
        uuid_obj = uuid.UUID(identifier)
        solution = query.filter(Solution.id == uuid_obj).first()
    except ValueError:
        pass

    # 2. Coba sebagai ID Publikasi (case-insensitive, contoh: P10212)
    if not solution:
        solution = query.filter(func.lower(Solution.publication_id) == identifier.strip().lower()).first()

    # 3. Coba sebagai Slug
    if not solution:
        solution = query.filter(Solution.slug == identifier.strip()).first()

    if not solution:
        raise HTTPException(status_code=404, detail="Solusi riset tidak ditemukan")
    return solution


# =========================================================================
# 💬 3. USULAN RISET DARI PENGUNJUNG MEJA INTERAKTIF
# =========================================================================

@router.post("/suggestion", response_model=SuggestionResponse, status_code=status.HTTP_201_CREATED, summary="Kirim Usulan Riset")
@router.post("/suggestions", response_model=SuggestionResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
def submit_research_suggestion(payload: SuggestionCreate, db: Session = Depends(get_db)):
    """
    Pengunjung mengirim usulan topik riset baru melalui layar meja interaktif.
    Hanya menerima & mengembalikan: title, deskripsi, persona_ids, challange_ids.
    """
    if not payload.title or len(payload.title.strip()) == 0:
        raise HTTPException(status_code=422, detail="Title (Judul usulan) wajib diisi")

    personas = []
    if payload.persona_ids:
        personas = db.query(Persona).filter(Persona.id.in_(payload.persona_ids)).all()

    challenges = []
    if payload.challange_ids:
        challenges = db.query(Challenge).filter(Challenge.id.in_(payload.challange_ids)).all()

    suggestion = ResearchSuggestion(
        title=payload.title.strip(),
        deskripsi=payload.deskripsi.strip() if payload.deskripsi else None,
        personas=personas,
        challenges=challenges,
        status="NEW"
    )
    db.add(suggestion)
    db.commit()
    db.refresh(suggestion)

    return {
        "id": suggestion.id,
        "title": suggestion.title,
        "deskripsi": suggestion.deskripsi,
        "persona_ids": [p.id for p in suggestion.personas],
        "challange_ids": [c.id for c in suggestion.challenges]
    }
