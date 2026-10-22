import os
import shutil
import uuid
import io
import csv
import json
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
import math
from typing import List, Optional, Union
from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File, Form, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc, cast, Text, or_
from sqlalchemy.exc import IntegrityError
from collections import defaultdict
from datetime import datetime
from app.db.session import get_db
from app.models.user import User
from app.models.persona import Persona
from app.models.challenge import Challenge, Zone
from app.models.solution import Solution, Innovation
from app.models.relevance import SolutionPersonaRelevance, InnovationPersonaRelevance
from app.models.suggestion import ResearchSuggestion
from app.models.interaction import ModuleInteractionLog
from app.models.publication import Publication
from app.schemas.publication import (
    PublicationCreate, PublicationUpdate, PublicationResponse,
    PublicationPaginationResponse, PublicationFilterOptionsResponse
)
from app.schemas.persona import PersonaCreate, PersonaUpdate, PersonaResponse
from app.schemas.challenge import ChallengeCreate, ChallengeUpdate, ChallengeResponse, ZoneCreate, ZoneUpdate, ZoneResponse
from app.schemas.solution import (
    SolutionCreate, SolutionUpdate, SolutionResponse,
    InnovationCreate, InnovationUpdate, InnovationResponse,
    RelevanceMappingItem
)
from app.schemas.suggestion import SuggestionResponse, SuggestionAdminResponse, SuggestionStatusUpdate
from app.schemas.admin import BulkStatusUpdate, BulkDeleteRequest, DashboardAnalyticsResponse
from app.api.v1.deps import get_current_admin
from app.core.helpers import build_full_url
from app.core.config import UPLOADS_DIR

router = APIRouter()


# =========================================================================
# 📊 1. HISTORI PEMAKAIAN MODUL (BERAPA KALI DIPAKAI & STATISTIK KOMBINASI)
# =========================================================================

