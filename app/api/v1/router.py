from fastapi import APIRouter, Depends
from app.api.v1.endpoints import auth, table, admin
from app.api.v1.deps import verify_table_access_token

api_router = APIRouter()

# 🔐 Authentication (Login, Refresh Token, Profile)
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"]
)

# 🖥️ Interactive Table / Public API (personas, challanges, solutions, solution/{id}, suggestion)
api_router.include_router(
    table.router,
    tags=["Public Table API"],
    dependencies=[Depends(verify_table_access_token)]
)

# Backward-compatibility alias with /table prefix
api_router.include_router(
    table.router,
    prefix="/table",
    include_in_schema=False,
    dependencies=[Depends(verify_table_access_token)]
)

# ⚙️ Admin CMS (Membutuhkan JWT Bearer Token)
api_router.include_router(
    admin.router,
    prefix="/admin",
    tags=["Admin CMS"]
)
