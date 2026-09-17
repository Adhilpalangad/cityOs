import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_extended import router as extended_router
from app.api.routes_hospitals import router as hospitals_router
from app.api.routes_incidents import router as incidents_router
from app.api.routes_infrastructure import router as infrastructure_router
from app.api.routes_live import router as live_router
from app.api.routes_live import run_consumer
from app.api.routes_projects import router as projects_router
from app.api.routes_roads import router as roads_router
from app.api.routes_system import router as system_router
from app.api.routes_vehicles import router as vehicles_router
from app.api.routes_workflows import router as workflows_router
from app.core.config import get_settings
from app.core.errors import install_exception_handlers
from app.core.logging import configure_logging
from app.middleware.request_context import RequestContextMiddleware

settings = get_settings()
configure_logging(settings.log_level)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    # Feeds app/api/routes_live.py's /ws/live broadcast from the traffic and
    # vehicles data providers -- see app/services/live_ingest.py. Skipped
    # under APP_ENV=test (see tests/conftest.py) so the unit test suite,
    # which spins up a fresh app per test and has no Redpanda to talk to,
    # doesn't pay a Kafka connect-timeout on every test.
    consumer_task = (
        asyncio.create_task(run_consumer()) if settings.app_env != "test" else None
    )
    yield
    if consumer_task is not None:
        consumer_task.cancel()


app = FastAPI(title="CityOS City Core Service", version="0.1.0", lifespan=lifespan)
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
app.include_router(roads_router)
app.include_router(hospitals_router)
app.include_router(vehicles_router)
app.include_router(incidents_router)
app.include_router(workflows_router)
app.include_router(infrastructure_router)
app.include_router(projects_router)
app.include_router(extended_router)
app.include_router(live_router)