@router.get("/module-usage")
def get_module_usage_history(db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    """
    Mengambil histori & statistik berapa kali setiap Modul Peran (Slot 1) 
    dan Modul Tantangan (Slot 2) digunakan di meja sentuh.
    """
    personas = db.query(Persona).order_by(Persona.created_at.asc()).all()
    challenges = db.query(Challenge).order_by(Challenge.created_at.asc()).all()

    # Hitung pemakaian peran murni dari interaksi meja sentuh (GET /solutions)
    persona_stats = []
    for p in personas:
        p_interactive = db.query(func.count(ModuleInteractionLog.id)).filter(
            ModuleInteractionLog.persona_id == p.id,
            ModuleInteractionLog.event == "EXPLORE"
        ).scalar() or 0
        s_count = db.query(func.count(ResearchSuggestion.id)).join(ResearchSuggestion.personas).filter(Persona.id == p.id).scalar() or 0
        sol_count = len(p.solutions) if hasattr(p, 'solutions') and p.solutions else 0
        persona_stats.append({
            "id": p.id,
            "name": p.name,
            "slug": p.slug,
            "tagline": p.tagline,
            "icon": getattr(p, 'icon', None),
            "is_active": p.is_active,
            "usage_count": p_interactive,
            "interactive_count": p_interactive,
            "suggestion_count": s_count,
            "solution_count": sol_count,
            "solutions_count": sol_count
        })

    # Hitung pemakaian tantangan murni dari interaksi meja sentuh (GET /solutions)
    challenge_stats = []
    for c in challenges:
        c_interactive = db.query(func.count(ModuleInteractionLog.id)).filter(
            ModuleInteractionLog.challenge_id == c.id,
            ModuleInteractionLog.event == "EXPLORE"
        ).scalar() or 0
        s_count = db.query(func.count(ResearchSuggestion.id)).join(ResearchSuggestion.challenges).filter(Challenge.id == c.id).scalar() or 0
        sol_count = db.query(func.count(Solution.id)).filter(Solution.challenge_id == c.id).scalar() or 0
        challenge_stats.append({
            "id": c.id,
            "name": c.name,
            "slug": c.slug,
            "color": c.color,
            "icon": c.icon,
            "description": c.description,
            "is_active": c.is_active,
            "usage_count": c_interactive,
            "interactive_count": c_interactive,
            "suggestion_count": s_count,
            "solution_count": sol_count,
            "solutions_count": sol_count
        })

    # Kombinasi paling sering dimainkan (Peran + Tantangan) murni dari interaksi meja sentuh (GET /solutions)
    comb_interactions = (
        db.query(Persona.name, Challenge.name, func.count(ModuleInteractionLog.id))
        .join(Persona, ModuleInteractionLog.persona_id == Persona.id)
        .join(Challenge, ModuleInteractionLog.challenge_id == Challenge.id)
        .filter(ModuleInteractionLog.event == "EXPLORE")
        .group_by(Persona.name, Challenge.name)
        .order_by(func.count(ModuleInteractionLog.id).desc())
        .limit(10)
        .all()
    )
    top_combinations = [
        {"persona": row[0], "zone": row[1], "challenge": row[1], "count": row[2]}
        for row in comb_interactions
    ]

    # Log aktivitas interaksi terkini (Meja Sentuh & Usulan Riset)
    recent_interactions = (
        db.query(ModuleInteractionLog)
        .options(
            joinedload(ModuleInteractionLog.persona),
            joinedload(ModuleInteractionLog.challenge),
            joinedload(ModuleInteractionLog.solution)
        )
        .order_by(ModuleInteractionLog.created_at.desc())
        .limit(25)
        .all()
    )

    recent_suggestions = (
        db.query(ResearchSuggestion)
        .options(
            joinedload(ResearchSuggestion.personas),
            joinedload(ResearchSuggestion.challenges)
        )
        .order_by(ResearchSuggestion.created_at.desc())
        .limit(25)
        .all()
    )

    logs_list = []
    for log in recent_interactions:
        event_name = log.event or ("DETAIL" if log.solution_id else "EXPLORE")
        sol_title = log.solution_title
        if event_name == "DETAIL" and sol_title:
            desc_text = f"Melihat Detail: {sol_title}"
        elif log.persona_name and log.challenge_name:
            desc_text = f"Eksplorasi Kombinasi: {log.persona_name} + {log.challenge_name}"
        else:
            desc_text = "Eksplorasi Solusi Meja Sentuh"

        logs_list.append({
            "id": log.id,
            "event": event_name,
            "persona_id": log.persona_id,
            "persona": log.persona_name or "-",
            "zone_id": log.challenge_id,
            "zone": log.challenge_name or "-",
            "challenge_id": log.challenge_id,
            "challenge": log.challenge_name or "-",
            "solution_id": log.solution_id,
            "solution_title": sol_title,
            "innovation_title": sol_title,
            "description": desc_text,
            "keterangan": desc_text,
            "created_at": log.created_at
        })

    for s in recent_suggestions:
        logs_list.append({
            "id": s.id,
            "event": "SUGGESTION",
            "persona_id": s.persona_id,
            "persona": s.persona_name or "-",
            "zone_id": s.challenge_id,
            "zone": s.challenge_name or "-",
            "challenge_id": s.challenge_id,
            "challenge": s.challenge_name or "-",
            "solution_id": None,
            "solution_title": None,
            "description": s.title,
            "keterangan": s.deskripsi or s.title,
            "created_at": s.created_at
        })

    logs_list.sort(key=lambda x: x["created_at"] or datetime.min, reverse=True)
    recent_logs = logs_list[:25]

    total_interactive = db.query(func.count(ModuleInteractionLog.id)).filter(ModuleInteractionLog.event == "EXPLORE").scalar() or 0
    total_suggestions = db.query(func.count(ResearchSuggestion.id)).scalar() or 0

    return {
        "summary": {
            "total_persona_types": len(personas),
            "total_zone_types": len(challenges),
            "total_challenge_types": len(challenges),
            "total_interactive_plays": total_interactive,
            "total_suggestions_submitted": total_suggestions
        },
        "persona_stats": sorted(persona_stats, key=lambda x: (x["usage_count"], x["solution_count"]), reverse=True),
        "zone_stats": sorted(challenge_stats, key=lambda x: (x["usage_count"], x["solution_count"]), reverse=True),
        "challenge_stats": sorted(challenge_stats, key=lambda x: (x["usage_count"], x["solution_count"]), reverse=True),
        "top_combinations": top_combinations,
        "recent_logs": recent_logs
    }


# =========================================================================
# 👥 2. CRUD MASTER PERAN (PERSONA) & TANTANGAN (CHALLENGE / ZONE)
# =========================================================================

# --- PERSONA CRUD ---
@router.get("/personas", response_model=List[PersonaResponse])
def get_all_personas(db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    return db.query(Persona).order_by(Persona.created_at.asc()).all()


@router.post("/personas", response_model=PersonaResponse, status_code=status.HTTP_201_CREATED)
def create_persona(payload: PersonaCreate, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    existing = db.query(Persona).filter(Persona.slug == payload.slug).first()
    if existing:
        raise HTTPException(status_code=409, detail="Slug peran sudah digunakan")
    
    try:
        persona = Persona(**payload.model_dump())
        db.add(persona)
        db.commit()
        db.refresh(persona)
        return persona
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Slug peran sudah digunakan atau data konflik")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Gagal menambah peran: {str(e)}")


@router.put("/personas/{id}", response_model=PersonaResponse)
def update_persona(id: uuid.UUID, payload: PersonaUpdate, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    persona = db.query(Persona).filter(Persona.id == id).first()
    if not persona:
        raise HTTPException(status_code=404, detail="Peran tidak ditemukan")
    if payload.slug and payload.slug != persona.slug:
        existing = db.query(Persona).filter(Persona.slug == payload.slug, Persona.id != id).first()
        if existing:
            raise HTTPException(status_code=409, detail="Slug peran sudah digunakan")
    try:
        for key, val in payload.model_dump(exclude_unset=True).items():
            setattr(persona, key, val)
        db.commit()
        db.refresh(persona)
        return persona
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Slug peran sudah digunakan atau data konflik")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Gagal memperbarui peran: {str(e)}")


@router.delete("/personas/{id}")
def delete_persona(id: uuid.UUID, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    persona = db.query(Persona).filter(Persona.id == id).first()
    if not persona:
        raise HTTPException(status_code=404, detail="Peran tidak ditemukan")
    try:
        name = persona.name
        db.delete(persona)
        db.commit()
        return {"message": f"Peran '{name}' berhasil dihapus"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Gagal menghapus peran: {str(e)}")


# --- CHALLENGE / ZONE CRUD ---
@router.get("/challenges", response_model=List[ChallengeResponse])
def get_all_challenges(db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    return db.query(Challenge).order_by(Challenge.created_at.asc()).all()

# Alias route untuk /zones
@router.get("/zones", response_model=List[ChallengeResponse], include_in_schema=False)
def get_all_zones_alias(db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    return get_all_challenges(db=db, admin=admin)


@router.post("/challenges", response_model=ChallengeResponse, status_code=status.HTTP_201_CREATED)
def create_challenge(payload: ChallengeCreate, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    existing = db.query(Challenge).filter(Challenge.slug == payload.slug).first()
    if existing:
        raise HTTPException(status_code=409, detail="Slug tantangan sudah digunakan")
    
    try:
        challenge = Challenge(**payload.model_dump())
        db.add(challenge)
        db.commit()
        db.refresh(challenge)
        return challenge
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Slug tantangan sudah digunakan atau data konflik")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Gagal menambah tantangan: {str(e)}")

# Alias route untuk POST /zones
@router.post("/zones", response_model=ChallengeResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
def create_zone_alias(payload: ChallengeCreate, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    return create_challenge(payload=payload, db=db, admin=admin)


@router.put("/challenges/{id}", response_model=ChallengeResponse)
def update_challenge(id: uuid.UUID, payload: ChallengeUpdate, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    challenge = db.query(Challenge).filter(Challenge.id == id).first()
    if not challenge:
        raise HTTPException(status_code=404, detail="Tantangan tidak ditemukan")
    if payload.slug and payload.slug != challenge.slug:
        existing = db.query(Challenge).filter(Challenge.slug == payload.slug, Challenge.id != id).first()
        if existing:
            raise HTTPException(status_code=409, detail="Slug tantangan sudah digunakan")
    try:
        for key, val in payload.model_dump(exclude_unset=True).items():
            setattr(challenge, key, val)
        db.commit()
        db.refresh(challenge)
        return challenge
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Slug tantangan sudah digunakan atau data konflik")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Gagal memperbarui tantangan: {str(e)}")

# Alias route untuk PUT /zones/{id}
@router.put("/zones/{id}", response_model=ChallengeResponse, include_in_schema=False)
def update_zone_alias(id: uuid.UUID, payload: ChallengeUpdate, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    return update_challenge(id=id, payload=payload, db=db, admin=admin)


@router.delete("/challenges/{id}")
def delete_challenge(id: uuid.UUID, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    challenge = db.query(Challenge).filter(Challenge.id == id).first()
    if not challenge:
        raise HTTPException(status_code=404, detail="Tantangan tidak ditemukan")
    try:
        name = challenge.name
        db.delete(challenge)
        db.commit()
        return {"message": f"Tantangan '{name}' berhasil dihapus"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Gagal menghapus tantangan: {str(e)}")

# Alias route untuk DELETE /zones/{id}
@router.delete("/zones/{id}", include_in_schema=False)
def delete_zone_alias(id: uuid.UUID, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    return delete_challenge(id=id, db=db, admin=admin)


# =========================================================================
# 📬 3. MODERASI USULAN RISET PENGUNJUNG
# =========================================================================

@router.get("/suggestions", response_model=List[SuggestionAdminResponse])
def list_suggestions(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    query = db.query(ResearchSuggestion).options(
        joinedload(ResearchSuggestion.personas),
        joinedload(ResearchSuggestion.challenges)
    )
    if status and status.upper() != "ALL":
        query = query.filter(ResearchSuggestion.status == status.upper())
    
    rows = query.order_by(ResearchSuggestion.created_at.desc()).offset(offset).limit(limit).all()
    return [
        {
            "id": r.id,
            "title": r.title,
            "deskripsi": r.deskripsi,
            "persona_ids": [p.id for p in r.personas],
            "challange_ids": [c.id for c in r.challenges],
            "persona_name": ", ".join(p.name for p in r.personas) if r.personas else "-",
            "challenge_name": ", ".join(c.name for c in r.challenges) if r.challenges else "-",
            "zone_name": ", ".join(c.name for c in r.challenges) if r.challenges else "-",
            "topic_wanted": r.title,
            "feedback": r.deskripsi,
            "status": r.status,
            "admin_notes": r.admin_notes,
            "created_at": r.created_at,
            "updated_at": r.created_at
        }
        for r in rows
    ]


@router.patch("/suggestions/{suggestion_id}/status", response_model=SuggestionAdminResponse)
def update_suggestion_status(
    suggestion_id: uuid.UUID,
    payload: SuggestionStatusUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    suggestion = db.query(ResearchSuggestion).options(
        joinedload(ResearchSuggestion.personas),
        joinedload(ResearchSuggestion.challenges)
    ).filter(ResearchSuggestion.id == suggestion_id).first()
    
    if not suggestion:
        raise HTTPException(status_code=404, detail="Usulan tidak ditemukan")

    suggestion.status = payload.status.upper()
    if payload.admin_notes is not None:
        suggestion.admin_notes = payload.admin_notes

    db.commit()
    db.refresh(suggestion)
    return {
        "id": suggestion.id,
        "title": suggestion.title,
        "deskripsi": suggestion.deskripsi,
        "persona_ids": [p.id for p in suggestion.personas],
        "challange_ids": [c.id for c in suggestion.challenges],
        "persona_name": ", ".join(p.name for p in suggestion.personas) if suggestion.personas else "-",
        "challenge_name": ", ".join(c.name for c in suggestion.challenges) if suggestion.challenges else "-",
        "zone_name": ", ".join(c.name for c in suggestion.challenges) if suggestion.challenges else "-",
        "topic_wanted": suggestion.title,
        "feedback": suggestion.deskripsi,
        "status": suggestion.status,
        "admin_notes": suggestion.admin_notes,
        "created_at": suggestion.created_at,
        "updated_at": suggestion.created_at
    }


@router.post("/suggestions/bulk-status")
def bulk_update_suggestion_status(
    payload: BulkStatusUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    if not payload.ids:
        raise HTTPException(status_code=422, detail="Daftar ID tidak boleh kosong")

    updated_count = db.query(ResearchSuggestion).filter(ResearchSuggestion.id.in_(payload.ids)).update(
        {ResearchSuggestion.status: payload.status.upper()}, synchronize_session=False
    )
    db.commit()
    return {"message": f"{updated_count} usulan berhasil diperbarui", "updated_count": updated_count}


@router.delete("/suggestions/{suggestion_id}")
def delete_suggestion(suggestion_id: uuid.UUID, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    suggestion = db.query(ResearchSuggestion).filter(ResearchSuggestion.id == suggestion_id).first()
    if not suggestion:
        raise HTTPException(status_code=404, detail="Data tidak ditemukan")
    try:
        db.delete(suggestion)
        db.commit()
        return {"message": "Usulan berhasil dihapus"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Gagal menghapus usulan: {str(e)}")


@router.post("/suggestions/bulk-delete")
def bulk_delete_suggestions(payload: BulkDeleteRequest, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    if not payload.ids:
        raise HTTPException(status_code=422, detail="Daftar ID tidak boleh kosong")

    try:
        deleted_count = db.query(ResearchSuggestion).filter(ResearchSuggestion.id.in_(payload.ids)).delete(synchronize_session=False)
        db.commit()
        return {"message": f"{deleted_count} data usulan berhasil dihapus", "deleted_count": deleted_count}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Gagal menghapus usulan terpilih: {str(e)}")


# =========================================================================
# 💡 4. SOLUSI CRUD (SOLUTIONS / DAFTAR SOLUSI)
# =========================================================================

@router.get("/solutions", response_model=List[SolutionResponse])
def list_solutions(
    challenge_id: Optional[uuid.UUID] = None,
    zone_id: Optional[uuid.UUID] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    eff_challenge_id = challenge_id or zone_id
    query = db.query(Solution).options(
        joinedload(Solution.challenge),
        joinedload(Solution.relevant_challenges),
        joinedload(Solution.personas),
        joinedload(Solution.persona)
    )
    if eff_challenge_id:
        query = query.filter(Solution.challenge_id == eff_challenge_id)
    return query.order_by(Solution.card_no.asc().nullslast(), Solution.created_at.asc()).offset(offset).limit(limit).all()

# Alias route untuk /innovations
@router.get("/innovations", response_model=List[SolutionResponse], include_in_schema=False)
def list_innovations_alias(
    zone_id: Optional[uuid.UUID] = None,
    challenge_id: Optional[uuid.UUID] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    return list_solutions(challenge_id=challenge_id, zone_id=zone_id, limit=limit, offset=offset, db=db, admin=admin)


@router.post("/solutions", response_model=SolutionResponse, status_code=status.HTTP_201_CREATED)
def create_solution(payload: SolutionCreate, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    existing = db.query(Solution).filter(Solution.slug == payload.slug).first()
    if existing:
        raise HTTPException(status_code=409, detail="Slug solusi sudah digunakan")
    
    try:
        sol_data = payload.model_dump(exclude={"relevant_challenge_ids", "relevant_zone_ids", "persona_ids"})
        # Map challenge_id jika menggunakan zone_id
        if "zone_id" in sol_data and "challenge_id" not in sol_data:
            sol_data["challenge_id"] = sol_data.pop("zone_id")
        
        sol = Solution(**sol_data)

        # Hubungkan M2M Tantangan Relevan
        rel_ids = payload.relevant_challenge_ids or getattr(payload, 'relevant_zone_ids', None)
        if rel_ids:
            sol.relevant_challenges = db.query(Challenge).filter(Challenge.id.in_(rel_ids)).all()

        # Hubungkan M2M Kategori Peran
        if payload.persona_ids:
            sol.personas = db.query(Persona).filter(Persona.id.in_(payload.persona_ids)).all()
            if not sol.persona_id and len(sol.personas) > 0:
                sol.persona_id = sol.personas[0].id

        db.add(sol)
        db.commit()
        db.refresh(sol)
        return sol
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Slug solusi sudah digunakan atau data konflik")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Gagal menyimpan solusi: {str(e)}")

# Alias route untuk POST /innovations
@router.post("/innovations", response_model=SolutionResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
def create_innovation_alias(payload: SolutionCreate, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    return create_solution(payload=payload, db=db, admin=admin)


@router.put("/solutions/{id}", response_model=SolutionResponse)
def update_solution(id: uuid.UUID, payload: SolutionUpdate, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    sol = db.query(Solution).filter(Solution.id == id).first()
    if not sol:
        raise HTTPException(status_code=404, detail="Solusi tidak ditemukan")
    if payload.slug and payload.slug != sol.slug:
        existing = db.query(Solution).filter(Solution.slug == payload.slug, Solution.id != id).first()
        if existing:
            raise HTTPException(status_code=409, detail="Slug solusi sudah digunakan")
    try:
        update_data = payload.model_dump(exclude_unset=True, exclude={"relevant_challenge_ids", "relevant_zone_ids", "persona_ids"})
        if "zone_id" in update_data and "challenge_id" not in update_data:
            update_data["challenge_id"] = update_data.pop("zone_id")

        for key, val in update_data.items():
            setattr(sol, key, val)

        rel_ids = payload.relevant_challenge_ids or getattr(payload, 'relevant_zone_ids', None)
        if rel_ids is not None:
            sol.relevant_challenges = db.query(Challenge).filter(Challenge.id.in_(rel_ids)).all()

        if payload.persona_ids is not None:
            sol.personas = db.query(Persona).filter(Persona.id.in_(payload.persona_ids)).all()
            if sol.personas:
                sol.persona_id = sol.personas[0].id

        db.commit()
        db.refresh(sol)
        return sol
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Slug solusi sudah digunakan atau data konflik")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Gagal memperbarui solusi: {str(e)}")

# Alias route untuk PUT /innovations/{id}
@router.put("/innovations/{id}", response_model=SolutionResponse, include_in_schema=False)
def update_innovation_alias(id: uuid.UUID, payload: SolutionUpdate, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    return update_solution(id=id, payload=payload, db=db, admin=admin)


@router.delete("/solutions/{id}")
def delete_solution(id: uuid.UUID, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    sol = db.query(Solution).filter(Solution.id == id).first()
    if not sol:
        raise HTTPException(status_code=404, detail="Solusi tidak ditemukan")
    db.delete(sol)
    db.commit()
    return {"message": "Solusi berhasil dihapus"}

# Alias route untuk DELETE /innovations/{id}
@router.delete("/innovations/{id}", include_in_schema=False)
def delete_innovation_alias(id: uuid.UUID, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    return delete_solution(id=id, db=db, admin=admin)


# =========================================================================
# ⚙️ 5. RINGKASAN ANALITIK & PENGATURAN
# =========================================================================

@router.get("/analytics", response_model=DashboardAnalyticsResponse)
def get_analytics(db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    total_sol = db.query(func.count(Solution.id)).scalar() or 0
    total_personas = db.query(func.count(Persona.id)).scalar() or 0
    total_challenges = db.query(func.count(Challenge.id)).scalar() or 0
    total_sugg = db.query(func.count(ResearchSuggestion.id)).scalar() or 0
    new_sugg = db.query(func.count(ResearchSuggestion.id)).filter(ResearchSuggestion.status == "NEW").scalar() or 0
    rev_sugg = db.query(func.count(ResearchSuggestion.id)).filter(ResearchSuggestion.status == "REVIEWED").scalar() or 0
    trl_dist = {}

    tc_res = (
        db.query(Challenge.name, func.count(ResearchSuggestion.id))
        .join(Challenge.suggestions, isouter=True)
        .group_by(Challenge.id, Challenge.name)
        .order_by(func.count(ResearchSuggestion.id).desc())
        .limit(5)
        .all()
    )
    top_zones = [{"zone": r[0], "challenge": r[0], "count": r[1]} for r in tc_res]

    tp_res = (
        db.query(Persona.name, func.count(ResearchSuggestion.id))
        .join(Persona.suggestions, isouter=True)
        .group_by(Persona.id, Persona.name)
        .order_by(func.count(ResearchSuggestion.id).desc())
        .limit(5)
        .all()
    )
    top_personas = [{"persona": r[0], "count": r[1]} for r in tp_res]

    return {
        "total_innovations": total_sol,
        "total_solutions": total_sol,
        "total_personas": total_personas,
        "total_zones": total_challenges,
        "total_challenges": total_challenges,
        "total_suggestions": total_sugg,
        "new_suggestions": new_sugg,
        "reviewed_suggestions": rev_sugg,
        "top_zones": top_zones,
        "top_personas": top_personas,
        "trl_distribution": trl_dist
    }


# =========================================================================
# 📰 6. PUBLICATIONS CRUD
# =========================================================================

@router.get("/publications/filter-options", response_model=PublicationFilterOptionsResponse)
def get_publication_filter_options(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """Mengambil daftar tahun dan bidang publikasi yang tersedia untuk filter dropdown."""
    years_q = db.query(Publication.year).filter(Publication.year.isnot(None)).distinct().order_by(Publication.year.desc()).all()
    years = [y[0] for y in years_q if y[0] is not None]

    try:
        from app.api.v1.endpoints.table import _load_publications_data
        _, global_stats = _load_publications_data(db)
        fields = [f["name"] for f in global_stats.get("fields", []) if f.get("name")]
    except Exception:
        fields = []

    return {
        "years": years,
        "fields": fields
    }


@router.get("/publications", response_model=Union[PublicationPaginationResponse, List[PublicationResponse]])
def list_publications(
    response: Response,
    search: Optional[str] = Query(None, description="Search query across title, id, author, satker, etc."),
    year: Optional[int] = None,
    source: Optional[str] = None,
    coverage: Optional[str] = None,
    field: Optional[str] = None,
    research_center: Optional[str] = None,
    author: Optional[str] = None,
    page: Optional[int] = Query(None, ge=1, description="Nomor halaman (1-based)"),
    pageSize: Optional[int] = Query(None, ge=1, le=1000, description="Ukuran halaman"),
    limit: int = Query(100, ge=1, le=100000),
    offset: int = 0,
    paginated: bool = Query(False, description="Set True untuk response berformat paginasi"),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """List publications with server-side pagination, search, and filters."""
    query = db.query(Publication)

    if search and search.strip():
        s = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Publication.title.ilike(s),
                Publication.publication_id.ilike(s),
                cast(Publication.brin_author, Text).ilike(s),
                cast(Publication.research_center, Text).ilike(s),
                cast(Publication.field, Text).ilike(s),
                Publication.province.ilike(s),
                Publication.region.ilike(s),
                Publication.source.ilike(s),
                Publication.publication_media.ilike(s),
            )
        )

    if year:
        query = query.filter(Publication.year == year)
    if source:
        query = query.filter(Publication.source == source)
    if coverage:
        query = query.filter(Publication.coverage == coverage)
    if field:
        query = query.filter(cast(Publication.field, Text).ilike(f"%{field}%"))
    if research_center:
        query = query.filter(cast(Publication.research_center, Text).ilike(f"%{research_center}%"))
    if author:
        query = query.filter(cast(Publication.brin_author, Text).ilike(f"%{author}%"))

    total = query.count()
    response.headers["X-Total-Count"] = str(total)

    if page is not None:
        effective_limit = pageSize or limit
        effective_offset = (page - 1) * effective_limit
        current_page = page
    else:
        effective_limit = pageSize or limit
        effective_offset = offset
        current_page = (offset // effective_limit) + 1 if effective_limit > 0 else 1

    rows = query.order_by(Publication.year.desc().nullslast(), Publication.created_at.desc()).offset(effective_offset).limit(effective_limit).all()

    if paginated or page is not None:
        total_pages = math.ceil(total / effective_limit) if effective_limit > 0 else 1
        return {
            "items": rows,
            "total": total,
            "page": current_page,
            "pageSize": effective_limit,
            "totalPages": total_pages
        }

    return rows


@router.post("/publications", response_model=PublicationResponse, status_code=status.HTTP_201_CREATED)
def create_publication(
    payload: PublicationCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    # Check unique publication_id if provided
    if payload.publication_id:
        existing = db.query(Publication).filter(Publication.publication_id == payload.publication_id).first()
        if existing:
            raise HTTPException(status_code=409, detail="publication_id already exists")
    try:
        pub = Publication(**payload.model_dump())
        db.add(pub)
        db.commit()
        db.refresh(pub)
        try:
            from app.api.v1.endpoints.table import invalidate_publications_cache
            invalidate_publications_cache()
        except Exception:
            pass
        return pub
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="publication_id already exists or data conflict")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create publication: {str(e)}")


@router.get("/publications/template")
def download_publication_template(
    format: str = Query("xlsx", pattern="^(xlsx|csv)$"),
    admin: User = Depends(get_current_admin)
):
    """
    Menghasilkan file template import publikasi (Excel .xlsx atau CSV)
    dengan kolom: ID, Judul, Media Publikasi, Cakupan, Tahun, Sumber,
    Penulis BRIN, Pusat Riset / Satker, Bidang, Provinsi, Wilayah, Catatan data, Dihitung.
    """
    headers = [
        "ID", "Judul", "Media Publikasi", "Cakupan", "Tahun", "Sumber",
        "Penulis BRIN", "Pusat Riset / Satker", "Bidang", "Provinsi", "Wilayah", "Catatan data", "Dihitung"
    ]
    sample_rows = [
        [
            "P00001",
            "1-Dimensional analysis of land subsidence in Semarang city due to anthropogenic forces",
            "Prosiding",
            "Global",
            2021,
            "Scopus",
            "Arifan Jaya Syahbana; Dwi Sarah; Eko Soebowo",
            "Pusat Riset Teknologi Hidrodinamika; Pusat Riset Kebencanaan Geologi",
            "Bumi, Laut & Kebencanaan; Transportasi & Antariksa",
            "Jawa Tengah",
            "Jawa",
            "",
            "Ya"
        ],
        [
            "P00002",
            "1-Ethyl-3-methylimidazolium tolerance and intracellular lipid accumulation of 38 oleaginous yeast species",
            "Jurnal",
            "Global",
            2017,
            "Scopus",
            "Sarah Asih Faulina",
            "",
            "",
            "",
            "",
            "Satker tidak terpetakan",
            "Ya"
        ]
    ]

    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(headers)
        writer.writerows(sample_rows)
        output.seek(0)
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode("utf-8-sig")),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=template_import_publikasi.csv"}
        )
    else:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Template Publikasi"

        header_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
        header_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
        border_side = Side(style='thin', color="CBD5E1")
        border = Border(left=border_side, right=border_side, top=border_side, bottom=border_side)

        ws.append(headers)
        for col_idx in range(1, len(headers) + 1):
            cell = ws.cell(row=1, column=col_idx)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = border

        for row in sample_rows:
            ws.append(row)

        for row_idx in range(2, len(sample_rows) + 2):
            for col_idx in range(1, len(headers) + 1):
                cell = ws.cell(row=row_idx, column=col_idx)
                cell.font = Font(name="Segoe UI", size=10)
                cell.border = border
                if col_idx in [1, 4, 5, 6, 13]:
                    cell.alignment = Alignment(horizontal="center", vertical="center")

        widths = [12, 50, 18, 15, 10, 15, 35, 35, 30, 20, 18, 25, 12]
        for idx, width in enumerate(widths, 1):
            ws.column_dimensions[openpyxl.utils.get_column_letter(idx)].width = width

        stream = io.BytesIO()
        wb.save(stream)
        stream.seek(0)
        return StreamingResponse(
            stream,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=template_import_publikasi.xlsx"}
        )


@router.post("/publications/import")
def import_publications(
    file: UploadFile = File(...),
    mode: str = Form("create_or_update"),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """
    Mengimpor data publikasi skala besar (hingga puluhan ribu baris) dari file Excel (.xlsx / .xls) atau CSV (.csv).
    Menggunakan streaming row generator, pre-fetched lookup O(1), dan batch insert/commit (2.000 baris per batch).
    """
    if not file.filename:
        raise HTTPException(status_code=422, detail="Tidak ada file yang dipilih")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".xlsx", ".xls", ".csv"]:
        raise HTTPException(status_code=422, detail="Format file tidak didukung. Harap pilih file .xlsx, .xls, atau .csv")

    def row_generator():
        file.file.seek(0)
        if ext == ".csv":
            try:
                stream = io.TextIOWrapper(file.file, encoding="utf-8-sig", errors="replace")
                reader = csv.reader(stream)
                for r in reader:
                    if any(c is not None and str(c).strip() for c in r):
                        yield [str(c).strip() if c is not None else "" for c in r]
            except Exception:
                file.file.seek(0)
                stream = io.TextIOWrapper(file.file, encoding="latin-1", errors="replace")
                reader = csv.reader(stream)
                for r in reader:
                    if any(c is not None and str(c).strip() for c in r):
                        yield [str(c).strip() if c is not None else "" for c in r]
        else:
            wb = openpyxl.load_workbook(file.file, read_only=True, data_only=True)
            try:
                ws = wb.worksheets[0] if wb.worksheets else wb.active
                for r in ws.iter_rows(values_only=True):
                    if any(c is not None and str(c).strip() for c in r):
                        yield [str(c).strip() if c is not None else "" for c in r]
            finally:
                wb.close()

    gen = row_generator()
    header_row = next(gen, None)

    if not header_row:
        return {
            "success": False,
            "message": "File kosong atau tidak memiliki baris data setelah header.",
            "total_rows": 0,
            "imported": 0,
            "updated": 0,
            "skipped": 0,
            "errors": ["File tidak memuat baris data yang valid."]
        }

    def norm(h):
        return str(h).strip().lower().replace("_", " ").replace("-", " ")

    headers = [norm(h) for h in header_row]

    def find_col(aliases):
        # 1. Exact match priority
        for alias in aliases:
            for idx, h in enumerate(headers):
                if alias == h:
                    return idx
        # 2. Substring match for aliases > 3 chars (hindari kata pendek seperti 'id' mencocokkan 'bidang')
        for alias in aliases:
            if len(alias) <= 3:
                continue
            for idx, h in enumerate(headers):
                if alias in h:
                    return idx
        return None

    idx_id = find_col(["id publikasi", "publication id", "id_publikasi", "id", "pub id", "kode publikasi"])
    idx_title = find_col(["judul", "title", "nama publikasi", "judul publikasi"])
    idx_media = find_col(["media publikasi", "media", "publication media", "jenis media", "jenis"])
    idx_coverage = find_col(["cakupan", "coverage", "scope", "tingkat"])
    idx_year = find_col(["tahun", "year"])
    idx_source = find_col(["sumber", "source", "indeks", "index"])
    idx_author = find_col(["penulis brin", "penulis", "author", "brin author", "authors", "nama penulis"])
    idx_center = find_col(["pusat riset / satker", "pusat riset", "satker", "research center", "unit kerja", "organisasi"])
    idx_field = find_col(["bidang", "field", "area", "bidang riset", "topik riset"])
    idx_prov = find_col(["provinsi", "province"])
    idx_region = find_col(["wilayah", "region"])
    idx_notes = find_col(["catatan data", "catatan", "notes", "data notes", "keterangan"])
    idx_counted = find_col(["dihitung", "counted", "is counted", "status hitung"])

    if idx_title is None:
        raise HTTPException(status_code=422, detail="Kolom 'Judul' / 'Title' wajib ada dalam file spreadsheet.")

    # Pre-fetch existing IDs and titles into memory for O(1) lookups without 60,000 DB roundtrips
    existing_pubs = dict(
        db.query(Publication.publication_id, Publication.id)
        .filter(Publication.publication_id.isnot(None))
        .all()
    )
    existing_titles = dict(
        db.query(func.lower(Publication.title), Publication.id)
        .filter(Publication.title.isnot(None))
        .all()
    )

    imported_count = 0
    updated_count = 0
    skipped_count = 0
    total_processed = 0
    errors = []

    def parse_bool(v):
        if v is None or v == "":
            return True
        v_str = str(v).strip().lower()
        if v_str in ["ya", "true", "1", "y", "yes"]:
            return True
        if v_str in ["tidak", "false", "0", "n", "no"]:
            return False
        return True

    def parse_int(v):
        if not v:
            return None
        try:
            return int(float(str(v).strip()))
        except (ValueError, TypeError):
            return None

    def parse_list(v):
        if not v:
            return []
        if isinstance(v, list):
            return [str(x).strip() for x in v if str(x).strip()]
        s = str(v).strip()
        if not s:
            return []
        if s.startswith('[') and s.endswith(']'):
            try:
                parsed = json.loads(s)
                if isinstance(parsed, list):
                    return [str(x).strip() for x in parsed if str(x).strip()]
            except Exception:
                pass
        if ';' in s:
            return [x.strip() for x in s.split(';') if x.strip()]
        return [s]

    BATCH_SIZE = 1000
    batch_inserts = []
    batch_updates = []
    seen_in_import = set()

    def flush_batch():
        nonlocal batch_inserts, batch_updates
        if batch_inserts:
            try:
                db.bulk_insert_mappings(Publication, batch_inserts)
                db.commit()
            except Exception as e:
                db.rollback()
                for item in batch_inserts:
                    try:
                        db.bulk_insert_mappings(Publication, [item])
                        db.commit()
                    except Exception as row_err:
                        db.rollback()
                        if len(errors) < 50:
                            errors.append(f"Gagal simpan ID {item.get('publication_id', '-')}: {str(row_err)}")
            batch_inserts.clear()

        if batch_updates:
            try:
                db.bulk_update_mappings(Publication, batch_updates)
                db.commit()
            except Exception as e:
                db.rollback()
                for item in batch_updates:
                    try:
                        db.bulk_update_mappings(Publication, [item])
                        db.commit()
                    except Exception as row_err:
                        db.rollback()
                        if len(errors) < 50:
                            errors.append(f"Gagal perbarui ID {item.get('publication_id', '-')}: {str(row_err)}")
            batch_updates.clear()

    for r_idx, row in enumerate(gen, start=2):
        total_processed += 1
        try:
            def get_val(idx):
                if idx is not None and idx < len(row):
                    val = str(row[idx]).strip()
                    return val if val else None
                return None

            title = get_val(idx_title)
            if not title:
                skipped_count += 1
                continue

            pub_id = get_val(idx_id)
            media = get_val(idx_media)
            coverage = get_val(idx_coverage)
            year = parse_int(get_val(idx_year))
            source = get_val(idx_source)
            author_list = parse_list(get_val(idx_author))
            center_list = parse_list(get_val(idx_center))
            field_list = parse_list(get_val(idx_field))
            prov = get_val(idx_prov)
            region = get_val(idx_region)
            notes = get_val(idx_notes)
            counted = parse_bool(get_val(idx_counted))

            existing_uuid = None
            if pub_id and pub_id in existing_pubs:
                existing_uuid = existing_pubs[pub_id]
            elif not pub_id and title.lower() in existing_titles:
                existing_uuid = existing_titles[title.lower()]

            if existing_uuid:
                if mode == "skip_existing":
                    skipped_count += 1
                    continue
                batch_updates.append({
                    "id": existing_uuid,
                    "publication_id": pub_id,
                    "title": title,
                    "publication_media": media,
                    "coverage": coverage,
                    "year": year,
                    "source": source,
                    "brin_author": author_list,
                    "research_center": center_list,
                    "field": field_list,
                    "province": prov,
                    "region": region,
                    "data_notes": notes,
                    "is_counted": counted
                })
                updated_count += 1
            else:
                if pub_id and pub_id in seen_in_import:
                    skipped_count += 1
                    continue
                if pub_id:
                    seen_in_import.add(pub_id)

                new_uuid = uuid.uuid4()
                batch_inserts.append({
                    "id": new_uuid,
                    "publication_id": pub_id,
                    "title": title,
                    "publication_media": media,
                    "coverage": coverage,
                    "year": year,
                    "source": source,
                    "brin_author": author_list,
                    "research_center": center_list,
                    "field": field_list,
                    "province": prov,
                    "region": region,
                    "data_notes": notes,
                    "is_counted": counted,
                    "is_active": True
                })
                if pub_id:
                    existing_pubs[pub_id] = new_uuid
                else:
                    existing_titles[title.lower()] = new_uuid
                imported_count += 1

            if len(batch_inserts) >= BATCH_SIZE or len(batch_updates) >= BATCH_SIZE:
                flush_batch()

        except Exception as e:
            if len(errors) < 50:
                errors.append(f"Baris {r_idx}: {str(e)}")

    # Flush sisa batch terakhir
    flush_batch()

    try:
        from app.api.v1.endpoints.table import invalidate_publications_cache
        invalidate_publications_cache()
    except Exception:
        pass

    return {
        "success": True,
        "message": f"Import selesai: {imported_count} data baru berhasil diimpor, {updated_count} diperbarui, {skipped_count} dilewati.",
        "total_rows": total_processed,
        "imported": imported_count,
        "updated": updated_count,
        "skipped": skipped_count,
        "errors": errors
    }


@router.post("/publications/bulk-delete")
def bulk_delete_publications(
    payload: BulkDeleteRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    if not payload.ids:
        raise HTTPException(status_code=422, detail="ID list cannot be empty")
    try:
        deleted_count = db.query(Publication).filter(Publication.id.in_(payload.ids)).delete(synchronize_session=False)
        db.commit()
        try:
            from app.api.v1.endpoints.table import invalidate_publications_cache
            invalidate_publications_cache()
        except Exception:
            pass
        return {"message": f"{deleted_count} publications deleted", "deleted_count": deleted_count}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to bulk-delete publications: {str(e)}")


@router.get("/publications/{id}", response_model=PublicationResponse)
def get_publication(id: uuid.UUID, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    pub = db.query(Publication).filter(Publication.id == id).first()
    if not pub:
        raise HTTPException(status_code=404, detail="Publication not found")
    return pub


@router.put("/publications/{id}", response_model=PublicationResponse)
def update_publication(
    id: uuid.UUID,
    payload: PublicationUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    pub = db.query(Publication).filter(Publication.id == id).first()
    if not pub:
        raise HTTPException(status_code=404, detail="Publication not found")
    if payload.publication_id and payload.publication_id != pub.publication_id:
        existing = db.query(Publication).filter(
            Publication.publication_id == payload.publication_id,
            Publication.id != id
        ).first()
        if existing:
            raise HTTPException(status_code=409, detail="publication_id already in use")
    try:
        for key, val in payload.model_dump(exclude_unset=True).items():
            setattr(pub, key, val)
        db.commit()
        db.refresh(pub)
        try:
            from app.api.v1.endpoints.table import invalidate_publications_cache
            invalidate_publications_cache()
        except Exception:
            pass
        return pub
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="publication_id conflict")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update publication: {str(e)}")


@router.delete("/publications/{id}")
def delete_publication(id: uuid.UUID, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    pub = db.query(Publication).filter(Publication.id == id).first()
    if not pub:
        raise HTTPException(status_code=404, detail="Publication not found")
    try:
        db.delete(pub)
        db.commit()
        try:
            from app.api.v1.endpoints.table import invalidate_publications_cache
            invalidate_publications_cache()
        except Exception:
            pass
        return {"message": "Publication deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete publication: {str(e)}")


# =========================================================================
# 📁 7. FILE UPLOAD (ICONS, THUMBNAILS, MEDIA)
# =========================================================================

@router.post("/upload")
def upload_file(file: UploadFile = File(...), admin: User = Depends(get_current_admin)):
    """
    Endpoint untuk mengunggah file gambar (thumbnail, icon) ke server.
    Akan mengembalikan URL publik yang bisa diakses via browser atau Unity.
    """
    if not file.filename:
        raise HTTPException(status_code=422, detail="Tidak ada file yang dipilih")
    
    ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4().hex}{ext}"
    
    file_path = os.path.join(UPLOADS_DIR, unique_filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    full_url = build_full_url(f"/uploads/{unique_filename}")
    relative_url = f"/uploads/{unique_filename}"
    
    return {
        "message": "File berhasil diunggah", 
        "url": full_url,
        "relative_url": relative_url,
        "filename": unique_filename
    }
