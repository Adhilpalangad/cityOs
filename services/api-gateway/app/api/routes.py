from fastapi import APIRouter, Response, status

from app.core.config import get_settings
from app.core.readiness import dependency_status
from app.schemas.system import HealthResponse, ReadinessResponse, SystemInfo

router = APIRouter()


@router.get("/")
async def root() -> dict[str, str]:
    return {"name": "CityOS API Gateway", "status": "online"}


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse()


@router.get("/ready", response_model=ReadinessResponse)
async def ready(response: Response) -> ReadinessResponse:
    dependencies = await dependency_status(get_settings())
    is_ready = all(value == "healthy" for value in dependencies.values())
    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return ReadinessResponse(status="ready" if is_ready else "not_ready", dependencies=dependencies)


@router.get("/api/v1/system/info", response_model=SystemInfo)
async def system_info() -> SystemInfo:
    settings = get_settings()
    return SystemInfo(version="0.1.0", environment=settings.app_env)
