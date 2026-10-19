import uuid
from typing import List, Optional, Union, Any
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
    SolutionDetailResponse,
    InnovationResponse,
    InnovationExploreCard,
    InnovationDetailResponse
)
from app.schemas.suggestion import SuggestionCreate, SuggestionResponse
from app.core.helpers import build_full_url

router = APIRouter()


def _parse_uuids(val: Any) -> List[uuid.UUID]:
    if not val or hasattr(val, "default"):
        return []
    if isinstance(val, uuid.UUID):
        return [val]
    if isinstance(val, str):
        val = [val]
    parsed = []
    if isinstance(val, (list, tuple, set)):
        for item in val:
            if isinstance(item, uuid.UUID):
                parsed.append(item)
            elif isinstance(item, str):
                for part in item.split(","):
                    part_clean = part.strip()
                    if part_clean:
                        try:
                            parsed.append(uuid.UUID(part_clean))
                        except ValueError:
                            pass
    return list(dict.fromkeys(parsed))


def _get_explore_cards(
    db: Session,
    persona_ids: Optional[List[uuid.UUID]] = None,
    challange_ids: Optional[List[uuid.UUID]] = None,
    search: Optional[str] = None
) -> List[dict]:
    """
    Helper internal untuk mengambil, memfilter, & menghitung skor relevansi solusi riset.
    """
    query = db.query(Solution).options(
        joinedload(Solution.challenge),
        joinedload(Solution.relevant_challenges),
        joinedload(Solution.personas),
        joinedload(Solution.persona_relevances)
    ).filter(Solution.is_active == True)

    # Filter berdasarkan Tantangan / Bidang (Utama atau Tantangan Relevan M2M)
    if challange_ids:
        query = query.filter(
            (Solution.challenge_id.in_(challange_ids)) |
            (Solution.relevant_challenges.any(Challenge.id.in_(challange_ids)))
        )

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

        if persona_ids:
            is_matched_persona = any(p.id in persona_ids for p in item.personas) or (item.persona_id in persona_ids)
            if is_matched_persona:
                relevance_score += 80

            for pid in persona_ids:
                rel = next((r for r in item.persona_relevances if r.persona_id == pid), None)
                if rel:
                    relevance_score += rel.relevance_score
            if not is_matched_persona:
                relevance_score += 10

        # Jika kedua modul (Peran & Tantangan) cocok dengan solusi ini, berikan bonus sinergi
        if persona_ids and challange_ids and is_matched_persona:
            is_matched_challenge = (item.challenge_id in challange_ids) or any(c.id in challange_ids for c in item.relevant_challenges)
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

    cards = []
    for _, it in scored_items:
        cards.append({
            "id": it.id,
            "slug": it.slug,
            "title": it.title,
            "summary": it.summary,
            "year": it.year,
            "publication_media": it.publication_media,
            "question": it.question,
            "introduction": it.introduction,
            "challenge_name": it.challenge_name,
            "persona_name": it.persona_name,
        })
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
    persona_ids: Optional[List[str]] = Query(None, description="Daftar ID Persona (Slot 1)"),
    challange_ids: Optional[List[str]] = Query(None, description="Daftar ID Tantangan / Challenge (Slot 2)"),
    search: Optional[str] = Query(None, description="Pencarian kata kunci"),
    limit: Optional[int] = Query(None, ge=1, le=200, description="Batas jumlah hasil"),
    challenge_ids: Optional[List[str]] = Query(None, include_in_schema=False),
    persona_id: Optional[str] = Query(None, include_in_schema=False),
    challange_id: Optional[str] = Query(None, include_in_schema=False),
    challenge_id: Optional[str] = Query(None, include_in_schema=False),
    db: Session = Depends(get_db)
):
    """
    Mengambil daftar kartu solusi riset BRIN berdasarkan kombinasi Slot 1 (Peran) dan Slot 2 (Tantangan).
    Query parameters utama: persona_ids dan challange_ids.
    """
    raw_persona = persona_ids or ([persona_id] if persona_id else None)
    parsed_persona_ids = _parse_uuids(raw_persona)

    raw_challange = challange_ids or challenge_ids or ([challange_id or challenge_id] if (challange_id or challenge_id) else None)
    parsed_challenge_ids = _parse_uuids(raw_challange)

    cards = _get_explore_cards(
        db=db,
        persona_ids=parsed_persona_ids,
        challange_ids=parsed_challenge_ids,
        search=search
    )

    if limit is not None and isinstance(limit, int):
        return cards[:limit]

    return cards


@router.get("/solution/{identifier}", response_model=SolutionDetailResponse, summary="Detail Solusi Riset")
@router.get("/solutions/{identifier}", response_model=SolutionDetailResponse, include_in_schema=False)
@router.get("/innovations/{identifier}", response_model=SolutionDetailResponse, include_in_schema=False)
def get_solution_detail(identifier: str, db: Session = Depends(get_db)):
    """
    Mengambil detail solusi riset spesifik (11 field: id, title, summary, writter, year, research_center, publication_media, abstract_url, jurnal_publication, bidang_relevan, persona).
    Bisa dicari berdasarkan UUID, ID Publikasi (misal P10212), atau Slug.
    """
    query = db.query(Solution).options(
        joinedload(Solution.challenge),
        joinedload(Solution.relevant_challenges),
        joinedload(Solution.personas),
        joinedload(Solution.persona)
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

    relevant_challenges = [c.name for c in solution.relevant_challenges] if solution.relevant_challenges else []
    if not relevant_challenges and solution.challenge:
        relevant_challenges = [solution.challenge.name]

    personas = [p.name for p in solution.personas] if solution.personas else []
    if not personas and solution.persona:
        personas = [solution.persona.name]

    return {
        "id": solution.id,
        "title": solution.title,
        "summary": solution.summary,
        "aspect": solution.aspect,
        "writer": solution.writer,
        "year": solution.year,
        "research_center": solution.research_center,
        "publication_media": solution.publication_media,
        "abstract_url": solution.abstract_url,
        "journal_publication": solution.journal_publication,
        "question": solution.question,
        "introduction": solution.introduction,
        "challenge_name": solution.challenge_name,
        "persona_name": solution.persona_name,
        "relevant_challenges": relevant_challenges,
        "personas": personas,
    }


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
