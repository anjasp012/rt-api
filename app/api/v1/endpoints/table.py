import uuid
import time
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, func
from app.db.session import get_db
from app.models.persona import Persona
from app.models.challenge import Challenge, Zone
from app.models.solution import Solution, Innovation
from app.models.suggestion import ResearchSuggestion
from app.models.interaction import ModuleInteractionLog
from app.models.publication import Publication
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
from app.schemas.publication import PublicPublicationOverviewResponse
from app.schemas.last_change import LastChangeResponse
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
    if not resolved_persona_id and persona_id and isinstance(persona_id, str):
        try:
            resolved_persona_id = uuid.UUID(persona_id.strip())
        except ValueError:
            pass
    if not resolved_persona_id and isinstance(persona_slug, str) and persona_slug.strip():
        p = db.query(Persona.id).filter(Persona.slug == persona_slug.strip()).first()
        if p:
            resolved_persona_id = p[0]

    resolved_challenge_id = challenge_id if isinstance(challenge_id, uuid.UUID) else None
    if not resolved_challenge_id and challenge_id and isinstance(challenge_id, str):
        try:
            resolved_challenge_id = uuid.UUID(challenge_id.strip())
        except ValueError:
            pass
    if not resolved_challenge_id and isinstance(challenge_slug, str) and challenge_slug.strip():
        c = db.query(Challenge.id).filter(Challenge.slug == challenge_slug.strip()).first()
        if c:
            resolved_challenge_id = c[0]

    # Catat histori interaksi meja sentuh jika peran atau tantangan dipilih
    if resolved_persona_id or resolved_challenge_id:
        try:
            interaction_log = ModuleInteractionLog(
                persona_id=resolved_persona_id,
                challenge_id=resolved_challenge_id,
                event="EXPLORE"
            )
            db.add(interaction_log)
            db.commit()
        except Exception:
            db.rollback()

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

    # Urutkan berdasarkan relevansi tertinggi, lalu tahun terbaru
    scored_items.sort(
        key=lambda x: (
            x[0],
            x[1].year or 0
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
            "fun_fact": it.fun_fact,
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
@router.get("/solution", response_model=List[SolutionExploreCard], include_in_schema=False)
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
    persona_ids: Optional[List[str]] = Query(None, include_in_schema=False),
    challenge_ids: Optional[List[str]] = Query(None, include_in_schema=False),
    challange_ids: Optional[List[str]] = Query(None, include_in_schema=False),
    aspect: Optional[str] = Query(None, description="Filter nama aspek riset"),
    search: Optional[str] = Query(None, description="Pencarian kata kunci"),
    limit: Optional[int] = Query(None, ge=1, le=200, description="Batas jumlah hasil"),
    db: Session = Depends(get_db)
):
    """
    Mengambil daftar kartu solusi riset BRIN berdasarkan kombinasi Slot 1 (Peran) dan Slot 2 (Tantangan).
    Mengembalikan field utama kartu: id, slug, judul_asli, ringkasan, tahun, media_publikasi, pertanyaan, pengantar, challenge_name, persona_name, dan fun_fact.
    """
    effective_persona = persona_id or (persona_ids[0] if persona_ids else None)
    effective_challenge_id = challenge_id or challange_id or zone_id or (challenge_ids[0] if challenge_ids else None) or (challange_ids[0] if challange_ids else None)
    effective_challenge_slug = challenge_slug or challange_slug or zone_slug

    cards = _get_explore_cards(
        db=db,
        persona_id=effective_persona,
        persona_slug=persona_slug,
        challenge_id=effective_challenge_id,
        challenge_slug=effective_challenge_slug,
        aspect=aspect,
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

    # Catat histori interaksi meja sentuh saat melihat detail solusi
    try:
        sol_persona_id = solution.persona_id or (solution.personas[0].id if solution.personas else None)
        interaction_log = ModuleInteractionLog(
            persona_id=sol_persona_id,
            challenge_id=solution.challenge_id,
            solution_id=solution.id,
            event="DETAIL"
        )
        db.add(interaction_log)
        db.commit()
    except Exception:
        db.rollback()

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
        "fun_fact": solution.fun_fact,
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


# =========================================================================
# 📰 4. PUBLIKASI RISET BRIN (PUBLIC OVERVIEW & HAMPARAN)
# =========================================================================

_PUBLICATIONS_CACHE = {
    "timestamp": 0,
    "records": None,
    "global_stats": None
}

def invalidate_publications_cache():
    """Mengosongkan cache in-memory publikasi saat ada mutasi data dari CMS."""
    _PUBLICATIONS_CACHE["timestamp"] = 0
    _PUBLICATIONS_CACHE["records"] = None
    _PUBLICATIONS_CACHE["global_stats"] = None


def _load_publications_data(db: Session):
    """
    Mengambil data publikasi secara efisien (lightweight tuples) dengan caching in-memory 60 detik.
    Menghindari overhead ORM penuh untuk performa instan puluhan ribu baris.
    """
    now = time.time()
    if _PUBLICATIONS_CACHE["records"] is not None and (now - _PUBLICATIONS_CACHE["timestamp"] < 60):
        return _PUBLICATIONS_CACHE["records"], _PUBLICATIONS_CACHE["global_stats"]

    # Ambil field minimal yang dibutuhkan saja
    rows = db.query(
        Publication.id,
        Publication.publication_id,
        Publication.year,
        Publication.field,
        Publication.research_center,
        Publication.brin_author
    ).filter(Publication.is_active == True).order_by(
        Publication.publication_id.asc().nullslast()
    ).all()

    records = []
    author_set = set()
    center_set = set()
    valid_years = []
    all_fields_counter = {}

    for r in rows:
        pid = r[1] or str(r[0])
        y = r[2] if (r[2] and 1900 < r[2] < 2035) else None
        fields = [f.strip() for f in Publication._to_list(r[3]) if f.strip() and f.strip() != '-' and f.strip().lower() != 'null']
        centers = [c.strip() for c in Publication._to_list(r[4]) if c.strip() and c.strip() != '-' and c.strip().lower() not in ('null', 'none')]
        authors = [a.strip() for a in Publication._to_list(r[5]) if a.strip() and a.strip() != '-' and a.strip().lower() != 'null']

        for a in authors:
            author_set.add(a)
        for c in centers:
            center_set.add(c)
        if y:
            valid_years.append(y)
        for f in fields:
            all_fields_counter[f] = all_fields_counter.get(f, 0) + 1

        records.append({
            "id_publication": pid,
            "year": y,
            "fields": fields,
            "fields_lower": [f.lower() for f in fields],
            "centers": centers,
        })

    min_yr = min(valid_years) if valid_years else 2022
    max_yr = max(valid_years) if valid_years else 2025

    sorted_fields = [
        {"name": name, "count": count}
        for name, count in sorted(all_fields_counter.items(), key=lambda x: x[1], reverse=True)
    ]

    global_stats = {
        "total_publications": len(records),
        "total_researchers": len(author_set),
        "total_research_centers": len(center_set),
        "min_year": min_yr,
        "max_year": max_yr,
        "total_fields": len(sorted_fields),
        "fields": sorted_fields,
    }

    _PUBLICATIONS_CACHE["timestamp"] = now
    _PUBLICATIONS_CACHE["records"] = records
    _PUBLICATIONS_CACHE["global_stats"] = global_stats

    return records, global_stats


@router.get(
    "/publications",
    response_model=PublicPublicationOverviewResponse,
    summary="Statistik & Hamparan Publikasi Riset BRIN",
    description="Endpoint publik untuk layar meja interaktif / web publik. Mengembalikan ringkasan angka sekilas riset BRIN dan hamparan status boolean titik publikasi."
)
def get_public_publications(
    year: Optional[str] = Query(None, description="Filter tahun tertentu, misal 2024 atau ALL"),
    field: Optional[str] = Query(None, description="Filter bidang riset tertentu, misal 'Energi' atau ALL"),
    tahun: Optional[str] = Query(None, include_in_schema=False),
    bidang: Optional[str] = Query(None, include_in_schema=False),
    db: Session = Depends(get_db)
):
    # Support alias parameter Indonesia & clean Query defaults
    clean_year = year if (year is not None and not hasattr(year, "default")) else None
    clean_field = field if (field is not None and not hasattr(field, "default")) else None
    clean_tahun = tahun if (tahun is not None and not hasattr(tahun, "default")) else None
    clean_bidang = bidang if (bidang is not None and not hasattr(bidang, "default")) else None

    raw_year = clean_year or clean_tahun
    raw_field = clean_field or clean_bidang

    # Parse filter year
    filter_year = None
    if raw_year and str(raw_year).strip().upper() != 'ALL':
        try:
            filter_year = int(str(raw_year).strip())
        except ValueError:
            pass

    # Parse filter field
    filter_field = None
    filter_field_lower = None
    if raw_field and str(raw_field).strip().upper() != 'ALL':
        clean_field = str(raw_field).strip()
        if clean_field:
            filter_field = clean_field
            filter_field_lower = clean_field.lower()

    records, global_stats = _load_publications_data(db)

    # 1. Filter subset untuk bidang yang aktif jika ada
    if filter_field_lower:
        field_records = [
            r for r in records
            if filter_field_lower in r["fields_lower"]
        ]
    else:
        field_records = records

    # 2. Hitung angka patokan 'sejak'
    since_year = filter_year if filter_year is not None else global_stats["min_year"]
    count_all_years = len(field_records)
    count_since_year = sum(1 for r in field_records if r["year"] and r["year"] >= since_year)

    # 3. Hitung jejak tahunan (yearly trend)
    yearly_counts = {}
    for r in field_records:
        if r["year"]:
            yearly_counts[r["year"]] = yearly_counts.get(r["year"], 0) + 1

    sorted_years = sorted(yearly_counts.keys())
    chart_years = sorted_years[-8:] if len(sorted_years) > 8 else sorted_years
    yearly_trend = [{"year": y, "count": yearly_counts.get(y, 0)} for y in chart_years]

    # 4. Hitung Top 3 Pusat Riset
    center_counter = {}
    for r in field_records:
        for c in r["centers"]:
            center_counter[c] = center_counter.get(c, 0) + 1

    if not center_counter:
        for r in records:
            for c in r["centers"]:
                center_counter[c] = center_counter.get(c, 0) + 1

    top_satker = [
        {"name": name, "count": count}
        for name, count in sorted(center_counter.items(), key=lambda x: x[1], reverse=True)[:3]
    ]

    # 5. Bangun hamparan bitstring binary ('1' = aktif, '0' = nonaktif)
    # Super efisien: 59.625 status publikasi hanya berukuran ~59 KB (dibandingkan 3.5 MB jika array objek)
    # Sangat cepat, aman di Swagger UI (/docs) tanpa crash, dan langsung dipetakan oleh HTML5 Canvas
    is_filter_year = filter_year is not None
    is_filter_field = filter_field_lower is not None

    bits = []
    for r in records:
        if is_filter_year and r["year"] != filter_year:
            bits.append("0")
        elif is_filter_field and filter_field_lower not in r["fields_lower"]:
            bits.append("0")
        else:
            bits.append("1")
    hamparan_str = "".join(bits)

    return {
        "total_publications": global_stats["total_publications"],
        "total_researchers": global_stats["total_researchers"],
        "total_research_centers": global_stats["total_research_centers"],
        "min_year": global_stats["min_year"],
        "since_year": since_year,
        "count_since_year": count_since_year,
        "count_all_years": count_all_years,
        "yearly_trend": yearly_trend,
        "top_satker": top_satker,
        "total_fields": global_stats["total_fields"],
        "fields": global_stats["fields"],
        "filter": {
            "year": filter_year,
            "field": filter_field
        },
        "hamparan": hamparan_str
    }


# =========================================================================
# 🔄 5. DATA TERAKHIR YANG DIUPDATE (LAST CHANGE)
# =========================================================================

@router.get(
    "/last_change",
    response_model=LastChangeResponse,
    summary="Waktu & Data Terakhir yang Diupdate",
    description="Endpoint publik untuk memeriksa kapan data terakhir kali diperbarui di database beserta objek record terakhirnya."
)
def get_last_change(
    table: Optional[str] = Query(None, description="Filter entitas/tabel tertentu: 'solutions', 'publications', 'challenges', 'personas'"),
    db: Session = Depends(get_db)
):
    """
    Mengambil data yang benar-benar terakhir kali diupdate beserta timestamp updated_at.
    Hanya mengembalikan 1 objek data yang paling baru di antara entitas sistem.
    """
    candidates = []

    # 1. Tabel Solusi Riset (solutions)
    latest_sol = db.query(Solution).order_by(
        Solution.updated_at.desc().nullslast(),
        Solution.created_at.desc().nullslast()
    ).first()

    if latest_sol:
        sol_time = latest_sol.updated_at or latest_sol.created_at
        if sol_time:
            sol_data = {
                "id": str(latest_sol.id),
                "title": latest_sol.title,
                "slug": latest_sol.slug,
                "summary": latest_sol.summary,
                "aspect": latest_sol.aspect,
                "writer": latest_sol.writer,
                "year": latest_sol.year,
                "research_center": latest_sol.research_center,
                "publication_media": latest_sol.publication_media,
                "challenge_name": latest_sol.challenge_name,
                "persona_name": latest_sol.persona_name,
                "fun_fact": latest_sol.fun_fact,
                "is_active": latest_sol.is_active,
                "created_at": latest_sol.created_at,
                "updated_at": sol_time
            }
            candidates.append((sol_time, "solutions", sol_data))

    # 2. Tabel Publikasi Riset (publications)
    latest_pub = db.query(Publication).order_by(
        Publication.updated_at.desc().nullslast(),
        Publication.created_at.desc().nullslast()
    ).first()

    if latest_pub:
        pub_time = latest_pub.updated_at or latest_pub.created_at
        if pub_time:
            pub_data = {
                "id": str(latest_pub.id),
                "publication_id": latest_pub.publication_id,
                "title": latest_pub.title,
                "year": latest_pub.year,
                "source": latest_pub.source,
                "coverage": latest_pub.coverage,
                "province": latest_pub.province,
                "region": latest_pub.region,
                "created_at": latest_pub.created_at,
                "updated_at": pub_time
            }
            candidates.append((pub_time, "publications", pub_data))

    # 3. Tabel Tantangan (challenges)
    latest_challenge = db.query(Challenge).order_by(Challenge.created_at.desc().nullslast()).first()
    if latest_challenge and latest_challenge.created_at:
        ch_time = latest_challenge.created_at
        ch_data = {
            "id": str(latest_challenge.id),
            "name": latest_challenge.name,
            "slug": latest_challenge.slug,
            "color": latest_challenge.color,
            "created_at": ch_time,
            "updated_at": ch_time
        }
        candidates.append((ch_time, "challenges", ch_data))

    # 4. Tabel Peran (personas)
    latest_persona = db.query(Persona).order_by(Persona.created_at.desc().nullslast()).first()
    if latest_persona and latest_persona.created_at:
        pe_time = latest_persona.created_at
        pe_data = {
            "id": str(latest_persona.id),
            "name": latest_persona.name,
            "slug": latest_persona.slug,
            "tagline": latest_persona.tagline,
            "created_at": pe_time,
            "updated_at": pe_time
        }
        candidates.append((pe_time, "personas", pe_data))

    # Jika memfilter tabel tertentu
    if table and table.strip():
        target_table = table.strip().lower()
        matched = [c for c in candidates if c[1] == target_table]
        if matched:
            win_time, win_tbl, win_data = matched[0]
            return {
                "table": win_tbl,
                "updated_at": win_time,
                "timestamp": int(win_time.timestamp()),
                "data": win_data
            }
        else:
            raise HTTPException(status_code=404, detail=f"Data untuk tabel '{table}' tidak ditemukan atau belum ada data.")

    # Urutkan berdasarkan timestamp terbaru (descending) dan ambil yang benar-benar paling baru
    candidates.sort(key=lambda x: x[0], reverse=True)

    if candidates:
        win_time, win_tbl, win_data = candidates[0]
        return {
            "table": win_tbl,
            "updated_at": win_time,
            "timestamp": int(win_time.timestamp()),
            "data": win_data
        }

    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    return {
        "table": None,
        "updated_at": now,
        "timestamp": int(now.timestamp()),
        "data": None
    }


