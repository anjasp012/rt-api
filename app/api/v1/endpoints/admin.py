from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc
from app.db.session import get_db
from app.models.user import User
from app.models.persona import Persona
from app.models.zone import Zone
from app.models.research_center import ResearchCenter
from app.models.innovation import Innovation
from app.models.relevance import InnovationPersonaRelevance
from app.models.suggestion import ResearchSuggestion
from app.models.telemetry import TelemetryLog
from app.models.setting import AppSetting
from app.schemas.persona import PersonaCreate, PersonaUpdate, PersonaResponse
from app.schemas.zone import ZoneCreate, ZoneUpdate, ZoneResponse
from app.schemas.research_center import ResearchCenterCreate, ResearchCenterUpdate, ResearchCenterResponse
from app.schemas.innovation import InnovationCreate, InnovationUpdate, InnovationResponse, RelevanceMappingItem
from app.schemas.suggestion import SuggestionResponse, SuggestionStatusUpdate
from app.schemas.admin import BulkStatusUpdate, BulkDeleteRequest, SettingsUpdate, DashboardAnalyticsResponse
from app.api.v1.deps import get_current_admin

router = APIRouter()


# =========================================================================
# 📊 1. HISTORI PEMAKAIAN MODUL (BERAPA KALI DIPAKAI & STATISTIK KOMBINASI)
# =========================================================================

