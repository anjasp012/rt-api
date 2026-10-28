from pydantic import BaseModel, Field
from typing import Optional, Any, Dict
from datetime import datetime


class LastChangeResponse(BaseModel):
    table: Optional[str] = Field(None, description="Nama tabel/entitas terakhir yang diupdate (e.g. 'solutions', 'publications')")
    updated_at: Optional[datetime] = Field(None, description="Waktu terakhir data diperbarui (ISO 8601 timestamp)")
    timestamp: Optional[int] = Field(None, description="Waktu terakhir dalam Unix epoch timestamp (detik)")
    data: Optional[Dict[str, Any]] = Field(None, description="Objek data terakhir yang diupdate")

    class Config:
        from_attributes = True
