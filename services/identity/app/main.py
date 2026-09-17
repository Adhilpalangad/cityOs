from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_auth import router as auth_router
from app.api.routes_departments import router as departments_router
from app.api.routes_permissions import router as permissions_router
from app.api.routes_roles import router as roles_router
from app.api.routes_system import router as system_router
from app.api.routes_users import router as users_router
from app.core.config import get_settings
from app.core.errors import install_exception_handlers
from app.core.logging import configure_logging
from app.middleware.request_context import RequestContextMiddleware

settings = get_settings()
configure_logging(settings.log_level)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    yield


app = FastAPI(title="CityOS Identity Service", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)
app.add_middleware(RequestContextMiddleware)
install_exception_handlers(app)

app.include_router(system_router)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(roles_router)
app.include_router(departments_router)
app.include_router(permissions_router)