@router.get("/module-usage")
def get_module_usage_history(db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    """
    Mengambil histori & statistik berapa kali setiap Modul Pengguna (Slot 1) 
    dan Token Tantangan (Slot 2) digunakan di meja sentuh.
    """
    personas = db.query(Persona).order_by(Persona.order_index.asc()).all()
    zones = db.query(Zone).order_by(Zone.zone_number.asc()).all()

    # Hitung pemakaian persona dari telemetry & usulan
    persona_stats = []
    for p in personas:
        t_count = db.query(func.count(TelemetryLog.id)).filter(TelemetryLog.persona_slug == p.slug).scalar() or 0
        s_count = db.query(func.count(ResearchSuggestion.id)).filter(ResearchSuggestion.persona_id == p.id).scalar() or 0
        total_usage = t_count + s_count
        persona_stats.append({
            "id": p.id,
            "name": p.name,
            "slug": p.slug,
            "tagline": p.tagline,
            "order_index": p.order_index,
            "is_active": p.is_active,
            "usage_count": total_usage,
            "suggestion_count": s_count
        })

    # Hitung pemakaian zona dari telemetry & usulan
    zone_stats = []
    for z in zones:
        t_count = db.query(func.count(TelemetryLog.id)).filter(TelemetryLog.zone_slug == z.slug).scalar() or 0
        s_count = db.query(func.count(ResearchSuggestion.id)).filter(ResearchSuggestion.zone_id == z.id).scalar() or 0
        total_usage = t_count + s_count
        zone_stats.append({
            "id": z.id,
            "name": z.name,
            "slug": z.slug,
            "zone_number": z.zone_number,
            "description": z.description,
            "color_theme": z.color_theme,
            "is_active": z.is_active,
            "usage_count": total_usage,
            "suggestion_count": s_count
        })

    # Kombinasi paling sering dimainkan (Persona + Zona)
    comb_suggestions = (
        db.query(Persona.name, Zone.name, func.count(ResearchSuggestion.id))
        .join(Persona, ResearchSuggestion.persona_id == Persona.id)
        .join(Zone, ResearchSuggestion.zone_id == Zone.id)
        .group_by(Persona.name, Zone.name)
        .order_by(func.count(ResearchSuggestion.id).desc())
        .limit(10)
        .all()
    )
    top_combinations = [
        {"persona": row[0], "zone": row[1], "count": row[2]}
        for row in comb_suggestions
    ]

    # Log aktivitas interaksi terbaru
    recent_logs = (
        db.query(TelemetryLog)
        .order_by(TelemetryLog.created_at.desc())
        .limit(15)
        .all()
    )

    total_sessions = db.query(func.count(TelemetryLog.id)).scalar() or 0
    total_suggestions = db.query(func.count(ResearchSuggestion.id)).scalar() or 0

    return {
        "summary": {
            "total_persona_types": len(personas),
            "total_zone_types": len(zones),
            "total_interactive_plays": total_sessions + total_suggestions,
            "total_suggestions_submitted": total_suggestions
        },
        "persona_stats": sorted(persona_stats, key=lambda x: x["usage_count"], reverse=True),
        "zone_stats": sorted(zone_stats, key=lambda x: x["usage_count"], reverse=True),
        "top_combinations": top_combinations,
        "recent_logs": [
            {
                "id": log.id,
                "event": log.event_type,
                "persona": log.persona_slug or "-",
                "zone": log.zone_slug or "-",
                "created_at": log.created_at
            }
            for log in recent_logs
        ]
    }


# =========================================================================
# 👥 2. CRUD MASTER MODUL PENGGUNA (PERSONA) & TOKEN TANTANGAN (ZONA)
# =========================================================================

# --- PERSONA CRUD ---
@router.get("/personas", response_model=List[PersonaResponse])
def get_all_personas(db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    return db.query(Persona).order_by(Persona.order_index.asc()).all()


@router.post("/personas", response_model=PersonaResponse, status_code=status.HTTP_201_CREATED)
def create_persona(payload: PersonaCreate, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    existing = db.query(Persona).filter(Persona.slug == payload.slug).first()
    if existing:
        raise HTTPException(status_code=400, detail="Slug persona sudah digunakan")
    
    persona = Persona(**payload.model_dump())
    db.add(persona)
    db.commit()
    db.refresh(persona)
    return persona


@router.put("/personas/{id}", response_model=PersonaResponse)
def update_persona(id: int, payload: PersonaUpdate, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    persona = db.query(Persona).filter(Persona.id == id).first()
    if not persona:
        raise HTTPException(status_code=404, detail="Persona tidak ditemukan")
    for key, val in payload.model_dump(exclude_unset=True).items():
        setattr(persona, key, val)
    db.commit()
    db.refresh(persona)
    return persona


@router.delete("/personas/{id}")
def delete_persona(id: int, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    persona = db.query(Persona).filter(Persona.id == id).first()
    if not persona:
        raise HTTPException(status_code=404, detail="Persona tidak ditemukan")
    db.delete(persona)
    db.commit()
    return {"message": f"Persona '{persona.name}' berhasil dihapus"}


# --- ZONE CRUD ---
@router.get("/zones", response_model=List[ZoneResponse])
def get_all_zones(db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    return db.query(Zone).order_by(Zone.zone_number.asc()).all()


@router.post("/zones", response_model=ZoneResponse, status_code=status.HTTP_201_CREATED)
def create_zone(payload: ZoneCreate, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    existing = db.query(Zone).filter(Zone.slug == payload.slug).first()
    if existing:
        raise HTTPException(status_code=400, detail="Slug zona sudah digunakan")
    
    zone = Zone(**payload.model_dump())
    db.add(zone)
    db.commit()
    db.refresh(zone)
    return zone


@router.put("/zones/{id}", response_model=ZoneResponse)
def update_zone(id: int, payload: ZoneUpdate, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    zone = db.query(Zone).filter(Zone.id == id).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Zona tidak ditemukan")
    for key, val in payload.model_dump(exclude_unset=True).items():
        setattr(zone, key, val)
    db.commit()
    db.refresh(zone)
    return zone


@router.delete("/zones/{id}")
def delete_zone(id: int, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    zone = db.query(Zone).filter(Zone.id == id).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Zona tidak ditemukan")
    db.delete(zone)
    db.commit()
    return {"message": f"Zona '{zone.name}' berhasil dihapus"}


# =========================================================================
# 📬 3. MODERASI USULAN RISET PENGUNJUNG
# =========================================================================

@router.get("/suggestions", response_model=List[SuggestionResponse])
def get_all_suggestions(
    status: Optional[str] = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    query = db.query(ResearchSuggestion).options(
        joinedload(ResearchSuggestion.persona),
        joinedload(ResearchSuggestion.zone)
    )
    if status and status != 'ALL':
        query = query.filter(ResearchSuggestion.status == status.upper())
    
    rows = query.order_by(ResearchSuggestion.created_at.desc()).offset(offset).limit(limit).all()
    return [
        {
            "id": r.id,
            "visitor_name": r.visitor_name,
            "age_range": r.age_range,
            "topic_wanted": r.topic_wanted,
            "feedback": r.feedback,
            "persona_id": r.persona_id,
            "persona_name": r.persona.name if r.persona else None,
            "zone_id": r.zone_id,
            "zone_name": r.zone.name if r.zone else None,
            "screen_context": r.screen_context,
            "status": r.status,
            "admin_notes": r.admin_notes,
            "created_at": r.created_at,
            "updated_at": r.created_at
        }
        for r in rows
    ]


@router.patch("/suggestions/{suggestion_id}/status", response_model=SuggestionResponse)
def update_suggestion_status(
    suggestion_id: int,
    payload: SuggestionStatusUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    suggestion = db.query(ResearchSuggestion).options(
        joinedload(ResearchSuggestion.persona),
        joinedload(ResearchSuggestion.zone)
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


@router.post("/suggestions/bulk-status")
def bulk_update_suggestion_status(
    payload: BulkStatusUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    if not payload.ids:
        raise HTTPException(status_code=400, detail="Daftar ID tidak boleh kosong")

    updated_count = db.query(ResearchSuggestion).filter(ResearchSuggestion.id.in_(payload.ids)).update(
        {ResearchSuggestion.status: payload.status.upper()}, synchronize_session=False
    )
    db.commit()
    return {"message": f"{updated_count} usulan berhasil diperbarui", "updated_count": updated_count}


@router.delete("/suggestions/{suggestion_id}")
def delete_suggestion(suggestion_id: int, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    suggestion = db.query(ResearchSuggestion).filter(ResearchSuggestion.id == suggestion_id).first()
    if not suggestion:
        raise HTTPException(status_code=404, detail="Data tidak ditemukan")
    db.delete(suggestion)
    db.commit()
    return {"message": "Usulan berhasil dihapus"}


@router.post("/suggestions/bulk-delete")
def bulk_delete_suggestions(payload: BulkDeleteRequest, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    if not payload.ids:
        raise HTTPException(status_code=400, detail="Daftar ID tidak boleh kosong")

    deleted_count = db.query(ResearchSuggestion).filter(ResearchSuggestion.id.in_(payload.ids)).delete(synchronize_session=False)
    db.commit()
    return {"message": f"{deleted_count} data usulan berhasil dihapus", "deleted_count": deleted_count}


# =========================================================================
# 💡 4. INOVASI CRUD (PENDUKUNG KATALOG)
# =========================================================================

@router.get("/innovations", response_model=List[InnovationResponse])
def list_innovations(
    zone_id: Optional[int] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    query = db.query(Innovation).options(joinedload(Innovation.zone), joinedload(Innovation.research_center))
    if zone_id:
        query = query.filter(Innovation.zone_id == zone_id)
    return query.order_by(Innovation.order_priority.desc()).offset(offset).limit(limit).all()


@router.post("/innovations", response_model=InnovationResponse, status_code=status.HTTP_201_CREATED)
def create_innovation(payload: InnovationCreate, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    inno = Innovation(**payload.model_dump())
    db.add(inno)
    db.commit()
    db.refresh(inno)
    return inno


@router.put("/innovations/{id}", response_model=InnovationResponse)
def update_innovation(id: int, payload: InnovationUpdate, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    inno = db.query(Innovation).filter(Innovation.id == id).first()
    if not inno:
        raise HTTPException(status_code=404, detail="Inovasi tidak ditemukan")
    for key, val in payload.model_dump(exclude_unset=True).items():
        setattr(inno, key, val)
    db.commit()
    db.refresh(inno)
    return inno


@router.delete("/innovations/{id}")
def delete_innovation(id: int, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    inno = db.query(Innovation).filter(Innovation.id == id).first()
    if not inno:
        raise HTTPException(status_code=404, detail="Inovasi tidak ditemukan")
    db.delete(inno)
    db.commit()
    return {"message": "Inovasi berhasil dihapus"}


# =========================================================================
# ⚙️ 5. RINGKASAN ANALITIK & PENGATURAN
# =========================================================================

@router.get("/analytics", response_model=DashboardAnalyticsResponse)
def get_analytics(db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    total_inno = db.query(func.count(Innovation.id)).scalar() or 0
    total_personas = db.query(func.count(Persona.id)).scalar() or 0
    total_zones = db.query(func.count(Zone.id)).scalar() or 0
    total_sugg = db.query(func.count(ResearchSuggestion.id)).scalar() or 0
    new_sugg = db.query(func.count(ResearchSuggestion.id)).filter(ResearchSuggestion.status == "NEW").scalar() or 0
    rev_sugg = db.query(func.count(ResearchSuggestion.id)).filter(ResearchSuggestion.status == "REVIEWED").scalar() or 0

    trl_res = db.query(Innovation.trl, func.count(Innovation.id)).group_by(Innovation.trl).all()
    trl_dist = {f"TRL {row[0]}": row[1] for row in trl_res}

    tz_res = (
        db.query(Zone.name, func.count(ResearchSuggestion.id))
        .join(ResearchSuggestion, Zone.id == ResearchSuggestion.zone_id, isouter=True)
        .group_by(Zone.id, Zone.name)
        .order_by(func.count(ResearchSuggestion.id).desc())
        .limit(5)
        .all()
    )
    top_zones = [{"zone": r[0], "count": r[1]} for r in tz_res]

    tp_res = (
        db.query(Persona.name, func.count(ResearchSuggestion.id))
        .join(ResearchSuggestion, Persona.id == ResearchSuggestion.persona_id, isouter=True)
        .group_by(Persona.id, Persona.name)
        .order_by(func.count(ResearchSuggestion.id).desc())
        .limit(5)
        .all()
    )
    top_personas = [{"persona": r[0], "count": r[1]} for r in tp_res]

    return {
        "total_innovations": total_inno,
        "total_personas": total_personas,
        "total_zones": total_zones,
        "total_suggestions": total_sugg,
        "new_suggestions": new_sugg,
        "reviewed_suggestions": rev_sugg,
        "top_zones": top_zones,
        "top_personas": top_personas,
        "trl_distribution": trl_dist
    }


@router.get("/settings")
def get_settings(db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    setting = db.query(AppSetting).filter(AppSetting.key == "frontend_display_limit").first()
    limit_val = int(setting.value) if setting and str(setting.value).isdigit() else 50
    return {"frontend_display_limit": limit_val}


@router.post("/settings")
def update_settings(payload: SettingsUpdate, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    if payload.frontend_display_limit and payload.frontend_display_limit <= 0:
        raise HTTPException(status_code=400, detail="Batas kuota harus lebih besar dari 0")
        
    setting = db.query(AppSetting).filter(AppSetting.key == "frontend_display_limit").first()
    if not setting:
        setting = AppSetting(key="frontend_display_limit", value=str(payload.frontend_display_limit))
        db.add(setting)
    else:
        setting.value = str(payload.frontend_display_limit)
        
    db.commit()
    db.refresh(setting)
    return {"message": "Pengaturan berhasil diperbarui", "frontend_display_limit": int(setting.value)}
