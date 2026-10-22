import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings, UPLOADS_DIR
from app.db.session import engine, Base
from app.api.v1.router import api_router

# Auto create tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    docs_url="/docs",
    redoc_url="/redoc",
    swagger_ui_parameters={
        "persistAuthorization": True,
        "displayRequestDuration": True,
        "docExpansion": "list",
    }
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*", "X-Total-Count"],
)

from fastapi.responses import JSONResponse
from starlette.requests import Request

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    traceback.print_exc()
    response = JSONResponse(
        status_code=500,
        content={"detail": f"Internal Server Error: {str(exc)}"},
    )
    origin = request.headers.get("origin")
    if origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"
    return response

app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
def root():
    return {
        "app": settings.PROJECT_NAME,
        "status": "online",
        "docs": "/docs",
        "api_v1": "/api/v1"
    }


from typing import Optional
from sqlalchemy.orm import Session
from fastapi import Depends
from app.db.session import get_db
from app.schemas.publication import PublicPublicationOverviewResponse

@app.get(
    "/publications",
    response_model=PublicPublicationOverviewResponse,
    summary="Statistik & Hamparan Publikasi Riset BRIN",
    description="Endpoint publik untuk layar meja interaktif / web publik. Mengembalikan ringkasan angka sekilas riset BRIN dan hamparan status boolean titik publikasi."
)
def public_publications_root(
    year: Optional[str] = None,
    field: Optional[str] = None,
    tahun: Optional[str] = None,
    bidang: Optional[str] = None,
    db: Session = Depends(get_db)
):
    from app.api.v1.endpoints.table import get_public_publications
    return get_public_publications(year=year, field=field, tahun=tahun, bidang=bidang, db=db)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
